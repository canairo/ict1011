from core import Game
import uuid
import asyncio
import json
import struct
from socket import *
import time

# Attempt to import packets, fallback if not available
try:
    import packets
except ImportError:
    packets = None

TIMEOUT_LIMIT = 10
INPUT_STRUCT_FMT = '<8s16sfi' # Little endian, 32 bytes total

class UDPServer(asyncio.DatagramProtocol):
    def __init__(self, game):
        self.game = game
        self.clients = {} # Key: UUID, Value: {addr, last_updated, is_spectator}
        self.pending_packets = []
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        pkt = None
        # Try JSON first
        try:
            pkt = json.loads(data.decode('utf-8'))
        except (UnicodeDecodeError, json.JSONDecodeError):
            pass

        # If not JSON, try Struct (Binary Input)
        if pkt is None:
            try:
                if len(data) == struct.calcsize(INPUT_STRUCT_FMT):
                    raw_type, raw_uuid, angle, boost = struct.unpack(INPUT_STRUCT_FMT, data)
                    str_type = raw_type.decode('utf-8', errors='ignore').rstrip('\x00')
                    str_uuid = raw_uuid.decode('utf-8', errors='ignore').rstrip('\x00')
                    pkt = {
                        "type": str_type,
                        "uuid": str_uuid,
                        "inp": {
                            "angle": angle,
                            "boost": bool(boost)
                        }
                    }
                else:
                    return
            except Exception as e:
                print(f'[SERVER] failed to decode binary data: {e}')
                return

        msg_type = pkt.get("type")
        msg_uuid = pkt.get("uuid")
        
        if not msg_uuid:
            return

        # --- HANDLERS ---

        if msg_type == "JOIN":
            print(f'[SERVER] Player JOIN from {addr} ({msg_uuid})')
            self.game.add_player(msg_uuid)
            self.clients[msg_uuid] = {"addr": addr, "last_updated": time.time(), "is_spectator": False}
            return

        if msg_type == "SPECTATE":
            print(f'[SERVER] Spectator JOIN from {addr} ({msg_uuid})')
            # Add to clients list so they get updates, but DON'T add to Game engine
            self.clients[msg_uuid] = {"addr": addr, "last_updated": time.time(), "is_spectator": True}
            return

        if msg_type == "HEARTBEAT":
            # Keep alive for spectators or idle players
            if msg_uuid in self.clients:
                self.clients[msg_uuid]["last_updated"] = time.time()
            return

        if msg_type == "DISCOVER":
            resp = json.dumps({"type": "DISCOVER_RECEIVED"}).encode()
            self.transport.sendto(resp, addr)
            return

        # Standard Input Packet
        if msg_uuid in self.clients:
            self.clients[msg_uuid]["addr"] = addr
            self.pending_packets.append(pkt)

    async def tick_loop(self):
        while True:
            await asyncio.sleep(0.016)

            # 1. Process Inputs
            for packet in self.pending_packets:
                uid = packet.get("uuid")
                if uid in self.clients and not self.clients[uid]["is_spectator"]:
                    self.clients[uid]["last_updated"] = time.time()
                    if packet.get('type') == "INPUT":
                        self.game.input(uid, packet.get('inp'))

            # 2. Remove Inactive Users
            inactive_users = []
            for uid, client in self.clients.items():
                if time.time() - client["last_updated"] > TIMEOUT_LIMIT:
                    inactive_users.append(uid)

            for uid in inactive_users:
                is_spec = self.clients[uid]["is_spectator"]
                del self.clients[uid]
                if not is_spec:
                    self.game.remove_player(uid)
                print(f'[SERVER] Removed {"spectator" if is_spec else "player"} {uid} due to timeout.')

            self.pending_packets = []
            
            # 3. Game Tick
            self.game.tick()
            state_snapshot = self.game.state()
            
            # 4. Broadcast
            # Optimize: Encode JSON once for standard clients
            json_payload = json.dumps(state_snapshot).encode('utf-8')

            for uid, client in self.clients.items():
                # Use compressed packets for specific user if module exists
                if uid == "meowboy" and packets:
                    out_data = packets.compress_packet(state_snapshot)
                else:
                    out_data = json_payload
                
                self.transport.sendto(out_data, client['addr'])

async def main():
    game = Game()
    loop = asyncio.get_running_loop()
    print('[SERVER] started server on 0.0.0.0:9999...')
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: UDPServer(game),
        local_addr=("0.0.0.0", 9999)
    )

    try:
        await protocol.tick_loop()
    finally:
        transport.close()

if __name__ == "__main__":
    asyncio.run(main())
