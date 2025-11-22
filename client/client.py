import asyncio
import json
import uuid
import math
import pygame

SERVER_ADDR = ("127.0.0.1", 9999)
UUID = str(uuid.uuid4())

WIN_W, WIN_H = 1200, 800
FPS = 60

MAP_SIZE = 3000
HALF_MAP = MAP_SIZE / 2

BG_COLOR = (115, 93, 120)
PLAYER_COLOR = (247, 209, 205)
OTHER_COLOR  = (209, 179, 196)
HEAD_COLOR   = (255, 220, 220) # pale white 
FOOD_COLOR = (255, 180, 200)  # pink

BODY_RADIUS = 8
HEAD_RADIUS = 13
RENDER_SPACING = 6   # distance between circles

font = None

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


def draw_void_bg(screen, cam_x, cam_y, t):
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

def draw_red_aura(screen, sx, sy, r, t):
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
            
            draw_red_aura(screen, int(ix), int(iy), BODY_RADIUS, t)
            pygame.draw.circle(screen, color, (int(ix), int(iy)), BODY_RADIUS)
            
def draw_game(screen, state, cam_x, cam_y):
    t = pygame.time.get_ticks() * 0.001
    draw_void_bg(screen, cam_x, cam_y, t)
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

async def run_game():
    pygame.init()
    screen = pygame.display.set_mode((WIN_W, WIN_H))
    pygame.font.init()
    global font
    font = pygame.font.Font("LilitaOne-Regular.ttf", 50)
    pygame.display.set_caption("kittens.io client")
    clock = pygame.time.Clock()

    loop = asyncio.get_running_loop()
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: UDPClient(),
        remote_addr=SERVER_ADDR
    )

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
