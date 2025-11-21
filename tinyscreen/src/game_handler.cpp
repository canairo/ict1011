// most of this is vibecoded
// unfortunately the bytepacked struct format is really nice and cool
// but coming up with the schema, packing and unpacking would've just taken me too long
// in another life i would've written it myself... another life where this project isn't due in 5 days and i still don't have a snake rendered on the tinyscreen.

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <math.h>

#include "button_handler.h"
#include "game_handler.h"
#include "utils.h"

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif
// ================= HELPER: SAFE READING =================

// Reads 'size' bytes into 'dest', then advances cursor.
// Uses memcpy to prevent ARM HardFaults on unaligned memory.
void safe_read(uint8_t** cursor, void* dest, size_t size) {
    memcpy(dest, *cursor, size);
    *cursor += size;
}

// Advances cursor to skip padding
void skip_bytes(uint8_t** cursor, size_t size) {
    *cursor += size;
}

// ================= CORE FUNCTION =================

void decompress_packet_into_game_state(GameState* state, uint8_t* data, size_t len) {
    // Offset 8: GAMEDATA header ends.
    uint8_t* cursor = data + 8; 

    // 1. Player Count
    safe_read(&cursor, &state->player_count, sizeof(uint16_t));
    skip_bytes(&cursor, 2); // Skip 2 bytes padding

    state->players = (Snake*)malloc(sizeof(Snake) * state->player_count);

    serialf("[debug] decompressed player count: %d\n", state->player_count);

    for (int i = 0; i < state->player_count; i++) {
        Snake* s = &state->players[i];

        // 2. UUID
        uint8_t uuid_len;
        safe_read(&cursor, &uuid_len, sizeof(uint8_t));
        
        s->uuid = (char*)malloc(uuid_len + 1);
        safe_read(&cursor, s->uuid, uuid_len);
        s->uuid[uuid_len] = '\0'; // Null terminate
        
        // Skip Variable Padding (Align to 4)
        // Calculation: (4 - (1 + len) % 4) % 4
        int current_chunk = 1 + uuid_len;
        int pad_needed = (4 - (current_chunk % 4)) % 4;
        skip_bytes(&cursor, pad_needed);

        // 3. Position (Floats)
        safe_read(&cursor, &s->x, sizeof(float));
        safe_read(&cursor, &s->y, sizeof(float));

        // 4. Angle (U16) and Boost (U8)
        uint16_t raw_angle;
        safe_read(&cursor, &raw_angle, sizeof(uint16_t));
        s->angle = ((float)raw_angle / 65535.0f) * (2.0f * M_PI);

        safe_read(&cursor, &s->boost, sizeof(uint8_t));

        skip_bytes(&cursor, 1); // Skip 1 byte padding (after Boost)

        // 5. Length (Float)
        safe_read(&cursor, &s->length, sizeof(float));

        // 6. Segments
        safe_read(&cursor, &s->segment_count, sizeof(uint16_t));
        skip_bytes(&cursor, 2); // Skip 2 bytes padding

        s->segments = (Vector2*)malloc(sizeof(Vector2) * s->segment_count);
        for (int j = 0; j < s->segment_count; j++) {
            safe_read(&cursor, &s->segments[j].x, sizeof(float));
            safe_read(&cursor, &s->segments[j].y, sizeof(float));
        }
    }

    // 7. Food
    safe_read(&cursor, &state->food_count, sizeof(uint16_t));
    skip_bytes(&cursor, 2); // Skip 2 bytes padding

    state->foods = (Food*)malloc(sizeof(Food) * state->food_count);

    for (int i = 0; i < state->food_count; i++) {
        safe_read(&cursor, &state->foods[i].x, sizeof(float));
        safe_read(&cursor, &state->foods[i].y, sizeof(float));
        safe_read(&cursor, &state->foods[i].size, sizeof(uint8_t));
        
        skip_bytes(&cursor, 3); // Skip 3 bytes padding
    }
}


// returns an idx
int get_snake_by_uuid(GameState *game_state, char* uuid) {
  for (int i = 0; i < game_state->player_count; i++) {
     if (!strcmp(game_state->players[i].uuid, uuid)) {
       return i;
     }
  }
  return -1;
}

void populate_input_packet(char *input_packet, GameState *game_state, ButtonInput current_input, char* uuid) {
    int idx = get_snake_by_uuid(game_state, uuid);
    if (idx >= 0) {
      float current_angle = game_state->players[idx].angle;
      serialf("[debug] snake with uuid %s has current angle %f\n");
    } else {
      serialf("[debug] no snake with uuid %s found.\n", uuid);
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

void free_gamestate_contents(GameState* state) {
    if (!state) return;
    
    // 1. Free existing players
    if (state->players) {
        for (int i = 0; i < state->player_count; i++) {
            // Free the dynamically allocated UUID
            if (state->players[i].uuid) {
                free(state->players[i].uuid);
            }
            // Free the dynamically allocated segments array
            if (state->players[i].segments) {
                free(state->players[i].segments);
            }
        }
        // Free the array of Snake structs
        free(state->players);
        state->players = NULL;
    }

    // 2. Free existing food
    if (state->foods) {
        free(state->foods);
        state->foods = NULL;
    }

    state->player_count = 0;
    state->food_count = 0;
}
