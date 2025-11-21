#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <math.h>
#include "button_handler.h"


#ifndef GAME_HANDLER_H
#define GAME_HANDLER_H

// Declarations for game_handler.cpp

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

void safe_read(uint8_t** cursor, void* dest, size_t size);
void skip_bytes(uint8_t** cursor, size_t size);
void decompress_packet_into_game_state(GameState* state, uint8_t* data, size_t len);
const char* debug_state(GameState* state);
void free_gamestate_contents(GameState* state);
void populate_input_packet(char *input_packet, GameState *game_state, ButtonInput current_input, char* uuid);
#endif // GAME_HANDLER_H
