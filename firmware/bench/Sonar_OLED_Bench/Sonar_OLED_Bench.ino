// One HC-SR04 and the already verified OLED, powered from ESP32 USB only.
// HC-SR04: VCC=USB 5V/VIN, GND=common GND, TRIG=13, ECHO via divider to 35.
// Echo divider: ECHO--1k--1k--NODE--1k--1k--1k--GND. NODE->GPIO35.
// OLED remains VCC=3V3, GND=GND, SDA=21, SCL=22. Mic is disconnected.
#include <Arduino.h>
#include "BenchDisplay.h"

constexpr uint8_t TRIGGER_PIN = 13;
constexpr uint8_t ECHO_PIN = 35;
constexpr unsigned long ECHO_TIMEOUT_US = 30000;
constexpr unsigned long PING_INTERVAL_MS = 120;
unsigned long lastPing = 0;
unsigned long lastDisplay = 0;
unsigned long lastDisplayRetry = 0;
unsigned long echoDuration = 0;
float distanceCm = 0;
bool distanceValid = false;
const char *sonarStatus = "NOT_MEASURED";

void drawDigit(char value, int x, int y) {
  const uint8_t shapes[] = {0x3F, 0x06, 0x5B, 0x4F, 0x66,
                            0x6D, 0x7D, 0x07, 0x7F, 0x6F};
  if (value == ' ') return;
  if (value == '-') { rectangle(x + 3, y + 13, 12, 3, true); return; }
  if (value < '0' || value > '9') return;
  const uint8_t mask = shapes[value - '0'];
  if (mask & 0x01) rectangle(x + 3, y, 12, 3, true);
  if (mask & 0x02) rectangle(x + 15, y + 3, 3, 10, true);
  if (mask & 0x04) rectangle(x + 15, y + 16, 3, 10, true);
  if (mask & 0x08) rectangle(x + 3, y + 26, 12, 3, true);
  if (mask & 0x10) rectangle(x, y + 16, 3, 10, true);
  if (mask & 0x20) rectangle(x, y + 3, 3, 10, true);
  if (mask & 0x40) rectangle(x + 3, y + 13, 12, 3, true);
}

void drawDistance() {
  memset(frame, 0, sizeof(frame));
  rectangle(0, 0, 128, 64, false);
  char text[8];
  if (distanceValid) snprintf(text, sizeof(text), "%5.1f", double(distanceCm));
  else snprintf(text, sizeof(text), "---.-");
  int x = 7;
  for (size_t i = 0; text[i]; ++i) {
    if (text[i] == '.') { rectangle(x, 42, 3, 3, true); x += 6; }
    else { drawDigit(text[i], x, 16); x += 21; }
  }
  // Small 'cm' unit label, implemented as two 3x5 glyphs.
  const uint8_t unit[2][5] = {{7, 4, 4, 4, 7}, {5, 7, 7, 5, 5}};
  for (int letter = 0; letter < 2; ++letter) {
    for (int y = 0; y < 5; ++y) {
      for (int col = 0; col < 3; ++col) {
        if (unit[letter][y] & (1 << (2 - col))) pixel(104 + letter * 5 + col, 38 + y);
      }
    }
  }
  rectangle(7, 53, 114, 6, false);
  if (distanceValid) {
    const int width = constrain(int(distanceCm / 100.0f * 110), 1, 110);
    rectangle(9, 55, width, 2, true);
  }
}

void measureDistance() {
  distanceValid = false;
  echoDuration = 0;
  if (digitalRead(ECHO_PIN) == HIGH) { sonarStatus = "ECHO_STUCK_HIGH"; return; }
  digitalWrite(TRIGGER_PIN, LOW);
  delayMicroseconds(3);
  digitalWrite(TRIGGER_PIN, HIGH);
  delayMicroseconds(12);
  digitalWrite(TRIGGER_PIN, LOW);
  echoDuration = pulseIn(ECHO_PIN, HIGH, ECHO_TIMEOUT_US);
  if (echoDuration == 0) { sonarStatus = "NO_ECHO"; return; }
  distanceCm = float(echoDuration) / 58.0f;
  if (distanceCm < 2.0f || distanceCm > 400.0f) { sonarStatus = "OUT_OF_RANGE"; return; }
  distanceValid = true;
  sonarStatus = "VALID";
}

void setup() {
  Serial.begin(115200);
  delay(500);
  pinMode(TRIGGER_PIN, OUTPUT);
  digitalWrite(TRIGGER_PIN, LOW);
  pinMode(ECHO_PIN, INPUT); // Divider supplies pull-down; GPIO35 has no internal pull resistor.
  busReady = Wire.begin(SDA_PIN, SCL_PIN, 100000);
  Wire.setTimeOut(50);
  Serial.println("ROVER SONAR BENCH: TRIG=13 ECHO=35 through 2k/3k divider; one sensor only.");
  lastDisplayRetry = millis() - 3000;
  lastPing = millis() - PING_INTERVAL_MS;
}

void loop() {
  const unsigned long now = millis();
  if (now - lastPing >= PING_INTERVAL_MS) {
    lastPing = now;
    measureDistance();
    if (distanceValid) Serial.printf("SONAR status=VALID echo_us=%lu distance_cm=%.1f\n", echoDuration, double(distanceCm));
    else Serial.printf("SONAR status=%s echo_us=%lu distance_cm=UNAVAILABLE\n", sonarStatus, echoDuration);
  }
  if (busReady && !displayReady && now - lastDisplayRetry >= 3000) {
    lastDisplayRetry = now;
    displayReady = beginDisplay();
    if (displayReady) {
      drawDistance();
      displayReady = showFrame();
      const uint8_t on[] = {0xAF};
      if (displayReady) displayReady = commands(on, sizeof(on));
    }
  }
  if (displayReady && now - lastDisplay >= 250) {
    lastDisplay = now;
    drawDistance();
    if (!showFrame()) {
      displayReady = false;
      lastDisplayRetry = now;
      Serial.println("OLED transfer failed; unplug USB before adjusting wires.");
    }
  }
  delay(1);
}
