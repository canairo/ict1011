import asyncio
import json
import uuid
import random
import math
import time
from socket import socket, AF_INET, SOCK_DGRAM

SERVER_ADDR = ("127.0.0.1", 9999)
TICK_RATE = 1/60
SEND_RATE = 1/60

gen_uuid = lambda: str(uuid.uuid4())
MY_UUID = gen_uuid()

# Movement smoothing parameters
TARGET_CHANGE_INTERVAL = 1.5   # seconds between picking a new target direction
SMOOTHING = 0.15               # how fast it blends toward the target direction

# GAME INPUT FORMAT:
#   { "type":"INPUT", "uuid":UUID, "inp": {"dx":float, "dy":float} }

class AIClient:
    def __init__(self):
        self.sock = socket(AF_INET, SOCK_DGRAM)
        self.sock.setblocking(False)

        self.uuid = MY_UUID

        # smooth movement state
        self.target_dx = 0
        self.target_dy = 0
        self.current_dx = 0
        self.current_dy = 0
        self.last_target_change = time.time()

    async def discover_server(self):
        pkt = json.dumps({"type": "DISCOVER"}).encode()
        self.sock.sendto(pkt, SERVER_ADDR)

        await asyncio.sleep(0.2)  # wait for response

    async def join(self):
        pkt = json.dumps({
            "type": "JOIN",
            "uuid": self.uuid
        }).encode()

        print(f"[CLIENT] sending JOIN as {self.uuid}")
        self.sock.sendto(pkt, SERVER_ADDR)

    def maybe_change_direction(self):
        """Pick a new random direction occasionally."""
        now = time.time()
        if now - self.last_target_change > TARGET_CHANGE_INTERVAL:
            angle = random.uniform(0, math.tau)
            self.target_dx = math.cos(angle)
            self.target_dy = math.sin(angle)
            self.last_target_change = now

    def smooth_step(self, current, target):
        return current + (target - current) * SMOOTHING

    def build_input_packet(self):
        """Smoothly adjust movement toward target."""
        self.maybe_change_direction()

        # smooth movement vector blending
        self.current_dx = self.smooth_step(self.current_dx, self.target_dx)
        self.current_dy = self.smooth_step(self.current_dy, self.target_dy)

        return {
            "type": "INPUT",
            "uuid": self.uuid,
            "inp": {
                "dx": round(self.current_dx, 3),
                "dy": round(self.current_dy, 3)
            }
        }

    async def send_loop(self):
        """Send movement updates at SEND_RATE."""
        while True:
            pkt = self.build_input_packet()
            self.sock.sendto(json.dumps(pkt).encode(), SERVER_ADDR)
            await asyncio.sleep(SEND_RATE)

    async def recv_loop(self):
        """Receive state packets."""
        loop = asyncio.get_event_loop()

        while True:
            try:
                data, addr = await loop.run_in_executor(None, self.sock.recvfrom, 65535)
            except BlockingIOError:
                await asyncio.sleep(0.001)
                continue

            # If server uses compressed packets for some clients, add handler here.
            try:
                pkt = json.loads(data.decode())
            except Exception:
                # could be compressed binary. ignore for now.
                continue

            # You can inspect state:
            # print("[CLIENT] received state, players:", pkt.get("players"))
            pass

    async def run(self):
        await self.discover_server()
        await self.join()
        await asyncio.gather(self.send_loop(), self.recv_loop())


if __name__ == "__main__":
    print("[CLIENT] AI client starting...")
    asyncio.run(AIClient().run())

