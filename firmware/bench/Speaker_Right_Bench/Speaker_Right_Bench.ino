// Classic ESP32 only: quiet right-channel PAM8403 bench test.
// GPIO25 -> 0.1uF ceramic series capacitor -> R input (orange).
// Power: USB 5V/VIN -> white +; GND -> yellow - and green input GND.
// Unused L input red -> GND; one speaker between R OUT + and R OUT -.
// Disconnect sonars/mic/motors/batteries. OLED stays 3V3/21/22/GND.
#include <Arduino.h>
#include "BenchDisplay.h"
#if !defined(CONFIG_IDF_TARGET_ESP32)
#error "This wiring requires the classic ESP32 GPIO25 DAC."
#endif
constexpr uint8_t AUDIO_PIN = 25;
constexpr uint8_t BIAS = 128;
constexpr uint8_t AMPLITUDE = 2; // Deliberately quiet: do not raise for USB bench test.
constexpr uint32_t PERIOD_MS = 3000;
uint32_t nextBeep = 0;
bool enabled = true;

void drawSpeaker(bool sounding) {
  memset(frame, 0, sizeof(frame));
  rectangle(0, 0, 128, 64, false);
  rectangle(34, 25, 10, 16, true);
  for (int x = 44; x < 60; ++x) {
    int h = 16 + (x - 44) * 2;
    rectangle(x, 33 - h / 2, 1, h, true);
  }
  if (sounding) {
    rectangle(70, 23, 3, 20, true);
    rectangle(81, 17, 3, 32, true);
    rectangle(92, 11, 3, 44, true);
  }
}

void updateDisplay(bool sounding) {
  if (!displayReady) return;
  drawSpeaker(sounding);
  displayReady = showFrame();
}

void quietBeep() {
  updateDisplay(true);
  Serial.println("AUDIO right-channel quiet beep; GPIO25 DAC 126..130");
  // About 500Hz square wave, 200ms. No I2C/Serial work inside the burst.
  for (unsigned i = 0; i < 100; ++i) {
    dacWrite(AUDIO_PIN, BIAS + AMPLITUDE);
    delayMicroseconds(1000);
    dacWrite(AUDIO_PIN, BIAS - AMPLITUDE);
    delayMicroseconds(1000);
  }
  dacWrite(AUDIO_PIN, BIAS);
  updateDisplay(false);
}

void setup() {
  dacWrite(AUDIO_PIN, BIAS);
  Serial.begin(115200);
  delay(400);
  Serial.println("ROVER QUIET RIGHT SPEAKER TEST: USB only, one speaker, series 0.1uF input capacitor.");
  Serial.println("Short quiet beep every 3 seconds after 8-second startup. x=stop, p=resume.");
  busReady = Wire.begin(SDA_PIN, SCL_PIN, 100000);
  Wire.setTimeOut(50);
  if (busReady) displayReady = beginDisplay();
  if (displayReady) {
    updateDisplay(false);
    const uint8_t on[] = {0xAF};
    if (displayReady) displayReady = commands(on, sizeof(on));
  }
  nextBeep = millis() + 8000;
}

void loop() {
  while (Serial.available()) {
    const char c = Serial.read();
    if (c == 'x' || c == 'X') {
      enabled = false;
      dacWrite(AUDIO_PIN, BIAS);
      Serial.println("AUDIO stopped");
    } else if (c == 'p' || c == 'P') {
      enabled = true;
      nextBeep = millis() + 1000;
      Serial.println("AUDIO resumed");
    }
  }
  if (enabled && int32_t(millis() - nextBeep) >= 0) {
    quietBeep();
    nextBeep = millis() + PERIOD_MS;
  }
  delay(1);
}
