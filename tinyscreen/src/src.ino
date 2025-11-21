#include <Wire.h>
#include <SPI.h>
#include <TinyScreen.h>
#include <WiFi101.h>
#include <string.h>
#include <WiFiUdp.h>
#include <Wireling.h>

#include "wifi_handler.h"
#include "game_handler.h"
#include "renderer.h"
#include "utils.h"
#include "wifi_secrets.h"
#include "button_handler.h"

typedef enum {
  NO_WIFI,
  FINDING_SERVER,
  CONNECTED_TO_SERVER
} State;

WiFiUDP udp;
unsigned long last_broadcast = 0;
unsigned long last_input = 0;
unsigned long last_packet_recv = 0;
char received_packet[2048];
int debug = 0;
State state;
GameState* game_state;

ButtonInput current_input;
char input_packet[sizeof(InputPacket)];

TinyScreen display = TinyScreen(TinyScreenPlus);
IPAddress remote_ip = IPAddress(69, 69, 69, 69); // quote unquote sentinel

void setup() {
    // i want to clean this up actually
    Wire.begin();
    Wireling.begin();
    SerialUSB.begin(9600);
    pinMode(A0, INPUT_PULLUP);
    pinMode(A1, INPUT_PULLUP);
    pinMode(A2, INPUT_PULLUP);
    while (!SerialUSB);
    WiFi.setPins(8, 2, A3, -1); // necessary for whatever reason
    display.begin();
    display.setBrightness(10);
    display.clearScreen();
    display.setFont(thinPixel7_10ptFontInfo);
    display.setCursor(0, 0);
    state = NO_WIFI;
    game_state = (GameState*)calloc(1, sizeof(GameState));
    serialf("[debug] meow meow woof woof game_state at %p\n", game_state);
    delay(2000);
}

void loop() {

  // handle inputs
  ButtonInput current_input = view_input();
  if (current_input != NO_INPUT) {
    serialf("[debug] button input is %d\n", current_input);
  }

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
    last_packet_recv = millis();
    /*
    if (debug) {
      serialf("\n[debug] received packet from %s:%d\n------\n",
          ip_to_str(udp.remoteIP()),
          udp.remotePort()
      );
      hexdump(received_packet, packet_size);
      serialf("\n------\n[debug] string form: %s\n", received_packet);
    }
    */
  } else {
    // i would want to clear the entire buffer
    // but i am worried that would take too long
    // so we just set the first byte as null
    // happy happy liao
    received_packet[0] = 0;
    if ((millis() - last_packet_recv > 500) && (state == CONNECTED_TO_SERVER)) {
      serialf("[DEBUG] haven't received a packet for over 500ms\n");
      debug_msg("kena!!!!", display);
      state = NO_WIFI;
      return;
    }
  }
 
  switch (state) {
    case FINDING_SERVER:
      if (millis() - last_broadcast > 1000) {
        broadcast_packet(udp);
        last_broadcast = millis();
      }
      remote_ip = receive_discover(udp, received_packet);
      if (remote_ip != IPAddress(69, 69, 69, 69)) {
        join_server(udp, remote_ip);
        state = CONNECTED_TO_SERVER;
      }
      break;

    case CONNECTED_TO_SERVER:
      if (assert_game_data(received_packet)) {
        free_gamestate_contents(game_state); // lmfao kena memory leak
        decompress_packet_into_game_state(game_state, (uint8_t*)received_packet, packet_size);
        render_game_state(&display, game_state, "meowboy");
      }
      // handle inps
      if (current_input != NO_INPUT) {
        populate_input_packet(input_packet, game_state, current_input, "meowboy");
        if (millis() - last_input > 50) {
        send_binary_packet(udp, remote_ip, 9999, input_packet, sizeof(InputPacket));
        serialf("[debug] sending input packet...\n");
        last_input = millis();
        }
      }
      break;
  }
}

