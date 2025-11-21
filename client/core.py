"""
Core game logic for a Slither.io-like multiplayer game.

This file contains **no rendering**, **no pygame**, and **no networking**.
You (the user) will provide networking. The server can:
- Maintain a single `Game()` instance globally.
- Call `game.tick()` every simulation step.
- Call `game.input(uuid, input_dict)` whenever input arrives.
- Call `game.state()` to send the authoritative state to all clients.

You can add/remove snakes dynamically by calling `Game.add_player(uuid)` and
`Game.remove_player(uuid)`.

Coordinate system: world is WIDTH × HEIGHT with wrap-around.
"""

import math
import random
from collections import deque

# ================= CONFIG =================
WIDTH, HEIGHT = 3000, 3000
SEGMENT_SPACING = 6
BASE_SPEED = 4.0
BOOST_MULT = 2.3
BOOST_COST = 0.09
INITIAL_LENGTH = 10
GROW_PER_FOOD = 1
FOOD_COUNT = 50
# ==========================================


def wrap_pos(v, maxv):
    if v < 0:
        return v + maxv
    if v >= maxv:
        return v - maxv
    return v


def distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])

# ==========================================
# FOOD
# ==========================================

class Food:
    def __init__(self, x=None, y=None):
        self.x = x if x is not None else random.random() * WIDTH
        self.y = y if y is not None else random.random() * HEIGHT
        self.size = random.randint(3, 6)

    def as_dict(self):
        return {"x": self.x, "y": self.y, "size": self.size}

# ==========================================
# SNAKE
# ==========================================

class Snake:
    def __init__(self, uuid, x=None, y=None):
        self.uuid = uuid
        self.x = x if x is not None else random.random() * WIDTH
        self.y = y if y is not None else random.random() * HEIGHT

        self.angle = 0.0
        self.length_units = INITIAL_LENGTH * SEGMENT_SPACING
        self.target_length_units = self.length_units

        self.boosting = False
        self.speed = BASE_SPEED

        self.pending_input = {}

        self.positions = deque()
        for _ in range(int(self.length_units // SEGMENT_SPACING) + 200):
            self.positions.appendleft((self.x, self.y))

        self.dead = False

    # called by Game when Game.input(uuid) happens
    def apply_input(self, inp):
        # does not move the snake yet — stores desired control
        # expected fields: angle, boost
        if "angle" in inp:
            self.pending_input["angle"] = float(inp["angle"])
        if "boost" in inp:
            self.pending_input["boost"] = bool(inp["boost"])

    def simulate(self):
        # read stored inputs
        if "angle" in self.pending_input:
            desired = self.pending_input["angle"]
            diff = (desired - self.angle + math.pi) % (2 * math.pi) - math.pi
            self.angle += diff * 0.25

        boosting = self.pending_input.get("boost", False)

        # boost logic
        if boosting and self.length_units > SEGMENT_SPACING * 8:
            self.speed = BASE_SPEED * BOOST_MULT
            self.length_units -= BOOST_COST
            self.boosting = True
        else:
            self.speed = BASE_SPEED
            self.boosting = False

        # movement
        dx = math.cos(self.angle) * self.speed
        dy = math.sin(self.angle) * self.speed

        self.x = wrap_pos(self.x + dx, WIDTH)
        self.y = wrap_pos(self.y + dy, HEIGHT)

        # push new head
        self.positions.appendleft((self.x, self.y))

        # trim history
        max_positions = int(self.target_length_units // SEGMENT_SPACING) + 300
        while len(self.positions) > max_positions:
            self.positions.pop()

        # adjust length gradually
        if self.length_units < self.target_length_units:
            self.length_units += 0.6
        elif self.length_units > self.target_length_units:
            self.length_units -= 0.6

    def segments(self):
        seg_count = max(3, int(self.length_units // SEGMENT_SPACING))
        out = []
        for i in range(seg_count):
            idx = i * SEGMENT_SPACING
            if idx >= len(self.positions):
                break
            out.append(self.positions[idx])
        return out

    def as_dict(self):
        return {
            "uuid": self.uuid,
            "x": self.x,
            "y": self.y,
            "angle": self.angle,
            "boost": self.boosting,
            "length": self.length_units,
            "segments": list(self.segments()),
        }

# ==========================================
# GAME
# ==========================================

class Game:
    def __init__(self):
        self.players = {}  # uuid -> Snake
        self.food = [Food() for _ in range(FOOD_COUNT)]

    def add_player(self, uuid):
        if uuid not in self.players:
            self.players[uuid] = Snake(uuid)

    def remove_player(self, uuid):
        if uuid in self.players:
            del self.players[uuid]

    def input(self, uuid, inp):
        if uuid in self.players:
            self.players[uuid].apply_input(inp)

    def tick(self):
        """
        Advance game by 1 tick.
        Returns: list of UUIDs that died this tick.
        """
        dead_uuids = []

        # 1. Movement
        for s in list(self.players.values()):
            if not s.dead:
                s.simulate()

        # 2. Food Collisions
        for s in list(self.players.values()):
            if s.dead: continue
            eaten = []
            for f in self.food:
                # Collision radius for food
                if distance((s.x, s.y), (f.x, f.y)) <= (s.speed + 10): 
                    eaten.append(f)
            for f in eaten:
                self.food.remove(f)
                s.target_length_units += GROW_PER_FOOD * SEGMENT_SPACING

        # Respawn food
        while len(self.food) < FOOD_COUNT:
            self.food.append(Food())

        # 3. Snake Collisions
        all_snakes = list(self.players.values())
        for a in all_snakes:
            if a.dead: continue
            
            head = (a.x, a.y)
            
            for b in all_snakes:
                # In Slither-style games, you usually can't kill yourself,
                # so we skip if a is b.
                if a is b: 
                    continue

                # Check collision against b's body segments
                # We skip a few segments near the head to prevent cheap head-to-head kills
                # or lag-induced overlaps.
                segs = b.segments()
                
                for pos in segs:
                    # If head is close to a body segment
                    if distance(head, pos) < 8: 
                        a.dead = True
                        break
                
                if a.dead:
                    break

        # 4. Process Deaths
        for s in list(self.players.values()):
            if s.dead:
                dead_uuids.append(s.uuid)
                
                # Turn dead snake body into food
                segs = s.segments()
                # Drop food every few segments so it's not too dense
                for (x, y) in segs[::4]: 
                    self.food.append(Food(x, y))
                
                self.remove_player(s.uuid)

        return dead_uuids

    def state(self):
        return {
            "players": {uuid: s.as_dict() for uuid, s in self.players.items()},
            "food": [f.as_dict() for f in self.food],
        }
