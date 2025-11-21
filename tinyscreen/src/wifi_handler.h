#ifndef WIFI_HANDLER_H
#define WIFI_HANDLER_H

// Declarations for wifi_handler.cpp

#include <Wire.h>
#include <SPI.h>
#include <TinyScreen.h>
#include <WiFi101.h>
#include <WiFiUdp.h>

bool prompt_and_connect(TinyScreen &display);
void broadcast_packet(WiFiUDP &udp);
void join_server(WiFiUDP &udp, IPAddress remote_ip);
bool assert_game_data(char *received_packet);
void send_packet(WiFiUDP &udp, IPAddress addr, int port, char* packet);
IPAddress receive_discover(WiFiUDP &udp, char* received_packet);

#endif // WIFI_HANDLER_H
