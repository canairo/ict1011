import asyncio
import json
import time
import math
import uuid

from game import *

def test_game():
    game = Game(
        20, 20, 2000, 2000, 100
    )

    for i in range(10):
        game.create_random_player()

    for i in range(100):
        game.tick()
        game.print_state()


if __name__ == "__main__":
    test_game()
