// Classic 30-pin ESP32 + 128x64 SSD1306 I2C OLED; USB power only.
// Connect by labels: GND->GND, VCC->3V3, SDA->21, SCL->22.
// Uses only the installed ESP32 core. No motors or external power controlled.
#include <Arduino.h>
#include <Wire.h>

constexpr int SDA_PIN = 21;
constexpr int SCL_PIN = 22;
uint8_t oledAddress = 0;
uint8_t frame[128 * 64 / 8] = {};
bool displayReady = false;
bool busReady = false;
unsigned long lastRetry = 0;
unsigned long lastFrame = 0;
unsigned long lastHeartbeat = 0;

bool transfer(uint8_t control, const uint8_t *bytes, size_t count) {
  Wire.beginTransmission(oledAddress);
  Wire.write(control);
  const size_t written = Wire.write(bytes, count);
  const uint8_t status = Wire.endTransmission();
  return written == count && status == 0;
}

bool commands(const uint8_t *bytes, size_t count) {
  return transfer(0x00, bytes, count);
}

bool beginDisplay() {
  // An ACK establishes bus response, not controller identity or working pixels.
  unsigned int found = 0;
  for (uint8_t address : {uint8_t(0x3C), uint8_t(0x3D)}) {
    Wire.beginTransmission(address);
    if (Wire.endTransmission() == 0) {
      oledAddress = address;
      ++found;
      Serial.printf("OLED candidate acknowledged at 0x%02X\n", address);
    }
  }
  if (found != 1) {
    Serial.println(found == 0 ? "No OLED response. Unplug USB before checking wires."
                             : "Two OLED addresses found; connect only one display.");
    return false;
  }
  // SSD1306 128x64, internal charge pump, page addressing, moderate contrast.
  const uint8_t init[] = {0xAE, 0xD5, 0x80, 0xA8, 0x3F, 0xD3, 0x00, 0x40,
                         0x8D, 0x14, 0x20, 0x02, 0xA1, 0xC8, 0xDA, 0x12,
                         0x81, 0x7F, 0xD9, 0xF1, 0xDB, 0x40, 0x2E, 0xA4,
                         0xA6};
  return commands(init, sizeof(init));
}

void pixel(int x, int y) {
  if (x >= 0 && x < 128 && y >= 0 && y < 64) {
    frame[x + (y / 8) * 128] |= uint8_t(1U << (y % 8));
  }
}

void rectangle(int x, int y, int w, int h, bool filled) {
  for (int dy = 0; dy < h; ++dy) {
    for (int dx = 0; dx < w; ++dx) {
      if (filled || dx == 0 || dx == w - 1 || dy == 0 || dy == h - 1) {
        pixel(x + dx, y + dy);
      }
    }
  }
}

bool showFrame() {
  for (uint8_t page = 0; page < 8; ++page) {
    const uint8_t position[] = {uint8_t(0xB0 + page), 0x00, 0x10};
    if (!commands(position, sizeof(position))) return false;
    for (int column = 0; column < 128; column += 16) {
      if (!transfer(0x40, frame + page * 128 + column, 16)) return false;
    }
  }
  return true;
}

void drawEyes(unsigned long now) {
  memset(frame, 0, sizeof(frame));
  rectangle(0, 0, 128, 64, false);
  const bool blink = now % 4000 < 220;
  const int height = blink ? 3 : 20;
  const int y = blink ? 28 : 20;
  rectangle(25, y, 22, height, true);
  rectangle(81, y, 22, height, true);
  const int position = (now / 100) % 102;
  rectangle(8 + position, 53, 10, 3, true);
}

void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println("ROVER OLED BENCH: USB only; GND/GND VCC/3V3 SDA/21 SCL/22.");
  busReady = Wire.begin(SDA_PIN, SCL_PIN, 100000);
  Wire.setTimeOut(50);
  if (!busReady) Serial.println("I2C startup failed; reset ESP32 and check the board selection.");
  lastRetry = millis() - 3000;
}

void loop() {
  const unsigned long now = millis();
  if (busReady && !displayReady && now - lastRetry >= 3000) {
    lastRetry = now;
    displayReady = beginDisplay();
    if (displayReady) {
      drawEyes(now);
      displayReady = showFrame();
      const uint8_t on[] = {0xAF};
      if (displayReady) displayReady = commands(on, sizeof(on));
      if (displayReady) Serial.println("Pixel data sent. Visually confirm border, eyes and moving bar.");
    }
  }
  if (displayReady && now - lastFrame >= 150) {
    lastFrame = now;
    drawEyes(now);
    if (!showFrame()) {
      displayReady = false;
      lastRetry = now;
      Serial.println("Display write failed. Unplug USB before adjusting connections.");
    }
  }
  if (now - lastHeartbeat >= 3000) {
    lastHeartbeat = now;
    Serial.printf("ESP32 running: %lu seconds; OLED data transfer: %s\n", now / 1000,
                  displayReady ? "OK (visual check still required)" : "not ready");
  }
  delay(5);
}
