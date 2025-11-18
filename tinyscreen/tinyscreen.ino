#include <Wire.h>
#include <SPI.h>
#include <TinyScreen.h>
#include <WiFi101.h>
#include <string.h>

#include "wifi_handler.h"

TinyScreen display = TinyScreen(TinyScreenPlus);
IPAddress remote_ip = IPAddress(69, 69, 69, 69); // quote unquote sentinel

void setup() {
    Wire.begin();
    SerialUSB.begin(9600);
    while (!SerialUSB);
    WiFi.setPins(8, 2, A3, -1); // necessary for whatever reason
    display.begin();
    display.setBrightness(10);
    display.clearScreen();
    display.setFont(thinPixel7_10ptFontInfo);
    display.setCursor(0, 0);
    delay(2000);
}

void loop() {
    char ReplyBuffer[256];
    strcpy(ReplyBuffer, "OK\n");
    char packetBuffer[256];
    display.clearScreen();
    display.setCursor(0,0);
    if (WiFi.status() != WL_CONNECTED) {
        prompt_and_connect(display);
    }
    else {
      udp.begin(1000);
      SerialUSB.println("beginning listener on port 1000");
      while (true) {
        int packetSize = udp.parsePacket();
        if (packetSize)
        {
          SerialUSB.print("Received packet of size ");
          SerialUSB.println(packetSize);
          SerialUSB.print("From ");
          IPAddress remoteIp = udp.remoteIP();
          SerialUSB.print(remoteIp);
          SerialUSB.print(", port ");
          SerialUSB.println(udp.remotePort());

          int len = udp.read(packetBuffer, 255);
          if (len > 0) packetBuffer[len] = 0;
          SerialUSB.println("Contents:");
          SerialUSB.println(packetBuffer);
          
          udp.beginPacket(udp.remoteIP(), udp.remotePort());
          udp.write(ReplyBuffer);
          udp.endPacket();
        }
      } 
    }
    delay(5000);
    display.println("rawr");
}

