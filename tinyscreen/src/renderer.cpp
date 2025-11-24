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

#define MAP_SIZE 3000.0f
#define HALF_MAP 1500.0f

#define ZOOM_FACTOR 0.15 

#define C_BG      0x10 // Dark Grey/Blue
#define C_ME      0xE0 // Red
#define C_ME_HEAD 0xFF // Whiteish
#define C_ENEMY   0x60 // Dark Red
#define C_FOOD    0xF4 // Pinkish

void draw_scaled_dot(TinyScreen *display, int x, int y, int size, uint8_t color) {
    if (x < -10 || x > SCREEN_W + 10 || y < -10 || y > SCREEN_H + 10) return;
    if (size <= 1) {
        display->drawPixel(x, y, color);
    } else if (size == 2) {
        display->drawRect(x, y, 2, 2, 1, color);
    } else {
        display->drawRect(x - (size/2), y - (size/2) + 1, size, size - 2, 1, color);
        display->drawRect(x - (size/2) + 1, y - (size/2), size - 2, size, 1, color);
    }
}

float get_shortest_diff(float target, float current) {
    float diff = target - current;
    if (diff > HALF_MAP) diff -= MAP_SIZE;
    else if (diff < -HALF_MAP) diff += MAP_SIZE;
    return diff;
}

void get_screen_pos(float wx, float wy, float cam_x, float cam_y, int *out_x, int *out_y) {
    float dx = wx - cam_x;
    float dy = wy - cam_y;
    if (dx > HALF_MAP) dx -= MAP_SIZE;
    else if (dx < -HALF_MAP) dx += MAP_SIZE;

    if (dy > HALF_MAP) dy -= MAP_SIZE;
    else if (dy < -HALF_MAP) dy += MAP_SIZE;

    *out_x = CENTER_X + (int)(dx * ZOOM_FACTOR);
    *out_y = CENTER_Y + (int)(dy * ZOOM_FACTOR);
}

void render_game_state(TinyScreen *display, GameState *state, const char* my_uuid) {
    display->drawRect(0, 0, SCREEN_W, SCREEN_H, 1, C_BG); 
    if (!state) return;

    static float cam_x = 1500;
    static float cam_y = 1500;
    static bool cam_initialized = false;

    Snake* me = NULL;
    for (int i = 0; i < state->player_count; i++) {
        if (strcmp(state->players[i].uuid, my_uuid) == 0) {
            me = &state->players[i];
            break;
        }
    }

    if (me) {
        if (!cam_initialized) {
            cam_x = me->x;
            cam_y = me->y;
            cam_initialized = true;
        } else {
            float diff_x = get_shortest_diff(me->x, cam_x);
            float diff_y = get_shortest_diff(me->y, cam_y);
            
            cam_x += diff_x * 0.1f;
            cam_y += diff_y * 0.1f;

            if (cam_x < 0) cam_x += MAP_SIZE;
            if (cam_x >= MAP_SIZE) cam_x -= MAP_SIZE;
            if (cam_y < 0) cam_y += MAP_SIZE;
            if (cam_y >= MAP_SIZE) cam_y -= MAP_SIZE;
        }
    }

    for (int i = 0; i < state->food_count; i++) {
        int sx, sy;
        get_screen_pos(state->foods[i].x, state->foods[i].y, cam_x, cam_y, &sx, &sy);
        draw_scaled_dot(display, sx, sy, 2, C_FOOD);
    }

    for (int i = 0; i < state->player_count; i++) {
        Snake* s = &state->players[i];
        bool is_me = (strcmp(s->uuid, my_uuid) == 0);
        uint8_t color = is_me ? C_ME : C_ENEMY;

        float prev_raw_x = s->x;
        float prev_raw_y = s->y;
        
        float cont_x = s->x;
        float cont_y = s->y;

        int hx, hy;
        get_screen_pos(cont_x, cont_y, cam_x, cam_y, &hx, &hy);
        
        uint8_t head_color = is_me ? C_ME_HEAD : color;
        draw_scaled_dot(display, hx, hy, 4, head_color);

        for (int j = 0; j < s->segment_count; j++) {
            float curr_raw_x = s->segments[j].x;
            float curr_raw_y = s->segments[j].y;

            float dx = curr_raw_x - prev_raw_x;
            float dy = curr_raw_y - prev_raw_y;

            if (dx < -HALF_MAP) dx += MAP_SIZE;
            else if (dx > HALF_MAP) dx -= MAP_SIZE;

            if (dy < -HALF_MAP) dy += MAP_SIZE;
            else if (dy > HALF_MAP) dy -= MAP_SIZE;

            cont_x += dx;
            cont_y += dy;

            int sx, sy;
            get_screen_pos(cont_x, cont_y, cam_x, cam_y, &sx, &sy);

            draw_scaled_dot(display, sx, sy, 3, color);

            prev_raw_x = curr_raw_x;
            prev_raw_y = curr_raw_y;
        }
    }
}

void draw_menu_bitmap(TinyScreen &display, const uint8_t *bitmap) {
  display.setX(0, 95);
  display.setY(0, 63);
  display.startData();
  uint8_t lineBuffer[96];
  int bitmapIndex = 0;
  for (int y = 0; y < 64; y++) {
    for (int byteOffset = 0; byteOffset < 12; byteOffset++) {
      uint8_t packedByte = bitmap[bitmapIndex++];
      for (int bit = 0; bit < 8; bit++) {
        bool isWhite = packedByte & (0x80 >> bit);
        lineBuffer[(byteOffset * 8) + bit] = isWhite ? 0xFF : 0x00; 
      }
    }
    display.writeBuffer(lineBuffer, 96);
  }

  display.endTransfer();
}
