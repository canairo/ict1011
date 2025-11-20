#ifndef WIFI_HANDLER_H
#define WIFI_HANDLER_H

// Declarations for wifi_handler.cpp

#include <Wire.h>
#include <SPI.h>
#include <TinyScreen.h>
#include <WiFi101.h>
#include <WiFiUdp.h>

bool prompt_and_connect(TinyScreen &display)
void broadcast_packet(WifiUDP &udp)
void join-server(WiFiUDP &udp, IPAddress remote_ip)
bool assert_game_data(char *received_packet)

#endif // WIFI_HANDLER_H
