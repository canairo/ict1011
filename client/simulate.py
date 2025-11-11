from core import Game
import uuid
import asyncio

gen_uuid = lambda: str(uuid.uuid4())
game = Game()

async def simul_init():
    for i in range(6):
        game.add_player(gen_uuid())

    for i in range(101):
        for player_uuid in game.players.keys():
            player_input = {
                "angle": 1.01 + game.players[player_uuid].angle
            }
            game.input(player_uuid, player_input)
        game.tick()
        await asyncio.sleep(1 / 20)
        yield game.state()

async def run_simulation():
    async for state in simul_init():
        print(state)

asyncio.run(run_simulation())
