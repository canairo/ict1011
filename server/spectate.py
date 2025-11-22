import asyncio
import json
import uuid
import pygame
import time

SERVER_ADDR = ("127.0.0.1", 9999)
SPEC_UUID = str(uuid.uuid4())

# Window Settings
WIN_W, WIN_H = 1000, 1000  # Keep square for best view of square map
FPS = 60

# --- CONFIG MATCHING CORE.PY ---
MAP_W = 3000
MAP_H = 3000
# -------------------------------

# Colors
BG_COLOR = (15, 15, 20)
GRID_COLOR = (30, 30, 40)
BORDER_COLOR = (60, 60, 80)
FOOD_COLOR = (255, 100, 150)
TEXT_COLOR = (200, 200, 200)

class SpectatorClient(asyncio.DatagramProtocol):
    def __init__(self):
        self.transport = None
        self.state = None
        self.connected = False

    def connection_made(self, transport):
        self.transport = transport
        print(f"[SPECTATE] Sending handshake as {SPEC_UUID}...")
        
        pkt = {"type": "SPECTATE", "uuid": SPEC_UUID}
        self.transport.sendto(json.dumps(pkt).encode("utf-8"))
        self.connected = True

        asyncio.create_task(self.heartbeat_loop())

    def datagram_received(self, data, addr):
        try:
            self.state = json.loads(data.decode("utf-8"))
        except Exception:
            pass

    async def heartbeat_loop(self):
        while True:
            await asyncio.sleep(1.0)
            if self.transport:
                pkt = {"type": "HEARTBEAT", "uuid": SPEC_UUID}
                self.transport.sendto(json.dumps(pkt).encode("utf-8"))

# --- Visualization Helpers ---

def world_to_screen(x, y, cam_x, cam_y, zoom, sw, sh):
    """
    Convert world coordinates (0..3000) to screen coordinates.
    Centering logic: (x - cam_x) puts the camera target at 0.
    """
    sx = (x - cam_x) * zoom + sw / 2
    sy = (y - cam_y) * zoom + sh / 2
    return int(sx), int(sy)

def draw_grid(screen, cam_x, cam_y, zoom):
    """Draws grid and map borders based on 0 to 3000 coordinates"""
    w, h = screen.get_size()
    
    # 1. Draw World Border (0,0 to 3000,3000)
    tl_x, tl_y = world_to_screen(0, 0, cam_x, cam_y, zoom, w, h)
    br_x, br_y = world_to_screen(MAP_W, MAP_H, cam_x, cam_y, zoom, w, h)
    
    rect_w = br_x - tl_x
    rect_h = br_y - tl_y
    
    # Fill map area slightly lighter
    pygame.draw.rect(screen, (20, 20, 25), (tl_x, tl_y, rect_w, rect_h))
    # Draw border
    pygame.draw.rect(screen, BORDER_COLOR, (tl_x, tl_y, rect_w, rect_h), 2)

    # 2. Grid lines
    grid_spacing = 250 # World units
    
    # Vertical lines
    for wx in range(0, MAP_W + 1, grid_spacing):
        sx, _ = world_to_screen(wx, 0, cam_x, cam_y, zoom, w, h)
        if 0 <= sx <= w: # Optimization: only draw if visible
            pygame.draw.line(screen, GRID_COLOR, (sx, tl_y), (sx, br_y))

    # Horizontal lines
    for wy in range(0, MAP_H + 1, grid_spacing):
        _, sy = world_to_screen(0, wy, cam_x, cam_y, zoom, w, h)
        if 0 <= sy <= h:
            pygame.draw.line(screen, GRID_COLOR, (tl_x, sy), (br_x, sy))

def draw_game(screen, state, cam_x, cam_y, zoom):
    w, h = screen.get_size()
    
    draw_grid(screen, cam_x, cam_y, zoom)

    if not state:
        return

    # Draw Food
    for f in state.get("food", []):
        sx, sy = world_to_screen(f["x"], f["y"], cam_x, cam_y, zoom, w, h)
        r = max(1, int(f["size"] * zoom))
        pygame.draw.circle(screen, FOOD_COLOR, (sx, sy), r)

    # Draw Players
    players = state.get("players", {})
    for pid, p in players.items():
        hue = abs(hash(pid)) % 360
        color = pygame.Color(0)
        color.hsla = (hue, 60, 50, 100)
        
        # Handle Wrap-Around Rendering Artifacts
        # If a segment jumps from 2990 to 10, don't draw a line across the screen.
        if "segments" in p:
            segs = p["segments"]
            for i in range(len(segs)):
                sx, sy = world_to_screen(segs[i][0], segs[i][1], cam_x, cam_y, zoom, w, h)
                r = max(2, int(10 * zoom)) 
                pygame.draw.circle(screen, color, (sx, sy), r)

        # Head
        hx, hy = world_to_screen(p["x"], p["y"], cam_x, cam_y, zoom, w, h)
        hr = max(3, int(14 * zoom))
        pygame.draw.circle(screen, (255, 255, 255), (hx, hy), hr)

    # UI Overlay
    font = pygame.font.SysFont("Arial", 16)
    info_text = f"Spectating | Players: {len(players)} | Zoom: {zoom:.3f}"
    surface = font.render(info_text, True, TEXT_COLOR)
    screen.blit(surface, (10, 10))

async def main():
    pygame.init()
    screen = pygame.display.set_mode((WIN_W, WIN_H), pygame.RESIZABLE)
    pygame.display.set_caption("Spectator - Full Map View")
    clock = pygame.time.Clock()

    loop = asyncio.get_running_loop()
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: SpectatorClient(),
        remote_addr=SERVER_ADDR
    )

    # --- CAMERA SETUP ---
    # Fixed Center of the Map (0 to 3000 -> Center is 1500)
    cam_x = MAP_W / 2
    cam_y = MAP_H / 2
    
    try:
        running = True
        while running:
            clock.tick(FPS)
            current_w, current_h = screen.get_size()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            
            # Auto-Scale Zoom to fit the 3000x3000 map into the window
            # Added 1.05 padding so borders are visible
            scale_x = current_w / (MAP_W * 1.05)
            scale_y = current_h / (MAP_H * 1.05)
            zoom = min(scale_x, scale_y)

            screen.fill(BG_COLOR)
            draw_game(screen, protocol.state, cam_x, cam_y, zoom)
            pygame.display.flip()
            
            await asyncio.sleep(0)

    finally:
        transport.close()
        pygame.quit()

if __name__ == "__main__":
    asyncio.run(main())
