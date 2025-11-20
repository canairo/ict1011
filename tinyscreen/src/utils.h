#ifndef UTILS_H
#define UTILS_H

#include "TinyScreen.h"
#include <Wire.h>
#include <SPI.h>
#include <TinyScreen.h>
#include <WiFi101.h>
#include <string.h>

// Declarations for utils.cpp

template <typename... Args>
void serialf(const char *fmt, Args... args) {
  char buf[128];
  snprintf(buf, sizeof(buf), fmt, args...);
  SerialUSB.print(buf);
}

void debug_msg(char *msg, TinyScreen &display);
void hexdump(char *buf, int size);
const char* ip_to_str(IPAddress ip);
void read_line(char *buffer, int maxLen);

#endif // UTILS_H
