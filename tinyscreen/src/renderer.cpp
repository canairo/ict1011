#include "button_handler.h"
#include "game_handler.h"
#include <Wire.h>
#include <SPI.h>
#include <TinyScreen.h>
#include <WiFi101.h>
#include <string.h>
#include <math.h>

#define SCREEN_W 96
#define SCREEN_H 64
#define CENTER_X 48
#define CENTER_Y 32

// --- CONFIGURATION ---
// 0.15 means 100 world units = 15 screen pixels.
// Adjust this to zoom in/out. 
#define ZOOM_FACTOR 0.15 

// 8-Bit Color Definitions (RRRGGGBB)
#define C_BG      0x10 // Dark Grey/Blue
#define C_ME      0xE0 // Red
#define C_ME_HEAD 0xFF // Whiteish
#define C_ENEMY   0x60 // Dark Red
#define C_FOOD    0xF4 // Pinkish

// Helper to draw a dot. 
// Since we are zoomed out, detailed circles don't matter as much as speed.
void draw_scaled_dot(TinyScreen *display, int x, int y, int size, uint8_t color) {
    // Culling: Don't draw if completely off screen
    if (x < -size || x > SCREEN_W + size || y < -size || y > SCREEN_H + size) return;

    if (size <= 1) {
        display->drawPixel(x, y, color);
    } else if (size == 2) {
        display->drawRect(x, y, 2, 2, 1, color); // 2x2 Square
    } else {
        // "Rounded" approx for larger dots
        // Draw cross shape
        display->drawRect(x - (size/2), y - (size/2) + 1, size, size - 2, 1, color);
        display->drawRect(x - (size/2) + 1, y - (size/2), size - 2, size, 1, color);
    }
}

void render_game_state(TinyScreen *display, GameState *state, const char* my_uuid) {
    // 1. Clear Background
    display->drawRect(0, 0, SCREEN_W, SCREEN_H, 1, C_BG); 

    if (!state) return;

    // 2. Find Camera Position (Center on Player)
    float cam_x = 0;
    float cam_y = 0;
    bool found_me = false;

    for (int i = 0; i < state->player_count; i++) {
        if (strcmp(state->players[i].uuid, my_uuid) == 0) {
            cam_x = state->players[i].x;
            cam_y = state->players[i].y;
            found_me = true;
            break;
        }
    }

    // 3. Draw Food
    for (int i = 0; i < state->food_count; i++) {
        // Apply Scaling Math: (WorldPos - CamPos) * Zoom + ScreenCenter
        int sx = (int)((state->foods[i].x - cam_x) * ZOOM_FACTOR) + CENTER_X;
        int sy = (int)((state->foods[i].y - cam_y) * ZOOM_FACTOR) + CENTER_Y;
        
        // Food is usually small
        draw_scaled_dot(display, sx, sy, 2, C_FOOD);
    }

    // 4. Draw Players
    for (int i = 0; i < state->player_count; i++) {
        Snake* s = &state->players[i];
        
        uint8_t color = (strcmp(s->uuid, my_uuid) == 0) ? C_ME : C_ENEMY;

        // Draw Segments
        for (int j = 0; j < s->segment_count; j++) {
            int sx = (int)((s->segments[j].x - cam_x) * ZOOM_FACTOR) + CENTER_X;
            int sy = (int)((s->segments[j].y - cam_y) * ZOOM_FACTOR) + CENTER_Y;
            
            // DRAWING FIX:
            // By scaling the world down (coordinates get closer), 
            // but keeping the dot size at 3px, the dots will overlap.
            // This connects the segments visually without complex math.
            draw_scaled_dot(display, sx, sy, 3, color);
        }

        // Draw Head (Slightly larger)
        int hx = (int)((s->x - cam_x) * ZOOM_FACTOR) + CENTER_X;
        int hy = (int)((s->y - cam_y) * ZOOM_FACTOR) + CENTER_Y;
        
        uint8_t head_color = (color == C_ME) ? C_ME_HEAD : color;
        draw_scaled_dot(display, hx, hy, 4, head_color);
    }
}
