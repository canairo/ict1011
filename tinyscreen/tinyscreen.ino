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
    display.clearScreen();
    display.setCursor(0,0);
    if (WiFi.status() != WL_CONNECTED) {
        prompt_and_connect(display);
    } else if (remote_ip == IPAddress(69, 69, 69, 69)) {
        find_server(remote_ip);
    }
    delay(5000);
    display.println("rawr");
}

