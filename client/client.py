import asyncio
import json
import uuid
import math
import pygame

SERVER_ADDR = ("127.0.0.1", 9999)
UUID = str(uuid.uuid4())

# Window
WIN_W, WIN_H = 1200, 800
FPS = 60

# Colors
BG_COLOR = (20, 20, 25)
PLAYER_COLOR = (180, 30, 50)   # dark blood red
OTHER_COLOR  = (120, 0, 20)    # darker red
HEAD_COLOR   = (255, 220, 220) # pale white 
FOOD_COLOR = (255, 180, 200)  # pink

# Snake look
BODY_RADIUS = 8
HEAD_RADIUS = 13
RENDER_SPACING = 6   # distance between circles

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
        try:
            self.state = json.loads(data.decode("utf-8"))
        except Exception:
            return
        
        print(f"[CLIENT] Received state with {len(self.state.get('players', {}))} players")

    def send(self, packet: dict):
        """Helper to send JSON packets"""
        if not self.transport:
            return
        self.transport.sendto(json.dumps(packet).encode("utf-8"))

    async def send_input_loop(self):
        """Send periodic INPUT packets"""
        while True:
            pkt = {
                "type": "INPUT",
                "uuid": UUID,
                "inp": {"angle": self.angle, "boost": self.boost},
            }
            self.send(pkt)
            await asyncio.sleep(0.05)

# Aesthetics 
def draw_void_bg(screen, t):
    w, h = screen.get_size()

    base = (5, 0, 10)
    screen.fill(base)
    for i in range(0, h, 12):
        shade = 10 + int(5 * math.sin((t * 0.8) + i * 0.05))
        pygame.draw.line(screen, (shade, 0, shade), (0, i), (w, i))

    pulse = 20 + int(10 * math.sin(t * 1.2))
    pygame.draw.circle(screen, (pulse, 0, 0), (w // 2, h // 2), int(300 + 40 * math.sin(t * 0.6)), width=1)

def draw_red_aura(screen, x, y, r, t):
    pulse = 1 + 0.25 * math.sin(t * 6)
    radius = int(r * pulse) + 3
    pygame.draw.circle(screen, (150, 0, 0), (x, y), radius, width=2)

# Rendering of Obejcts
def draw_snake(screen, segments, color, cam_x, cam_y):
    if len(segments) < 2:
        return
    for i in range(len(segments) - 1):
        x1, y1 = segments[i]
        x2, y2 = segments[i + 1]

        dx = x2 - x1
        dy = y2 - y1
        dist = math.hypot(dx, dy)

        # number of mini circles between actual server segments
        steps = max(1, int(dist / RENDER_SPACING))

        for s in range(steps):
            t = s / steps
            ix = x1 + dx * t
            iy = y1 + dy * t

            rx = int(ix - cam_x)
            ry = int(iy - cam_y)

            draw_red_aura(screen, rx, ry, BODY_RADIUS, t)
            pygame.draw.circle(screen, color, (rx, ry), BODY_RADIUS)

def draw_game(screen, state, cam_x, cam_y):
    screen.fill(BG_COLOR)

    t = pygame.time.get_ticks() * 0.001
    draw_void_bg(screen, t)

    if state is None:
        return
    # Food
    for f in state["food"]:
        fx = int(f["x"] - cam_x)
        fy = int(f["y"] - cam_y)
        pygame.draw.circle(screen, FOOD_COLOR, (fx, fy), f["size"])

    # Snakes
    for uid, snake in state["players"].items():
        # Body
        body_color = PLAYER_COLOR if uid == UUID else OTHER_COLOR
        segments = snake["segments"]
        draw_snake(screen, segments, body_color, cam_x, cam_y)
        # Head
        hx = int(snake["x"] - cam_x)
        hy = int(snake["y"] - cam_y)
        draw_red_aura(screen, hx, hy, HEAD_RADIUS, t)
        pygame.draw.circle(screen, HEAD_COLOR, (hx, hy), HEAD_RADIUS)

async def run_game():
    pygame.init()
    screen = pygame.display.set_mode((WIN_W, WIN_H))
    clock = pygame.time.Clock()

    loop = asyncio.get_running_loop()
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: UDPClient(),
        remote_addr=SERVER_ADDR
    )

    cam_x = cam_y = 0

    try:
        running = True
        while running:
            dt = clock.tick(FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            
            # mouse follow
            mx, my = pygame.mouse.get_pos()
            cx, cy = WIN_W // 2, WIN_H // 2
            dx, dy = mx - cx, my - cy

            if dx != 0 or dy != 0:
                protocol.angle = math.atan2(dy, dx)

            keys = pygame.key.get_pressed()
            protocol.boost = keys[pygame.K_SPACE] or pygame.mouse.get_pressed()[0]

            # camera follow
            if protocol.state and UUID in protocol.state["players"]:
                me = protocol.state["players"][UUID]
                cam_x = me["x"] - WIN_W / 2
                cam_y = me["y"] - WIN_H / 2

            draw_game(screen, protocol.state, cam_x, cam_y)
            pygame.display.flip()

            await asyncio.sleep(0)
    finally:
        transport.close()
        pygame.quit()

if __name__ == "__main__":
    asyncio.run(run_game())