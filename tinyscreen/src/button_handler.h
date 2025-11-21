#ifndef BUTTON_HANDLER_H
#define BUTTON_HANDLER_H

typedef enum {
  NO_INPUT,
  INPUT_BOOST,
  INPUT_RIGHT,
  INPUT_LEFT,
} ButtonInput;

ButtonInput view_input();

#endif // GAME_HANDLER_H
