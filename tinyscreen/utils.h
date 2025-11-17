#include <Wire.h>
#include <SPI.h>
#include <TinyScreen.h>
#include <WiFi101.h>
#include <string.h>

#define MAXLEN 0x40

template <typename... Args>
void serialf(const char *fmt, Args... args) {
  char buf[128];
  snprintf(buf, sizeof(buf), fmt, args...);
  SerialUSB.println(buf);
}

void read_line(char *buffer, int maxLen) {
  int i = 0;
  while (true) {
    if (SerialUSB.available()) {
      char c = SerialUSB.read();

      if (c == '\n' || c == '\r') {
        buffer[i] = '\0';
        return;
      }

      if (i < maxLen - 1) buffer[i++] = c;
    }
  }
}


