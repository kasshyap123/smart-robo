// USB-powered INMP441 microphone level check, with the working OLED retained.
// Mic: VDD=3V3, GND=GND, L/R=GND, SCK=26, WS=27, SD=34.
// OLED remains SDA=21, SCL=22, VCC=3V3, GND=GND.
#include <Arduino.h>
#include <ESP_I2S.h>
#include <math.h>
#include "BenchDisplay.h"

I2SClass microphone;
bool micReady = false;
int32_t samples[256];
double levelDbfs = -120.0;
unsigned long lastStatus = 0;
unsigned long lastOled = 0;
unsigned long lastOledRetry = 0;

void drawLevel(unsigned long now) {
  memset(frame, 0, sizeof(frame));
  rectangle(0, 0, 128, 64, false);
  const bool blink = now % 4000 < 220;
  rectangle(27, blink ? 25 : 16, 20, blink ? 3 : 20, true);
  rectangle(81, blink ? 25 : 16, 20, blink ? 3 : 20, true);
  rectangle(7, 44, 114, 13, false);
  // Relative level, not a calibrated sound-pressure measurement.
  int width = int((levelDbfs + 80.0) * (110.0 / 60.0));
  width = constrain(width, 0, 110);
  if (micReady && width > 0) rectangle(9, 46, width, 9, true);
}

void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println("ROVER MIC BENCH: 3V3 microphone; SCK=26 WS=27 SD=34 L/R=GND.");
  busReady = Wire.begin(SDA_PIN, SCL_PIN, 100000);
  Wire.setTimeOut(50);
  microphone.setPins(26, 27, -1, 34);
  microphone.setTimeout(100);
  micReady = microphone.begin(I2S_MODE_STD, 16000, I2S_DATA_BIT_WIDTH_32BIT,
                              I2S_SLOT_MODE_MONO, I2S_STD_SLOT_LEFT);
  Serial.println(micReady ? "I2S receiver started; this alone does not detect a microphone."
                          : "I2S startup failed; reset and check board selection.");
  lastOledRetry = millis() - 3000;
}

void loop() {
  const unsigned long now = millis();
  size_t count = 0;
  int32_t smallest = 8388607;
  int32_t largest = -8388608;
  double total = 0;
  double squared = 0;
  if (micReady) {
    const size_t bytes = microphone.readBytes(reinterpret_cast<char *>(samples), sizeof(samples));
    count = bytes / sizeof(int32_t);
    for (size_t i = 0; i < count; ++i) {
      // INMP441 signed 24-bit sample is in the high 24 bits of the I2S word.
      const int32_t value = samples[i] >> 8;
      if (value < smallest) smallest = value;
      if (value > largest) largest = value;
      total += value;
      squared += double(value) * value;
    }
    if (count) {
      const double mean = total / count;
      const double variance = fmax(0.0, squared / count - mean * mean);
      const double rms = sqrt(variance);
      levelDbfs = 20.0 * log10(fmax(rms / 8388608.0, 0.000001));
    } else {
      levelDbfs = -120.0;
    }
  }
  if (busReady && !displayReady && now - lastOledRetry >= 3000) {
    lastOledRetry = now;
    displayReady = beginDisplay();
    if (displayReady) {
      drawLevel(now);
      displayReady = showFrame();
      const uint8_t on[] = {0xAF};
      if (displayReady) displayReady = commands(on, sizeof(on));
    }
  }
  if (displayReady && now - lastOled >= 250) {
    lastOled = now;
    drawLevel(now);
    if (!showFrame()) {
      displayReady = false;
      lastOledRetry = now;
      Serial.println("OLED transfer failed; unplug USB before checking connections.");
    }
  }
  if (now - lastStatus >= 500) {
    lastStatus = now;
    Serial.printf("MIC samples=%u level=%.1f dBFS min=%ld max=%ld; listen-test pending\n",
                  unsigned(count), levelDbfs, count ? long(smallest) : 0L,
                  count ? long(largest) : 0L);
    if (!count || smallest == largest) {
      Serial.println("No changing sample values; check soldering, power, SD, clocks and L/R.");
    }
  }
  delay(1);
}
