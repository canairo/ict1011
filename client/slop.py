
"""
Simple Slither.io-style game using pygame
- Single-player: control your snake with mouse (or arrow keys)
- Eat food to grow
- AI snakes wander and eat food
- Speed boost with SPACE (consumes length)
- Wrap-around arena

Run: pip install pygame
      python slitherio_pygame.py

This is a single-file implementation intended for learning/extension.
"""

import math
import random
import sys
from collections import deque

import pygame

# ---------- CONFIG ----------
WIDTH, HEIGHT = 1200, 800
FPS = 60

PLAYER_COLOR = (50, 220, 100)
AI_COLOR = (220, 100, 100)
FOOD_COLOR = (230, 230, 80)
BG_COLOR = (24, 24, 30)

INITIAL_LENGTH = 40  # number of segments
SEGMENT_SPACING = 6  # pixels between stored positions
SEGMENT_RADIUS_BASE = 8
FOOD_COUNT = 200
AI_COUNT = 6

MAX_SPEED = 4.5
BOOST_MULT = 2.25
BOOST_COST = 0.12  # how much length is consumed per frame when boosting
GROW_PER_FOOD = 12  # how many "length units" are added when eating

# ---------- UTIL ----------

def clamp(x, a, b):
    return max(a, min(b, x))


def wrap_pos(x, maxv):
    if x < 0:
        return x + maxv
    if x >= maxv:
        return x - maxv
    return x


def distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])

# ---------- Game Objects ----------

class Food:
    def __init__(self):
        self.pos = [random.random() * WIDTH, random.random() * HEIGHT]
        self.radius = random.randint(3, 6)

    def draw(self, surf):
        pygame.draw.circle(surf, FOOD_COLOR, (int(self.pos[0]), int(self.pos[1])), self.radius)


class Snake:
    def __init__(self, color, start_pos=None, initial_length=INITIAL_LENGTH):
        self.color = color
        self.head = list(start_pos if start_pos else (random.random() * WIDTH, random.random() * HEIGHT))
        self.angle = 0.0
        self.speed = 2.4
        # positions history used to place segments
        self.positions = deque()
        # length units is continuous; each growth increases it; segments drawn at spacing
        self.length_units = initial_length * SEGMENT_SPACING
        self.target_length_units = self.length_units
        # create initial positions behind the head
        for i in range(int(self.length_units // SEGMENT_SPACING) + 200):
            self.positions.appendleft((self.head[0], self.head[1]))
        self.dead = False

    def update_head(self, dx, dy):
        self.head[0] += dx
        self.head[1] += dy
        # wrap
        self.head[0] = wrap_pos(self.head[0], WIDTH)
        self.head[1] = wrap_pos(self.head[1], HEIGHT)
        # store head in positions history
        self.positions.appendleft((self.head[0], self.head[1]))
        # trim history when it's longer than needed
        max_positions = int(self.target_length_units // SEGMENT_SPACING) + 300
        while len(self.positions) > max_positions:
            self.positions.pop()
        # approach target length gradually
        if self.length_units < self.target_length_units:
            self.length_units += 0.8
        elif self.length_units > self.target_length_units:
            self.length_units -= 0.8

    def draw(self, surf):
        # draw segments along history
        seg_count = max(3, int(self.length_units // SEGMENT_SPACING))
        radius = SEGMENT_RADIUS_BASE
        # head glow
        head_pos = (int(self.head[0]), int(self.head[1]))
        pygame.draw.circle(surf, (255, 255, 255), head_pos, int(radius * 1.6))
        for i in range(seg_count):
            idx = i * SEGMENT_SPACING
            if idx >= len(self.positions):
                break
            pos = self.positions[idx]
            r = int(radius * (1 - (i / (seg_count + 5))) )
            r = max(2, r)
            pygame.draw.circle(surf, self.color, (int(pos[0]), int(pos[1])), r)

    def get_segments_positions(self):
        seg_count = max(3, int(self.length_units // SEGMENT_SPACING))
        res = []
        for i in range(seg_count):
            idx = i * SEGMENT_SPACING
            if idx >= len(self.positions):
                break
            res.append(self.positions[idx])
        return res

    def head_collides_with(self, point, radius):
        return distance(self.head, point) <= radius

    def segment_collides_with(self, point, radius):
        for pos in self.get_segments_positions():
            if distance(pos, point) <= radius:
                return True
        return False


class Player(Snake):
    def __init__(self, color, start_pos=None):
        super().__init__(color, start_pos, initial_length=INITIAL_LENGTH)
        self.boosting = False
        self.score = 0

    def control_update(self, target_pos, dt, boosting):
        # compute desired angle toward target_pos
        vecx = target_pos[0] - self.head[0]
        vecy = target_pos[1] - self.head[1]
        ang = math.atan2(vecy, vecx)
        # small smoothing on angle
        diff = (ang - self.angle + math.pi) % (2 * math.pi) - math.pi
        self.angle += diff * 0.15
        base_speed = MAX_SPEED
        if boosting and (self.length_units > SEGMENT_SPACING * 8):
            self.boosting = True
            self.length_units -= BOOST_COST * dt * FPS
            speed = base_speed * BOOST_MULT
        else:
            self.boosting = False
            speed = base_speed
        dx = math.cos(self.angle) * speed
        dy = math.sin(self.angle) * speed
        self.update_head(dx, dy)


class AISnake(Snake):
    def __init__(self, color):
        super().__init__(color, initial_length=random.randint(30, 70))
        self.wander_target = [random.random() * WIDTH, random.random() * HEIGHT]
        self.change_timer = random.randint(40, 140)
        self.eat_seek = None

    def update_ai(self, foods):
        # simple behavior: wander, sometimes chase nearest food within a certain range
        self.change_timer -= 1
        if self.change_timer <= 0:
            self.change_timer = random.randint(40, 140)
            self.wander_target = [random.random() * WIDTH, random.random() * HEIGHT]

        # find closest food
        nearest = None
        nearest_d = 1e9
        for f in foods:
            d = distance(self.head, f.pos)
            if d < nearest_d:
                nearest_d = d
                nearest = f
        # if food is close enough, chase it
        if nearest and nearest_d < 220:
            tx, ty = nearest.pos
        else:
            tx, ty = self.wander_target
        # move toward tx,ty
        ang = math.atan2(ty - self.head[1], tx - self.head[0])
        # minor random wiggle
        ang += (random.random() - 0.5) * 0.2
        self.angle += ((ang - self.angle + math.pi) % (2 * math.pi) - math.pi) * 0.08
        speed = self.speed
        dx = math.cos(self.angle) * speed
        dy = math.sin(self.angle) * speed
        self.update_head(dx, dy)

# ---------- Collision helpers ----------


def check_food_collision(snake, foods):
    eaten = []
    for f in foods:
        # check against head
        if snake.head_collides_with(f.pos, f.radius + SEGMENT_RADIUS_BASE * 0.8):
            eaten.append(f)
    return eaten


def check_snake_vs_snake_collision(snake_a, snake_b):
    # head of a with segments of b (excluding b's head segment to avoid head-on small overlap)
    head = snake_a.head
    segs = snake_b.get_segments_positions()[3:]
    for pos in segs:
        if distance(head, pos) < SEGMENT_RADIUS_BASE * 0.9:
            return True
    return False

# ---------- Main ----------

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Slither-like (Pygame)")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 28)
    bigfont = pygame.font.SysFont(None, 56)

    # create food
    foods = [Food() for _ in range(FOOD_COUNT)]

    # create snakes
    player = Player(PLAYER_COLOR, start_pos=(WIDTH / 2, HEIGHT / 2))
    ais = [AISnake(AI_COLOR) for _ in range(AI_COUNT)]

    running = True
    mouse_pos = (WIDTH / 2, HEIGHT / 2)
    paused = False

    while running:
        dt = clock.tick(FPS) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEMOTION:
                mouse_pos = event.pos
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_p:
                    paused = not paused
                if event.key == pygame.K_r and player.dead:
                    # restart
                    main()
                    return

        keys = pygame.key.get_pressed()
        boosting = keys[pygame.K_SPACE]

        if not paused and not player.dead:
            # update player
            # fallback controls with arrows if mouse outside window
            target = mouse_pos
            if any([keys[pygame.K_UP], keys[pygame.K_DOWN], keys[pygame.K_LEFT], keys[pygame.K_RIGHT]]):
                tx = player.head[0]
                ty = player.head[1]
                if keys[pygame.K_UP]:
                    ty -= 200
                if keys[pygame.K_DOWN]:
                    ty += 200
                if keys[pygame.K_LEFT]:
                    tx -= 200
                if keys[pygame.K_RIGHT]:
                    tx += 200
                target = (tx, ty)

            player.control_update(target, dt, boosting)

            # update AI
            for ai in ais:
                ai.update_ai(foods)

            # food collisions
            eaten_by_player = check_food_collision(player, foods)
            for f in eaten_by_player:
                player.target_length_units += GROW_PER_FOOD * SEGMENT_SPACING
                player.score += 1
                try:
                    foods.remove(f)
                except ValueError:
                    pass

            for ai in ais:
                eaten = check_food_collision(ai, foods)
                for f in eaten:
                    ai.target_length_units += GROW_PER_FOOD * SEGMENT_SPACING
                    try:
                        foods.remove(f)
                    except ValueError:
                        pass

            # snake collisions
            # player head vs ais
            for ai in ais:
                if check_snake_vs_snake_collision(player, ai):
                    player.dead = True
                    break
            # ai head vs player body
            for ai in ais:
                if check_snake_vs_snake_collision(ai, player):
                    # kill ai: convert its segments into food
                    ai.dead = True

            # remove dead ais and spawn food from their bodies
            new_food = []
            for ai in [a for a in ais if a.dead]:
                segs = ai.get_segments_positions()
                for s in segs[::8]:
                    nf = Food()
                    nf.pos = [s[0] + random.uniform(-8, 8), s[1] + random.uniform(-8, 8)]
                    nf.radius = random.randint(2, 6)
                    new_food.append(nf)
                try:
                    ais.remove(ai)
                except ValueError:
                    pass
            foods.extend(new_food)

            # occasionally spawn new AI if count low
            if len(ais) < AI_COUNT and random.random() < 0.01:
                ais.append(AISnake(AI_COLOR))

            # maintain food count
            while len(foods) < FOOD_COUNT:
                foods.append(Food())

        # draw
        screen.fill(BG_COLOR)

        # draw foods
        for f in foods:
            f.draw(screen)

        # draw ais then player
        for ai in ais:
            ai.draw(screen)
        player.draw(screen)

        # HUD
        hud = font.render(f"Score: {player.score}  Length: {int(player.length_units)}  Boosting: {player.boosting}", True, (240, 240, 240))
        screen.blit(hud, (10, 10))

        if player.dead:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            screen.blit(overlay, (0, 0))
            txt = bigfont.render("You died", True, (255, 200, 200))
            sub = font.render("Press R to restart", True, (240, 240, 240))
            screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, HEIGHT // 2 - 80))
            screen.blit(sub, (WIDTH // 2 - sub.get_width() // 2, HEIGHT // 2))

        if paused:
            ptxt = bigfont.render("Paused", True, (255, 255, 255))
            screen.blit(ptxt, (WIDTH // 2 - ptxt.get_width() // 2, 30))

        pygame.display.flip()

    pygame.quit()


if __name__ == '__main__':
    main()
