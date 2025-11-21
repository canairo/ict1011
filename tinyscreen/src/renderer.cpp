#include "button_handler.h"
#include "game_handler.h"
#include <Wire.h>
#include <SPI.h>
#include <TinyScreen.h>
#include <WiFi101.h>
#include <string.h>

#define SCREEN_W 96
#define SCREEN_H 64
#define CENTER_X 48
#define CENTER_Y 32

// 8-Bit Color Definitions (RRRGGGBB)
#define C_BG      0x10 // Dark Grey/Blue
#define C_ME      0xE0 // Red (111 000 00)
#define C_ME_HEAD 0xFF // Whiteish (111 111 11)
#define C_ENEMY   0x60 // Dark Red (011 000 00)
#define C_FOOD    0xF4 // Pinkish

// Helper to draw a "fast circle" (Rectangle with corners removed)
void draw_fast_circle(TinyScreen *display, int x, int y, int size, uint8_t color) {
    // Simple Bounds Check to prevent drawing off-screen (wrapping)
    if (x < -size || x > SCREEN_W + size || y < -size || y > SCREEN_H + size) return;

    if (size <= 3) {
        // For tiny sizes, just draw a rect (cross shape logic is too expensive for 3x3)
        display->drawRect(x - 1, y - 1, 3, 3, 1, color);
    } else {
        // Draw a cross shape for larger "circles"
        // Horizontal bar
        display->drawRect(x - (size/2), y - (size/2) + 1, size, size - 2, 1, color);
        // Vertical bar
        display->drawRect(x - (size/2) + 1, y - (size/2), size - 2, size, 1, color);
    }
}

// kena vibecode once again

void render_game_state(TinyScreen *display, GameState *state, const char* my_uuid) {
    // 1. Clear Background
    // display->clearScreen(); // Slower, causes flicker
    display->drawRect(0, 0, SCREEN_W, SCREEN_H, 1, C_BG); // Fill rect is often faster/smoother

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

    // If we haven't joined yet or died, keep camera at 0,0 or last known
    if (!found_me) {
        cam_x = 0; 
        cam_y = 0; 
    }

    // 3. Draw Food (3x3 Circles)
    for (int i = 0; i < state->food_count; i++) {
        // Calculate Screen Position relative to Camera
        int sx = (int)(state->foods[i].x - cam_x) + CENTER_X;
        int sy = (int)(state->foods[i].y - cam_y) + CENTER_Y;
        
        draw_fast_circle(display, sx, sy, 3, C_FOOD);
    }

    // 4. Draw Players
    for (int i = 0; i < state->player_count; i++) {
        Snake* s = &state->players[i];
        
        // Determine Color
        uint8_t color = (strcmp(s->uuid, my_uuid) == 0) ? C_ME : C_ENEMY;

        // Draw Segments (4x4)
        for (int j = 0; j < s->segment_count; j++) {
            int sx = (int)(s->segments[j].x - cam_x) + CENTER_X;
            int sy = (int)(s->segments[j].y - cam_y) + CENTER_Y;
            
            draw_fast_circle(display, sx, sy, 4, color);
        }

        // Draw Head (5x5)
        int hx = (int)(s->x - cam_x) + CENTER_X;
        int hy = (int)(s->y - cam_y) + CENTER_Y;
        
        // If it's me, draw a brighter head
        uint8_t head_color = (color == C_ME) ? C_ME_HEAD : color;
        draw_fast_circle(display, hx, hy, 5, head_color);
    }
}
