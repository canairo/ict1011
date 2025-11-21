#include <Wire.h>
#include <SPI.h>
#include <TinyScreen.h>
#include <WiFi101.h>
#include <string.h>
#include <Wireling.h>
#include "utils.h"

void view_input() {
  if (!digitalRead(A0)) serialf("[debug] this nonsense is working");
}
