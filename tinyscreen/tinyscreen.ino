#include <Wire.h>
#include <SPI.h>
#include <TinyScreen.h>
#include <WiFi101.h>
#include <string.h>

TinyScreen display = TinyScreen(TinyScreenPlus);

void setup(void) {
  Wire.begin();//initialize I2C before we can initialize TinyScreen- not needed for TinyScreen+
  SerialUSB.begin(9600);
  WiFi.setPins(8, 2, A3, -1);
  display.begin();
  display.setBrightness(10);
}

template <typename... Args>
void serialf(const char *fmt, Args... args) {
  char buf[128];
  snprintf(buf, sizeof(buf), fmt, args...);
  SerialUSB.print(buf);
}

void debug_wifi(int numNetworks) {
  SerialUSB.print("wifi network debugging\n-----\n\n");
  for (int i = 0; i < numNetworks; i++) {
    serialf("network %d: %s %d %d\n",
      i,
      WiFi.SSID(i),
      WiFi.RSSI(i),
      WiFi.encryptionType(i)
    );
  }
  SerialUSB.println("--------");
}

void loop() {
  display.clearScreen();
  display.setFont(thinPixel7_10ptFontInfo);
  int numNetworks = WiFi.scanNetworks();
  display.setCursor(0, 0);
  display.print(numNetworks);
  display.println(" meowworks found");
  debug_wifi(numNetworks);
  delay(2500);
}
