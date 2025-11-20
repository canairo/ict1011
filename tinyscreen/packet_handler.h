#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <math.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

// ================= STRUCTURES =================

typedef struct {
    float x;
    float y;
} Vector2;

typedef struct {
    char* uuid;       // Null-terminated string
    float x;
    float y;
    float angle;      // Radians
    uint8_t boost;    // 1 or 0
    float length;
    uint16_t segment_count;
    Vector2* segments; // Array of Vector2
} Snake;

typedef struct {
    float x;
    float y;
    uint8_t size;
} Food;

typedef struct {
    uint16_t player_count;
    Snake* players;    // Array of Snakes
    
    uint16_t food_count;
    Food* foods;       // Array of Food
} GameState;

// ================= HELPER: READING =================

// Helper to read bytes and advance pointer
#define READ_VAL(ptr, type) (*(type*)read_and_advance(&ptr, sizeof(type)))
#define SWAP_UINT16(x) ((((x) & 0xFF) << 8) | (((x) >> 8) & 0xFF))

// Helper to safely read memory and move the cursor
void* read_and_advance(uint8_t** cursor, size_t bytes) {
    void* current = *cursor;
    *cursor += bytes;
    return current;
}

// Helper to read Big Endian Float (Network Byte Order)
float read_float_be(uint8_t** cursor) {
    uint32_t temp = READ_VAL(*cursor, uint32_t);
    // Swap bytes for Big Endian if on Little Endian machine (standard x86/ARM)
    uint32_t swapped = ((temp >> 24) & 0xff) | 
                       ((temp << 8) & 0xff0000) | 
                       ((temp >> 8) & 0xff00) | 
                       ((temp << 24) & 0xff000000);
    float res;
    memcpy(&res, &swapped, sizeof(float));
    return res;
}

// Helper to read Big Endian Short
uint16_t read_short_be(uint8_t** cursor) {
    uint16_t temp = READ_VAL(*cursor, uint16_t);
    return SWAP_UINT16(temp);
}

// ================= CORE FUNCTION =================

GameState* decompress_packet(uint8_t* data, size_t len) {
    uint8_t* cursor = data;
    GameState* state = (GameState*)malloc(sizeof(GameState));

    // 1. READ PLAYERS
    state->player_count = read_short_be(&cursor);
    state->players = (Snake*)malloc(sizeof(Snake) * state->player_count);

    for (int i = 0; i < state->player_count; i++) {
        Snake* s = &state->players[i];

        // UUID
        uint8_t uuid_len = READ_VAL(cursor, uint8_t);
        s->uuid = (char*)malloc(uuid_len + 1);
        memcpy(s->uuid, read_and_advance(&cursor, uuid_len), uuid_len);
        s->uuid[uuid_len] = '\0'; // Null terminate

        // Properties
        s->x = read_float_be(&cursor);
        s->y = read_float_be(&cursor);
        
        uint16_t raw_angle = read_short_be(&cursor);
        s->angle = ((float)raw_angle / 65535.0f) * (2.0f * M_PI); // Unmap
        
        s->boost = READ_VAL(cursor, uint8_t);
        s->length = read_float_be(&cursor);

        // Segments
        s->segment_count = read_short_be(&cursor);
        s->segments = (Vector2*)malloc(sizeof(Vector2) * s->segment_count);
        
        for (int j = 0; j < s->segment_count; j++) {
            s->segments[j].x = read_float_be(&cursor);
            s->segments[j].y = read_float_be(&cursor);
        }
    }

    // 2. READ FOOD
    state->food_count = read_short_be(&cursor);
    state->foods = (Food*)malloc(sizeof(Food) * state->food_count);

    for (int i = 0; i < state->food_count; i++) {
        state->foods[i].x = read_float_be(&cursor);
        state->foods[i].y = read_float_be(&cursor);
        state->foods[i].size = READ_VAL(cursor, uint8_t);
    }

    return state;
}

// ================= CLEANUP =================

void free_gamestate(GameState* state) {
    if (!state) return;
    
    for (int i = 0; i < state->player_count; i++) {
        free(state->players[i].uuid);
        free(state->players[i].segments);
    }
    free(state->players);
    free(state->foods);
    free(state);
}
