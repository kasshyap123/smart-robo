// Recovered from preserved Arduino preprocessor output; see firmware/README.md.
// First bench test: classic ESP32 board connected to USB only.
// No motor control, Wi-Fi credentials or external libraries.
#include <Arduino.h>

void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println("ROVER USB CHECK: STARTED");
}

void loop() {
  static unsigned long lastMessage = 0;
  const unsigned long now = millis();
  if (now - lastMessage >= 2000) {
    lastMessage = now;
    Serial.print("ESP32 running; seconds = ");
    Serial.println(now / 1000);
  }
  while (Serial.available()) {
    Serial.write(Serial.read());
  }
}
