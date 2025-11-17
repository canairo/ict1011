#include <Wire.h>
#include <SPI.h>
#include <TinyScreen.h>
#include <WiFi101.h>
#include <string.h>

#include "wifi_handler.h"

TinyScreen display = TinyScreen(TinyScreenPlus);

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
    if (WiFi.status() != WL_CONNECTED) {
        prompt_and_connect(display);
    } else {
        display.clearScreen();
        display.setCursor(0, 0);
        display.println("connected!");
        delay(5000);
    }
}

