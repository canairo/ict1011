#include <Wire.h>
#include <SPI.h>
#include <TinyScreen.h>
#include <WiFi101.h>
#include <string.h>
#include <Wireling.h>

#include "utils.h"
#include "button_handler.h"

ButtonInput view_input() {
  if (!digitalRead(A0)) return INPUT_BOOST;
  if (!digitalRead(A1)) return INPUT_LEFT;
  if (!digitalRead(A2)) return INPUT_RIGHT;
  return NO_INPUT; 
}
