#include <Wire.h>
#include <SPI.h>
#include <TinyScreen.h>
#include <WiFi101.h>
#include <string.h>

#include "utils.h"

#define MAXLEN 0x40
#define WIFITIMEOUT 15000


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

    for (int i = 0; i < num_networks; i++) {
        serialf("[%d] %s (RSSI %d) ENC %d", i, WiFi.SSID(i), WiFi.RSSI(i), WiFi.encryptionType(i));
    }

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

    serialf("connecting to %s...", ssid);
    display.clearScreen();
    display.setCursor(0, 0);
    display.println("da connecterrr...");

    WiFi.disconnect();
    delay(100);
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
        SerialUSB.print("\nyay! ip: ");
        SerialUSB.println(WiFi.localIP());
        display.clearScreen();
        display.setCursor(0, 0);
        display.println("wahoo!");
        return true;
    }
}
