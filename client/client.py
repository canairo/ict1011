import asyncio
import json
import uuid
import math
import pygame
import time

SERVER_ADDR = ("127.0.0.1", 9999)
UUID = str(uuid.uuid4())

WIN_W, WIN_H = 1200, 800
FPS = 60

MAP_SIZE = 3000
HALF_MAP = MAP_SIZE / 2

# SNAKE RENDER VARIABLES
BODY_RADIUS = 8
HEAD_RADIUS = 13
RENDER_SPACING = 6   # distance between circles
PLAYER_NAMES = {}  # maps UUID to temp player name storage
font = None

# COLOR PALETTE
BG_COLOR = (115, 93, 120)
PLAYER_COLOR = (247, 209, 205)
OTHER_COLOR  = (209, 179, 196)
HEAD_COLOR   = (255, 220, 220) # pale white 
FOOD_COLOR = (255, 180, 200)  # pink

# SCOREBOARD
SCORE_UPDATE = 0
CACHED_SCORES = []
SCOREBOARD_UPDATE_INTERVAL = 1.0
SCORE_VISIBILITY = True

class UDPClient(asyncio.DatagramProtocol):
    def __init__(self):
        self.transport = None
        self.angle = 0.0
        self.boost = False
        self.state = None

    def connection_made(self, transport):
        self.transport = transport
        print(f"[CLIENT] Connected as UUID {UUID}")
        join_pkt = {"type": "JOIN", "uuid": UUID}
        self.send(join_pkt)

        asyncio.create_task(self.send_input_loop())

    def datagram_received(self, data, addr):
        if b"DEAD" in data:
            import sys
            sys.exit(0)
        try:
            self.state = json.loads(data.decode("utf-8"))
        except Exception:
            return
        
    def send(self, packet: dict):
        if not self.transport:
            return
        self.transport.sendto(json.dumps(packet).encode("utf-8"))

    async def send_input_loop(self):
        while True:
            pkt = {
                "type": "INPUT",
                "uuid": UUID,
                "inp": {"angle": self.angle, "boost": self.boost},
            }
            self.send(pkt)
            await asyncio.sleep(0.05)

def get_shortest_diff(target, current, size):
    diff = target - current
    if diff > size / 2:
        diff -= size
    elif diff < -size / 2:
        diff += size
    return diff

def to_screen(wx, wy, cam_x, cam_y):
    dx = wx - cam_x
    dy = wy - cam_y

    if dx > HALF_MAP: dx -= MAP_SIZE
    elif dx < -HALF_MAP: dx += MAP_SIZE
    
    if dy > HALF_MAP: dy -= MAP_SIZE
    elif dy < -HALF_MAP: dy += MAP_SIZE

    return (WIN_W // 2) + dx, (WIN_H // 2) + dy

def unwrap_segments(points, mod_x=3000):
    if not points:
        return []

    unwrapped = [list(points[0])]
    x_offset = 0
    y_offset = 0 
    
    threshold = mod_x / 2.0

    for i in range(1, len(points)):
        prev_x, prev_y = points[i-1]
        curr_x, curr_y = points[i]
        
        dx = curr_x - prev_x
        dy = curr_y - prev_y
        
        if dx < -threshold: x_offset += mod_x
        elif dx > threshold: x_offset -= mod_x

        if dy < -threshold: y_offset += mod_x
        elif dy > threshold: y_offset -= mod_x
        
        unwrapped.append([curr_x + x_offset, curr_y + y_offset])
    
    return unwrapped

"""
PLAYER NAME INPUT
"""
def get_player_name():
    pygame.init()
    # variables definition
    font = pygame.font.Font(None, 36)
    small_font = pygame.font.Font(None, 28)
    player_name = ""
    input_active = True
    clock = pygame.time.Clock()

    # temporary popup windows for player name input
    input_screen = pygame.display.set_mode((400, 200))
    pygame.display.set_caption("kittens.io <3")
    
    while input_active:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return None
                
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    input_active = False
                elif event.key == pygame.K_BACKSPACE:
                    player_name = player_name[:-1]
                elif len(player_name) < 10:  # name length limit
                    if event.unicode.isalnum() or event.unicode in "_- ":
                        player_name += event.unicode

        # draw input screeen
        input_screen.fill((30, 30, 40))
        
        instruction = small_font.render("Enter your player name =^..^=", True, (220, 220, 220))
        input_screen.blit(instruction, (20, 50))
        
        # input windows
        name_text = font.render(player_name + ("|" if pygame.time.get_ticks() % 1000 > 500 else ""), True, (255, 255, 255))
        input_screen.blit(name_text, (20, 100))
        limit_text = small_font.render(f"{len(player_name)}/10", True, (180, 180, 180))
        input_screen.blit(limit_text, (350, 105))
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    stripped_name = player_name.strip()
    return stripped_name if stripped_name else "Guest"

"""
BACKGROUND/OBJECTS RENDERING
"""
def draw_bg(screen, cam_x, cam_y, t):
    w, h = screen.get_size()
    grid_sz = 100
    off_x = -cam_x % grid_sz
    off_y = -cam_y % grid_sz
    screen.fill(BG_COLOR)
    line_col = (30, 30, 40)
    for x in range(int(off_x), w, grid_sz):
        pygame.draw.line(screen, line_col, (x, 0), (x, h))
    for y in range(int(off_y), h, grid_sz):
        pygame.draw.line(screen, line_col, (0, y), (w, y))

def draw_aura(screen, sx, sy, r, t):
    if sx < -50 or sx > WIN_W + 50 or sy < -50 or sy > WIN_H + 50:
        return
    pulse = 1 + 0.25 * math.sin(t * 6)
    radius = int(r * pulse) + 3
    pygame.draw.circle(screen, (209, 179, 196), (sx, sy), radius, width=2)

def draw_snake(screen, segments, color, cam_x, cam_y, t, show_text=False):
    if len(segments) < 2:
        return
    
    # 1. Make the snake body continuous in mathematical space
    continuous_chain = unwrap_segments(segments, MAP_SIZE)

    # 2. Determine where the HEAD is on the screen
    head_raw = segments[0]
    head_screen_x, head_screen_y = to_screen(head_raw[0], head_raw[1], cam_x, cam_y)

    # 3. Calculate the offset between the continuous chain's head and the screen head
    chain_head_x, chain_head_y = continuous_chain[0]
    offset_x = head_screen_x - chain_head_x
    offset_y = head_screen_y - chain_head_y

    # 4. Draw segments relative to the screen head
    for i in range(len(continuous_chain) - 1):
        # Get continuous coordinates
        p1 = continuous_chain[i]
        p2 = continuous_chain[i+1]
        
        # Project to screen
        s1x, s1y = p1[0] + offset_x, p1[1] + offset_y
        s2x, s2y = p2[0] + offset_x, p2[1] + offset_y

        # Interpolate circles between segments
        dx, dy = s2x - s1x, s2y - s1y
        dist = math.hypot(dx, dy)
        steps = max(1, int(dist / RENDER_SPACING))

        for s in range(steps):
            ratio = s / steps
            ix = s1x + dx * ratio
            iy = s1y + dy * ratio
            
            draw_aura(screen, int(ix), int(iy), BODY_RADIUS, t)
            pygame.draw.circle(screen, color, (int(ix), int(iy)), BODY_RADIUS)

"""
SCOREBOARD RENDERING
"""
def toggle_scoreboard():
    global SCORE_VISIBILITY
    SCORE_VISIBILITY = not SCORE_VISIBILITY

def draw_scoreboard(screen, state):
    global SCORE_UPDATE, CACHED_SCORES, PLAYER_NAMES, ui_font
    # ui frame settings
    panel_width = 220
    row_height = 30
    header_height = 36
    padding = 8
    panel_height = header_height + row_height * 5 + padding * 2
    x = WIN_W - panel_width - 10
    y = 10

    if state is None or not SCORE_VISIBILITY:
        return

    # update cached scores periodically instead of every frame
    current_time = time.time()
    if current_time - SCORE_UPDATE >= SCOREBOARD_UPDATE_INTERVAL:
        scores = []
        for uid, snake in state["players"].items():
            score = len(snake["segments"])
            scores.append((score, uid))
        scores.sort(reverse=True, key=lambda x: x[0])
        CACHED_SCORES = scores[:5]
        SCORE_UPDATE = current_time

    top_scores = CACHED_SCORES
    # margin
    panel_rect = pygame.Rect(x, y, panel_width, panel_height)
    pygame.draw.rect(screen, (40, 30, 50), panel_rect, border_radius=12)
    inner_rect = panel_rect.inflate(-2, -2)
    pygame.draw.rect(screen, (60, 45, 75), inner_rect, border_radius=10)
    
    # header
    header_rect = pygame.Rect(x, y, panel_width, header_height)
    pygame.draw.rect(screen, (80, 60, 100), header_rect)

    # title
    title_surface = ui_font.render("LEADERBOARD", True, (255, 230, 255))
    title_rect = title_surface.get_rect(midtop=(x + panel_width // 2, y + 6))
    screen.blit(title_surface, title_rect)

    # player records
    yy = y + header_height + 4
    for i in range(5):
        if i < len(top_scores):
            score, uid = top_scores[i]
            is_me = (uid == UUID)
            # rank badge
            rank = i + 1
            rank_color = (255, 215, 0) if rank == 1 else (200, 200, 200) if rank == 2 else (205, 127, 50) if rank == 3 else (200, 200, 200)
            rank_surface = ui_font.render(f"#{rank}", True, rank_color)
            screen.blit(rank_surface, (x + padding, yy + 2))
            # player name
            name_color = (255, 255, 255) if is_me else (220, 220, 255)
            display_name = PLAYER_NAMES.get(uid, uid)[:10]  # Shorten to fit
            name_surface = ui_font.render(display_name, True, name_color)
            screen.blit(name_surface, (x + padding + 40, yy + 2))
            # score
            score_surface = ui_font.render(f"{score:3d}", True, (180, 255, 180))
            score_rect = score_surface.get_rect(right=x + panel_width - padding)
            screen.blit(score_surface, (score_rect.x, yy + 2))
        else:
            pygame.draw.rect(screen, (60, 45, 75), (x + padding, yy, panel_width - 2 * padding, row_height - 2))
            
        yy += row_height
        
def draw_game(screen, state, cam_x, cam_y):
    t = pygame.time.get_ticks() * 0.001
    draw_bg(screen, cam_x, cam_y, t)
    text = font.render('kittens.io <3', False, (247, 209, 205))
    screen.blit(text, (10, 10))
    if state is None:
        return
    
    for f in state["food"]:
        fx, fy = to_screen(f["x"], f["y"], cam_x, cam_y)
        if -20 <= fx <= WIN_W + 20 and -20 <= fy <= WIN_H + 20:
            pygame.draw.circle(screen, FOOD_COLOR, (int(fx), int(fy)), f["size"])

    # Draw Snakes
    for uid, snake in state["players"].items():
        is_me = (uid == UUID)
        body_color = PLAYER_COLOR if is_me else OTHER_COLOR
        segments = snake["segments"]
        
        draw_snake(screen, segments, body_color, cam_x, cam_y, t, show_text=is_me)
        
        hx, hy = to_screen(snake["x"], snake["y"], cam_x, cam_y)
        pygame.draw.circle(screen, HEAD_COLOR, (int(hx), int(hy)), HEAD_RADIUS)

        # player name above snakes
        name_x, name_y = to_screen(snake["x"], snake["y"] - 30, cam_x, cam_y)  # 30 pixels above the head
        name_color = (255, 255, 255) if is_me else (220, 220, 220)  # White for self, gray for others
        display_name = PLAYER_NAMES.get(uid, uid)
        name_surface = ui_font.render(display_name, True, name_color)
        name_rect = name_surface.get_rect(center=(int(name_x), int(name_y)))
        screen.blit(name_surface, name_rect)
    
    # Draw scoreboard
    draw_scoreboard(screen, state)

async def run_game():
    player_name = get_player_name()
    if player_name is None:
        return
    
    pygame.init()
    screen = pygame.display.set_mode((WIN_W, WIN_H))
    pygame.font.init()

    # global font
    global font, ui_font
    font = pygame.font.Font("LilitaOne-Regular.ttf", 50)
    ui_font = pygame.font.Font("LilitaOne-Regular.ttf", 24)  

    pygame.display.set_caption("kittens.io client")
    clock = pygame.time.Clock()

    loop = asyncio.get_running_loop()
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: UDPClient(),
        remote_addr=SERVER_ADDR
    )

    # store player name 
    global PLAYER_NAMES
    PLAYER_NAMES[UUID] = player_name 

    # Camera state
    cam_x, cam_y = 1500, 1500 # Start middle
    initialized_cam = False

    try:
        running = True
        while running:
            dt = clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                # tab close open scoreboard
                elif event.type == pygame.KEYDOWN: 
                    if event.key == pygame.K_TAB:
                        toggle_scoreboard()
            
            # Input handling
            mx, my = pygame.mouse.get_pos()
            cx, cy = WIN_W // 2, WIN_H // 2
            dx, dy = mx - cx, my - cy
            if dx != 0 or dy != 0:
                protocol.angle = math.atan2(dy, dx)

            keys = pygame.key.get_pressed()
            protocol.boost = keys[pygame.K_SPACE] or pygame.mouse.get_pressed()[0]

            # Camera Logic
            if protocol.state and UUID in protocol.state["players"]:
                me = protocol.state["players"][UUID]
                target_x, target_y = me['x'], me['y']

                if not initialized_cam:
                    cam_x, cam_y = target_x, target_y
                    initialized_cam = True
                else:
                    diff_x = get_shortest_diff(target_x, cam_x, MAP_SIZE)
                    diff_y = get_shortest_diff(target_y, cam_y, MAP_SIZE) # Assuming map is square

                    cam_x += diff_x * 0.1
                    cam_y += diff_y * 0.1

                    cam_x %= MAP_SIZE
                    cam_y %= MAP_SIZE

            draw_game(screen, protocol.state, cam_x, cam_y)
            
            pygame.display.flip()
            await asyncio.sleep(0)

    finally:
        transport.close()
        pygame.quit()

if __name__ == "__main__":
    asyncio.run(run_game())