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
  SerialUSB.print(buf);
}

void debug_msg(char *msg, TinyScreen &display) {
  display.clearScreen();
  display.setCursor(0, 0);
  display.println(msg);
}

void hexdump(char *buf, int size) {
  for (int i = 0; i<size; i++) {
    serialf("%02x", buf[i]);
  }
}

const char* ip_to_str(IPAddress ip) {
    static char buf[32];
    sprintf(buf, "%d.%d.%d.%d",
            (int)ip[0], (int)ip[1], (int)ip[2], (int)ip[3]);
    return buf;
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

