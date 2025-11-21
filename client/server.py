from core import Game
import uuid
import asyncio
import json
import struct  # <--- ADD THIS
from socket import *
import time
import packets

gen_uuid = lambda: str(uuid.uuid4())
game = Game()
TIMEOUT_LIMIT = 10
INPUT_STRUCT_FMT = '<8s16sfi' # Little endian, 32 bytes total

class UDPServer(asyncio.DatagramProtocol):
    def __init__(self, game):
        self.game = game
        self.clients = {}
        self.pending_packets = []
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        print(f'[SERVER] received data {data}')
        pkt = None
        try:
            pkt = json.loads(data.decode('utf-8'))
        except (UnicodeDecodeError, json.JSONDecodeError):
            pass

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
                    print(f'[SERVER] successfully parsed pkt {pkt}')
                else:
                    print(f'[SERVER] received unknown binary data of len {len(data)} from {addr}')
                    return
            except Exception as e:
                print(f'[SERVER] failed to decode binary data: {e}')
                return

        if pkt.get("type") == "JOIN":
            print(f'[SERVER] received a JOIN packet from {addr}')
            self.game.add_player(pkt.get('uuid'))
            self.clients[pkt.get("uuid")] = {"addr": addr}
            self.clients[pkt.get("uuid")]["last_updated"] = time.time()
            return

        if pkt.get("type") == "DISCOVER":
            print(f"[SERVER] received a DISCOVER pkt from {addr}")
            resp = json.dumps({"type": "DISCOVER_RECEIVED"}).encode()
            self.transport.sendto(resp, addr)
            return

        uuid_key = pkt.get("uuid")
        if uuid_key:
            self.clients[uuid_key] = {"addr": addr}
            self.pending_packets.append(pkt)

    async def tick_loop(self):
        while True:
            await asyncio.sleep(0.016)

            for packet in self.pending_packets:
                if packet.get("uuid") in self.clients:
                    self.clients[packet.get("uuid")]["last_updated"] = time.time()
                
                match packet.get('type'):
                    case "INPUT":
                        self.game.input(packet.get('uuid'), packet.get('inp'))

            inactive_users = []
            for client in self.clients:
                last_time = self.clients[client]["last_updated"]
                time_elapsed = time.time() - last_time
                if time_elapsed > TIMEOUT_LIMIT:
                    inactive_users.append(client)

            for user in inactive_users:
                del self.clients[user]
                self.game.remove_player(user)
                print(f'[SERVER] {user} hasn\'t sent a message in {TIMEOUT_LIMIT} seconds, deleted...')

            self.pending_packets = []
            self.game.tick()
            
            state_snapshot = self.game.state()
            
            for client in self.clients:
                client_addr = self.clients[client]['addr']
                
                if client == "meowboy":
                    out_data = packets.compress_packet(state_snapshot)
                else:
                    out_data = json.dumps(state_snapshot).encode('utf-8')
                
                self.transport.sendto(out_data, client_addr)

async def main():
    from core import Game
    game = Game()

    loop = asyncio.get_running_loop()
    print('[SERVER] started server, waiting for connections...')
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
