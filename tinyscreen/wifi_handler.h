#include <Wire.h>
#include <SPI.h>
#include <TinyScreen.h>
#include <WiFi101.h>
#include <string.h>
#include <WiFiUdp.h>

#include "utils.h"
#include "wifi_secrets.h"

#define MAXLEN 0x40
#define WIFITIMEOUT 15000

WiFiUDP udp;
char packet[256];
IPAddress broadcast_ip;

bool prompt_and_connect(TinyScreen display) {
    display.clearScreen();
    display.setCursor(0, 0);
    display.println("meowing for the wifi...");
    SerialUSB.println("\nmeowing for networks...");

    int num_networks = WiFi.scanNetworks();
    if (num_networks == 0) {
        SerialUSB.println("no networks found :(");
        display.println("no networks found :(");
        delay(2000);
        return false;
    }

    char ssid[MAXLEN] = {0};
    char pass[MAXLEN] = {0};
    for (int i = 0; i < num_networks; i++) {
      serialf("[%d] %s (RSSI %d) ENC %d", i, WiFi.SSID(i), WiFi.RSSI(i), WiFi.encryptionType(i));
      for (int j = 0; j < 10; j++) {
        if (!strcmp(WiFi.SSID(i), credentials[j][0])) {
          snprintf(ssid, sizeof(ssid) - 1, "%s", credentials[j][0]);
          snprintf(pass, sizeof(pass) - 1, "%s", credentials[j][1]);
          serialf("found stored credentials %s and %s", ssid, pass);
        }
      }
    }

    if (!ssid && !pass) {
      SerialUSB.print("\npick one > ");
      char input[MAXLEN];
      read_line(input, MAXLEN);
      int choice = atoi(input);
      if (choice < 0 || choice >= num_networks) {
          SerialUSB.println("kena...");
          return false;
      }

      char ssid[MAXLEN];
      strncpy(ssid, WiFi.SSID(choice), MAXLEN);
      ssid[MAXLEN - 1] = '\0';

      char pass[MAXLEN] = {0};
      int enc = WiFi.encryptionType(choice);
      if (enc != ENC_TYPE_NONE) {
          SerialUSB.print("enter password > ");
          read_line(pass, MAXLEN);
      }
    }
    
    serialf("connecting to %s...", ssid);
    display.clearScreen();
    display.setCursor(0, 0);
    display.println("da connecterrr...");

    WiFi.disconnect();
    WiFi.begin(ssid, pass);

    unsigned long start = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - start < WIFITIMEOUT) {
        SerialUSB.print(".");
        delay(500);
    }

    if (WiFi.status() != WL_CONNECTED) {
        SerialUSB.println("\nkena :(");
        display.clearScreen();
        display.setCursor(0, 0);
        display.println("connection kena :(");
        delay(2000);
        return false;
    } else {
        serialf("yay! ip: %s", ip_to_str(WiFi.localIP()));
        display.clearScreen();
        display.setCursor(0, 0);
        display.println("wahoo!");
        return true;
    }
}

bool find_server(IPAddress &serverIP) {
  udp.begin(1000);
  IPAddress ip = WiFi.localIP();
  IPAddress mask = WiFi.subnetMask();
  for (int i = 0; i<4; i++) {
    broadcast_ip[i] = (ip[i] & mask[i] | ~mask[i] & 0xFF);
  }
  SerialUSB.print("broadcasting to: ");
  SerialUSB.println(broadcast_ip);
  udp.beginPacket(broadcast_ip, 9999);
  udp.print("{\"type\": \"DISCOVER\", \"uuid\": \"TINYSCR\"}");
  udp.endPacket();

  unsigned long start = millis();
  SerialUSB.println("listening for packets > ");
  while (millis() - start < 150000) {
    int packetSize = udp.parsePacket();
    if (packetSize) {
      int len = udp.read(packet, sizeof(packet)-1);
      packet[len] = 0; //nullterm

      if (strstr(packet, "DISCOVER_REPLY")) {
        serverIP = udp.remoteIP();
        SerialUSB.print("\nfound remote ip :");
        SerialUSB.println(serverIP);
        return true;
      }
    }
  }
  SerialUSB.println("no packets found...");
  return false;
}
