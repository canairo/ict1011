from packets import *
import random

# NONE OF THIS IS VIBE CODED
# I HATE MYSELF AND WANT TO DIE

MAX_PLAYERS = 255

class Game:
    def __init__(self, tick_rate, broadcast_rate, width, height, speed):
        self.tick_rate = tick_rate
        self.broadcast_rate = broadcast_rate
        self.width = width
        self.height = height
        self.speed = speed
        self.players = []

    def generate_uuid(self):
        used_uuids = set([int(player.uuid) for player in self.players])
        unused_uuids = [i for i in range(MAX_PLAYERS) if i not in used_uuids]
        return random.choice(unused_uuids)
    
    def create_player(self, angle, size, x_pos, y_pos):
        player = Player()
        print(type(player), dir(player))
        player.uuid = self.generate_uuid()
        player.angle = angle
        player.size = size
        player.x_pos[0] = x_pos
        player.y_pos[0] = y_pos
        calculate_player_nodes(player)
        self.players.append(player)

    def create_random_player(self):
        self.create_player(
            random.random(),
            random.randint(10, 20),
            random.randint(0, 2000),
            random.randint(0, 2000)
        )

    def tick(self):
        for player in self.players:
            move(player)

    def print_state(self):
        for player in self.players:
            debug_show(player)
