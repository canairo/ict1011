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

bool prompt_and_connect(TinyScreen &display) {
    debug_msg("meowing for wifi", display); 
    SerialUSB.println("\n[debug] meowing for networks...");

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
      serialf("[%d] %s (RSSI %d) ENC %d\n", i, WiFi.SSID(i), WiFi.RSSI(i), WiFi.encryptionType(i));
      for (int j = 0; j < 10; j++) {
        if (!strcmp(WiFi.SSID(i), credentials[j][0])) {
          snprintf(ssid, sizeof(ssid) - 1, "%s", credentials[j][0]);
          snprintf(pass, sizeof(pass) - 1, "%s", credentials[j][1]);
          serialf("[debug] found stored credentials %s and %s\n", ssid, pass);
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
    
    serialf("connecting to %s...\n", ssid);
    debug_msg("connecting...", display);

    WiFi.disconnect();
    WiFi.begin(ssid, pass);

    unsigned long start = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - start < WIFITIMEOUT) {
        SerialUSB.print(".");
        delay(500);
    }

    if (WiFi.status() != WL_CONNECTED) {
        SerialUSB.println("\nkena :(");
        debug_msg("connection kena...", display);
        delay(2000);
        return false;
    } else {
        serialf("yay! ip: %s\n", ip_to_str(WiFi.localIP()));
        debug_msg("connected to wifi!", display);
        return true;
    }
}

void send_packet(WiFiUDP &udp, IPAddress addr, int port, char* packet) {
  udp.beginPacket(addr, port);
  udp.print(packet);
  udp.endPacket();
}

void broadcast_packet(WiFiUDP &udp) {
  IPAddress ip = WiFi.localIP();
  IPAddress mask = WiFi.subnetMask();
  IPAddress broadcast_ip;
  for (int i = 0; i<4; i++) {
    broadcast_ip[i] = (ip[i] & mask[i] | ~mask[i] & 0xFF);
  }
  send_packet(udp, broadcast_ip, 9999, "{\"type\": \"DISCOVER\", \"uuid\": \"meowboy\"}");
}

IPAddress receive_discover(WiFiUDP &udp, char* received_packet) {
  serialf("[debug] scanning packet %s\n", received_packet);
  if (strstr(received_packet, "DISCOVER_RECEIVED")) {
    serialf("[debug] successfully received DISCOVER_RECEIVED packet from %s\n",
        ip_to_str(udp.remoteIP())      
    );
    return udp.remoteIP();
  }
  return IPAddress(69, 69, 69, 69); // sentinel
}

void join_server(WiFiUDP &udp, IPAddress remote_ip) {
  send_packet(udp, broadcast_ip, 9999, "{\"type\": \"JOIN\", \"uuid\": \"meowboy\"}");
  serialf("[debug] sent JOIN packet to remote %s\n", ip_to_str(remote_ip));
}

bool assert_game_data(char* received_packet) {
  int res = strncmp(received_packet, "GAMEDATA", 8);
  /*
  serialf("compared %s to %s: result %d",
      "(GAMEDATA)",
      received_packet,
      res
  );
  */
  return !res;
}

/* 
bool find_server(IPAddress &serverIP, TinyScreen display) {
  debug_msg("finding remote server...", display);
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
  SerialUSB.println("beginning listener on port 1000");
  int loop = 0;
  while (!loop) {
    memset(packetBuffer, 0, sizeof(packetBuffer));
    int packetSize = udp.parsePacket();
    if (packetSize)
    {
      int read_amt = (packetSize > 2048) ? 2048 : packetSize;
      int len = udp.read(packetBuffer, packetSize);
      serialf("\nreceived packet from %d:%d\n",
          ip_to_str(udp.remoteIP()),
          udp.remotePort()
      );
      hexdump(packetBuffer, packetSize);
      if (len > 0) packetBuffer[len] = 0;
      if (strstr(packetBuffer, "DISCOVER_RECEIVED")) {
        serverIP = udp.remoteIP();
        serialf("found remote IP: %s at port %d\n", 
            ip_to_str(serverIP),
            udp.remotePort()
        );
        debug_msg("found remote server!", display);
        serialf("joining remote server...");
        udp.beginPacket(serverIP, 9999);
        udp.print("{\"type\": \"JOIN\", \"uuid\": \"meowboy\"}");
        udp.endPacket();
      } else {
        udp.beginPacket(udp.remoteIP(), udp.remotePort());
        udp.print(ReplyBuffer);
        udp.endPacket();
      }
    }
  } 
}
*/
