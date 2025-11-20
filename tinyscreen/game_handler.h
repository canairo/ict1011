// most of this is vibecoded
// unfortunately the bytepacked struct format is really nice and cool
// but coming up with the schema, packing and unpacking would've just taken me too long
// in another life i would've written it myself... another life where this project isn't due in 5 days and i still don't have a snake rendered on the tinyscreen.

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

#define READ_VAL(ptr, type) (*(type*)read_and_advance(&ptr, sizeof(type)))
#define SWAP_UINT16(x) ((((x) & 0xFF) << 8) | (((x) >> 8) & 0xFF))

void* read_and_advance(uint8_t** cursor, size_t bytes) {
    void* current = *cursor;
    *cursor += bytes;
    return current;
}

float read_float_be(uint8_t** cursor) {
    uint32_t temp = READ_VAL(*cursor, uint32_t);
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

void decompress_packet_into_game_state(GameState* state, uint8_t* data, size_t len) {
    uint8_t* cursor = data + 8; // skip GAMEDATA header;
    state->player_count = read_short_be(&cursor);
    state->players = (Snake*)malloc(sizeof(Snake) * state->player_count);

    serialf("[debug] starting to decompress >\n");
    for (int i = 0; i < state->player_count; i++) {
        Snake* s = &state->players[i];

        uint8_t uuid_len = READ_VAL(cursor, uint8_t);
        s->uuid = (char*)malloc(uuid_len + 1);
        memcpy(s->uuid, read_and_advance(&cursor, uuid_len), uuid_len);
        s->uuid[uuid_len] = '\0'; // Null terminate
        serialf("[debug] created snake w/ uuid %s\n", s->uuid);
        s->x = read_float_be(&cursor);
        s->y = read_float_be(&cursor);
        
        serialf("[debug] successfully scanned x=%f and y=%f",
            s->x, s->y
        );
        uint16_t raw_angle = read_short_be(&cursor);
        s->angle = ((float)raw_angle / 65535.0f) * (2.0f * M_PI); // Unmap
       
        serialf("[debug] successfully scanned angle=%f", s->angle);

        s->boost = READ_VAL(cursor, uint8_t);
        s->length = read_float_be(&cursor);
        serialf("[debug] successfully scanned boost=%d and length=%d",
            s->boost,
            s->length
        );
        s->segment_count = read_short_be(&cursor);
        s->segments = (Vector2*)malloc(sizeof(Vector2) * s->segment_count);
        for (int j = 0; j < s->segment_count; j++) {
            s->segments[j].x = read_float_be(&cursor);
            s->segments[j].y = read_float_be(&cursor);
        }
    }

    state->food_count = read_short_be(&cursor);
    state->foods = (Food*)malloc(sizeof(Food) * state->food_count);

    for (int i = 0; i < state->food_count; i++) {
        state->foods[i].x = read_float_be(&cursor);
        state->foods[i].y = read_float_be(&cursor);
        state->foods[i].size = READ_VAL(cursor, uint8_t);
    }
}

const char* debug_state(GameState* state) {
    static char buf[8192];
    buf[0] = '\0';
    size_t used = 0;
    int n;

    if (!state) {
        snprintf(buf, sizeof(buf), "<NULL GameState>");
        return buf;
    }

    n = snprintf(buf + used, sizeof(buf) - used, "GameState:\n  Players: %d\n", state->player_count);
    used += n;

    for (int i = 0; i < state->player_count; i++) {
        Snake* s = &state->players[i];

        n = snprintf(buf + used, sizeof(buf) - used,
            "  Player %d:\n"
            "    UUID: %s\n"
            "    Pos: (%.2f, %.2f)\n"
            "    Angle: %.2f rad\n"
            "    Boost: %d\n"
            "    Length: %.2f\n"
            "    Segments: %d\n",
            i, s->uuid, s->x, s->y, s->angle, s->boost, s->length, s->segment_count);
        used += n;

        for (int j = 0; j < s->segment_count; j++) {
            n = snprintf(buf + used, sizeof(buf) - used,
                "      Segment %d: (%.2f, %.2f)\n",
                j, s->segments[j].x, s->segments[j].y);
            used += n;

            if (used >= sizeof(buf)) {
                // truncated
                buf[sizeof(buf) - 1] = '\0';
                return buf;
            }
        }
    }

    n = snprintf(buf + used, sizeof(buf) - used, "  Food: %d\n", state->food_count);
    used += n;

    for (int i = 0; i < state->food_count; i++) {
        n = snprintf(buf + used, sizeof(buf) - used,
            "    Food %d: Pos(%.2f, %.2f) Size %d\n",
            i, state->foods[i].x, state->foods[i].y, state->foods[i].size);
        used += n;

        if (used >= sizeof(buf)) {
            buf[sizeof(buf) - 1] = '\0';
            return buf;
        }
    }

    return buf;
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
