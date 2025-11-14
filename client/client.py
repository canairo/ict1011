
import asyncio
import json
import uuid
import math
import random

SERVER_ADDR = ("127.0.0.1", 9999)
UUID = str(uuid.uuid4())

class UDPClient(asyncio.DatagramProtocol):
    def __init__(self):
        self.transport = None
        self.angle = 0.0

    def connection_made(self, transport):
        self.transport = transport
        print(f"[CLIENT] Connected as UUID {UUID}")

        join_packet = {
            "type": "JOIN",
            "uuid": UUID
        }
        self.send(join_packet)
        asyncio.create_task(self.send_input_loop())

    def datagram_received(self, data, addr):
        try:
            msg = json.loads(data.decode("utf-8"))
        except Exception:
            return

        print(f"[CLIENT] Received state with {len(msg.get('players', {}))} players")


    def send(self, packet: dict):
        if not self.transport:
            return
        data = json.dumps(packet).encode("utf-8")
        self.transport.sendto(data)

    async def send_input_loop(self):
        while True:
            self.angle += 0.3
            inp_packet = {
                "type": "INPUT",
                "uuid": UUID,
                "inp": {
                    "angle": self.angle,
                    "boost": random.random() < 0.1
                }
            }
            self.send(inp_packet)
            await asyncio.sleep(0.05)  # 20Hz input rate

async def main():
    loop = asyncio.get_running_loop()
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: UDPClient(),
        remote_addr=SERVER_ADDR
    )

    try:
        await asyncio.Future()  # run forever
    finally:
        transport.close()

if __name__ == "__main__":
    asyncio.run(main())
