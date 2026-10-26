// Classic ESP32, USB-only INMP441 test. No OLED or audio output.
// VDD=3V3, GND=GND, L/R=GND, SCK=26, WS=27, SD=34.
#include <Arduino.h>
#include <ESP_I2S.h>
#include <math.h>

I2SClass microphone;
int32_t words[1024];
bool ready = false;
uint32_t previousReport = 0;

struct ChannelStats {
  size_t count = 0;
  double sum = 0;
  double squares = 0;
  int32_t minimum = 8388607;
  int32_t maximum = -8388608;
  void add(int32_t value) {
    ++count;
    sum += value;
    squares += double(value) * value;
    if (value < minimum) minimum = value;
    if (value > maximum) maximum = value;
  }
  double dbfs() const {
    if (!count) return -120.0;
    const double mean = sum / count;
    const double rms = sqrt(fmax(0.0, squares / count - mean * mean));
    return 20.0 * log10(fmax(rms / 8388608.0, 0.000001));
  }
};
ChannelStats leftStats, rightStats;

void setup() {
  Serial.begin(115200);
  delay(600);
  Serial.println("MIC SERIAL ONLY: VDD=3V3 GND=GND LR=GND SCK=26 WS=27 SD=34");
  microphone.setPins(26, 27, -1, 34);
  microphone.setTimeout(100);
  ready = microphone.begin(I2S_MODE_STD, 16000, I2S_DATA_BIT_WIDTH_32BIT,
                           I2S_SLOT_MODE_STEREO, I2S_STD_SLOT_BOTH);
  Serial.println(ready ? "I2S_STARTED: receiver initialized; this is not microphone detection."
                       : "I2S_START_FAILED");
  Serial.println("Keep quiet, speak near the mic, then quiet again. Levels are relative, not calibrated loudness.");
  previousReport = millis();
}

void loop() {
  if (ready) {
    const size_t bytes = microphone.readBytes(reinterpret_cast<char *>(words), sizeof(words));
    const size_t count = bytes / sizeof(int32_t);
    for (size_t i = 0; i + 1 < count; i += 2) {
      leftStats.add(words[i] >> 8);
      rightStats.add(words[i + 1] >> 8);
    }
  }
  const uint32_t now = millis();
  if (now - previousReport >= 500) {
    previousReport = now;
    Serial.printf("MIC t=%lu Lframes=%u LdB=%.1f Lmin=%ld Lmax=%ld Rframes=%u RdB=%.1f Rmin=%ld Rmax=%ld\n",
                  (unsigned long)now, (unsigned)leftStats.count, leftStats.dbfs(),
                  leftStats.count ? (long)leftStats.minimum : 0L,
                  leftStats.count ? (long)leftStats.maximum : 0L,
                  (unsigned)rightStats.count, rightStats.dbfs(),
                  rightStats.count ? (long)rightStats.minimum : 0L,
                  rightStats.count ? (long)rightStats.maximum : 0L);
    leftStats = ChannelStats{};
    rightStats = ChannelStats{};
  }
  delay(1);
}
