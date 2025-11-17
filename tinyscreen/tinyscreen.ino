#include <Wire.h>
#include <SPI.h>
#include <TinyScreen.h>
#include <WiFi101.h>
#include <string.h>

#include "utils.h"
#define MAXLEN 0x40
#define WIFITIMEOUT 15000

TinyScreen display = TinyScreen(TinyScreenPlus);

void handle_wifi() {
  int num_networks = WiFi.scanNetworks();
  SerialUSB.println(WiFi.firmwareVersion());
  display.println("scanning for wifi...");
  display.setCursor(0, 10);
  SerialUSB.print("wifi network debugging\n-----\n\n");
  for (int i = 0; i < num_networks; i++) {
    serialf("network %d: %s %d %d",
      i,
      WiFi.SSID(i),
      WiFi.RSSI(i),
      WiFi.encryptionType(i)
    );
  }
  SerialUSB.println("-----");
  char ssid[64];
  char pass[64];
  display.println("prompting for creds (on serial)");
  SerialUSB.print("enter SSID > ");
  read_line(ssid, MAXLEN);
  SerialUSB.print("enter password > ");
  read_line(pass, MAXLEN);
  serialf("trying to connect to %s with %s", ssid, pass);
  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 15000) { // 15s timeout
      SerialUSB.print(".");
      delay(500);
  }

  if (WiFi.status() != WL_CONNECTED) {
      SerialUSB.println("\nFailed to connect");
  } else {
      SerialUSB.print("\nConnected! IP: ");
      SerialUSB.println(WiFi.localIP());
  }

}

void setup(void) {
  Wire.begin();//initialize I2C before we can initialize TinyScreen- not needed for TinyScreen+
  SerialUSB.begin(9600);
  WiFi.setPins(8, 2, A3, -1);
  display.begin();
  display.setBrightness(10);
  display.clearScreen();
  display.setFont(thinPixel7_10ptFontInfo);
  display.setCursor(0, 0);
  delay(5000); // bit of time so that the serial can actually connect
  handle_wifi();
}

void loop() {
  display.clearScreen();
  display.println("waiting for input...");
  delay(1000);
  display.setCursor(0, 0);
}
