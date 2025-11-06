import ctypes as c

class Packet(c.Structure):
    _fields = [
        ("type", c.c_uint8)
    ]

class Player(c.Structure):
    _fields = [
        ("uuid", c.c_uint8),
        ("angle", c.c_float),
        ("size", c.c_uint8),
        ("x_pos", c.c_float * 255),
        ("y_pos", c.c_float * 255)
    ]

class ClientPacket(c.Structure):
    _fields = [
        ("base", Packet),
        ("player", Player)
    ]

class ServerPacket(c.Structure):
    _fields = [
        ("base", Packet),
        ("count", c.c_uint8),
        ("players", Player * 255)
    ]

import math
DIST_BETWEEN_NODES = 10
def calculate_player_nodes(player):
    for i in range(player.size):
        player.x_pos[i] = player.x_pos[0] + DIST_BETWEEN_NODES * i * math.cos(player.angle)
        player.y_pos[i] = player.y_pos[0] + DIST_BETWEEN_NODES * i * math.sin(player.angle)

def move(player):
    for i in range(player.size - 1, 0, -1):
        player.x_pos[i] = player.x_pos[i-1]
        player.y_pos[i] = player.y_pos[i-1]
    player.x_pos[player.size] = 0
    player.y_pos[player.size] = 0
    player.x_pos[0] = player.x_pos[0] + DIST_BETWEEN_NODES * math.cos(player.angle)
    player.y_pos[0] = player.y_pos[0] + DIST_BETWEEN_NODES * math.sin(player.angle)

def debug_show(player):
    print(f"Player UUID: {player.uuid}")
    print(f"Angle: {player.angle}")
    print(f"Size: {player.size}")
    print("Node positions:")
    for i in range(player.size):
        x = player.x_pos[i]
        y = player.y_pos[i]
        print(f"  Node {i}: x = {x:.2f}, y = {y:.2f}")
