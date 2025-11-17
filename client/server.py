from core import Game
import uuid
import asyncio
import json
from socket import *

gen_uuid = lambda: str(uuid.uuid4())
game = Game()


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
            return

        self.clients[pkt.get("uuid")] = addr
        self.pending_packets.append(pkt)

    async def tick_loop(self):
        while True:
            await asyncio.sleep(0.016)

            for packet in self.pending_packets:
                print(packet)
                match packet.get('type'):
                    case "JOIN":
                        self.game.add_player(packet.get('uuid'))
                    case "INPUT":
                        self.game.input(packet.get('uuid'), packet.get('inp'))

            self.pending_packets = []
            self.game.tick()
            state_packet = json.dumps(self.game.state()).encode('utf-8')
            for addr in self.clients.values():
                self.transport.sendto(state_packet, addr)

async def main():
    from core import Game
    game = Game()

    loop = asyncio.get_running_loop()

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
