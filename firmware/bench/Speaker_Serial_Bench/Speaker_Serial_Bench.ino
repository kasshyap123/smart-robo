// Classic ESP32 USB bench test: low-volume DAC25 beeps, no OLED or microphone.
// GPIO25 -> series 104 ceramic capacitor -> ONE selected amplifier input.
// Ground the other audio input. Each speaker stays on its own OUT+/OUT- pair.
#include <Arduino.h>
#if !defined(CONFIG_IDF_TARGET_ESP32)
#error "This bench wiring requires classic ESP32 GPIO25 DAC."
#endif
constexpr uint8_t AUDIO_PIN = 25;
constexpr uint8_t BIAS = 128;
constexpr uint8_t AMPLITUDE = 2;
uint32_t nextBeep = 0;
bool enabled = true;

void quietBeep() {
  Serial.println("BEEP: DAC25 500Hz, 200ms, codes126..130; audible channel depends on wiring.");
  for (unsigned i = 0; i < 100; ++i) {
    dacWrite(AUDIO_PIN, BIAS + AMPLITUDE);
    delayMicroseconds(1000);
    dacWrite(AUDIO_PIN, BIAS - AMPLITUDE);
    delayMicroseconds(1000);
  }
  dacWrite(AUDIO_PIN, BIAS);
}

void setup() {
  dacWrite(AUDIO_PIN, BIAS);
  Serial.begin(115200);
  delay(400);
  Serial.println("QUIET SPEAKER SERIAL BENCH: USB power; no OLED/mic/motors/batteries.");
  Serial.println("DAC25 -> series104 -> chosen L or R input; other input -> GND.");
  Serial.println("First beep after 8 seconds, then a short beep about every 3 seconds. x=stop, p=resume.");
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
    nextBeep = millis() + 3000;
  }
  delay(1);
}
