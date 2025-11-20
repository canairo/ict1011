from core import Game
import uuid
import asyncio
import json
from socket import *
import time
import packets

gen_uuid = lambda: str(uuid.uuid4())
game = Game()
TIMEOUT_LIMIT = 10

class UDPServer(asyncio.DatagramProtocol):
    def __init__(self, game):
        self.game = game
        self.clients = {}
        self.pending_packets = []
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        try:
            pkt = json.loads(data.decode('utf-8'))
        except Exception:
            print(f'[SERVER] failed to decode data : {data}')
            return

        if pkt.get("type") == "DISCOVER":
            print(f"[SERVER] received a DISCOVER pkt from {addr}")
            resp = json.dumps({"type": "DISCOVER_RECEIVED"}).encode()
            self.transport.sendto(resp, addr)
            return

        if pkt.get("type") == "JOIN":
            print(f'[SERVER] received a JOIN packet from {addr}')
            self.game.add_player(pkt.get('uuid'))
            self.clients[pkt.get("uuid")] = {"addr": addr}
            self.clients[pkt.get("uuid")]["last_updated"] = time.time()
            return

        self.clients[pkt.get("uuid")] = {"addr": addr}
        self.pending_packets.append(pkt)

    async def tick_loop(self):
        while True:
            await asyncio.sleep(0.016)

            for packet in self.pending_packets:
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

            # why this loop not integrated sia ^
            for user in inactive_users:
                del self.clients[user]
                self.game.remove_player(user)
                print(f'[SERVER] {user} hasn\'t sent a message in 10 seconds, deleted...')

            self.pending_packets = []
            self.game.tick()
            state_packet = json.dumps(self.game.state())
            for client in self.clients:
                print(f'{time.time()} [SERVER] sending to {client} at {self.clients[client]['addr']} {len(state_packet)}')
                if client == "meowboy":
                    state_packet = packets.compress_packet(self.game.state())
                    print(f'[SERVER] sending compressed packet w/ len {len(state_packet)}')
                else:
                    print(type(state_packet), state_packet)
                    state_packet = state_packet.encode() if type(state_packet) == str else state_packet
                self.transport.sendto(state_packet, self.clients[client]['addr'])

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
