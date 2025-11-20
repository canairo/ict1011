#ifndef RENDERER_H
#define RENDERER_H

// Declarations for renderer.cpp
#include "game_handler.h"
#include <TinyScreen.h>

void draw_fast_circle(TinyScreen *display, int x, int y, int size, uint8_t color);
void render_game_state(TinyScreen *display, GameState *state, const char* my_uuid);

#endif // RENDERER_H
