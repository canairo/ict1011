#include <Wire.h>
#include <SPI.h>
#include <TinyScreen.h>
#include <WiFi101.h>
#include <string.h>

#include "wifi_handler.h"
#include "game_handler.h"
#include "renderer.h"

typedef enum {
  NO_WIFI,
  FINDING_SERVER,
  CONNECTED_TO_SERVER
} State;

WiFiUDP udp;
char received_packet[2048];
int debug = 1;
State state;
GameState* game_state;

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
    state = NO_WIFI;
    game_state = (GameState*)calloc(1, sizeof(GameState));
    serialf("[debug] allocated game_state at %p\n", game_state);
    delay(2000);
}

void loop() {
  if (state == NO_WIFI) {
    if (prompt_and_connect(display))  {
      state = FINDING_SERVER;
      udp.begin(1000);
    }
    return;
  }

  int packet_size = udp.parsePacket();
  if (packet_size) {
    int read_amt = (packet_size > 2048) ? 2048 : packet_size;
    int len = udp.read(received_packet, packet_size);
    if (debug) {
      serialf("\n[debug] received packet from %s:%d\n------\n",
          ip_to_str(udp.remoteIP()),
          udp.remotePort()
      );
      hexdump(received_packet, packet_size);
      serialf("\n------\n");
    }
  } else {

    // i would want to clear the entire buffer
    // but i am worried that would take too long
    // so we just set the first byte as null
    // happy happy liao
    received_packet[0] = 0;

  }

  switch (state) {
    case FINDING_SERVER:
      broadcast_packet(udp);
      remote_ip = receive_discover(udp, received_packet);
      if (remote_ip != IPAddress(69, 69, 69, 69)) {
        join_server(udp, remote_ip);
        serialf("[debug] found remote ip at %s\n",
          ip_to_str(remote_ip)
        );
        state = CONNECTED_TO_SERVER;
      }
      break;

    case CONNECTED_TO_SERVER:
      if (assert_game_data(received_packet)) {
        serialf("[debug] received game state > \n");
        hexdump(received_packet, packet_size);
        serialf("\n");
        serialf("[debug] parameters passed: game_state %p, packet_size %d\n",
            game_state,
            packet_size
        );
        free_gamestate_contents(game_state); // lmfao kena memory leak
        decompress_packet_into_game_state(game_state, (uint8_t*)received_packet, packet_size);
        serialf("[debug] successfully decompressed game state\n");
        serialf("%s", debug_state(game_state));
        render_game_state(&display, game_state, "meowboy");
      }
      break;
  }
}

