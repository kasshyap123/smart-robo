// Recovered from preserved Arduino preprocessor output; see firmware/README.md.
// USB-powered ESP32 plus OLED only. Connect by printed pin labels:
// OLED GND -> GND, VCC -> 3V3, SDA -> GPIO21, SCL -> GPIO22.
// This detects I2C acknowledgements; it does not test the OLED pixels.
#include <Arduino.h>
#include <Wire.h>
void setup() {
  Serial.begin(115200);
  delay(500);
  Wire.begin(21, 22, 100000);
  Wire.setTimeOut(50);
  Serial.println("OLED CONNECTION CHECK: SDA=21 SCL=22; OLED power=3V3");
}
void loop() {
  unsigned int count = 0;
  for (uint8_t address = 1; address < 127; ++address) {
    Wire.beginTransmission(address);
    uint8_t result = Wire.endTransmission();
    if (result == 0) {
      ++count;
      Serial.printf("I2C device acknowledged at 0x%02X%s\n", address,
        (address == 0x3C || address == 0x3D) ? " (common OLED address)" : "");
    }
  }
  if (count == 0) Serial.println("No I2C device detected; check labelled connections with USB unplugged.");
  Serial.println("Scan complete.");
  delay(3000);
}
