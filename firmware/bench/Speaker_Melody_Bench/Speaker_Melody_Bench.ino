// Classic ESP32 GPIO25 -> series 104 capacitor -> BOTH PAM8403 audio inputs.
// Quiet public-domain melody; each speaker has its OWN amplifier output pair.
// No batteries, motors, mic or sonar. OLED stays on GPIO21/22 and 3V3.
#include <Arduino.h>
#include <math.h>
#include "BenchDisplay.h"
#if !defined(CONFIG_IDF_TARGET_ESP32)
#error "Use the classic ESP32 GPIO25 DAC board for this wiring."
#endif

constexpr uint8_t AUDIO_PIN = 25;
constexpr uint8_t DAC_BIAS = 128;
constexpr float AMPLITUDE = 2.0f; // Same peak DAC level as the passed quiet beep.
constexpr uint32_t SAMPLE_RATE = 8000;
constexpr uint32_t SAMPLE_US = 1000000 / SAMPLE_RATE;
constexpr uint32_t BEAT_MS = 280;
constexpr float TAU = 6.28318530718f;
struct Note { float hz; uint8_t beats; };
constexpr float C = 523.251f, D = 587.330f, E = 659.255f;
constexpr float F = 698.456f, G = 783.991f, A = 880.000f;
// Traditional public-domain tune: Twinkle, Twinkle, Little Star.
const Note melody[] = {
  {C,1},{C,1},{G,1},{G,1},{A,1},{A,1},{G,2},
  {F,1},{F,1},{E,1},{E,1},{D,1},{D,1},{C,2},
  {G,1},{G,1},{F,1},{F,1},{E,1},{E,1},{D,2},
  {G,1},{G,1},{F,1},{F,1},{E,1},{E,1},{D,2},
  {C,1},{C,1},{G,1},{G,1},{A,1},{A,1},{G,2},
  {F,1},{F,1},{E,1},{E,1},{D,1},{D,1},{C,2}
};
bool playing = false;
bool queued = true;
uint32_t playAt = 0;

void drawProgress(size_t completed, bool active) {
  if (!displayReady) return;
  memset(frame, 0, sizeof(frame));
  rectangle(0, 0, 128, 64, false);
  // Two note stems and note heads; lower bar progresses through the melody.
  rectangle(43, 12, 3, 28, true);
  rectangle(67, 9, 3, 28, true);
  rectangle(43, 9, 27, 4, true);
  rectangle(34, 35, 12, 7, true);
  rectangle(58, 32, 12, 7, true);
  if (active) rectangle(89, 18, 3, 22, true);
  rectangle(7, 52, 114, 7, false);
  const size_t count = sizeof(melody) / sizeof(melody[0]);
  if (completed) rectangle(9, 54, int(completed * 110 / count), 3, true);
  displayReady = showFrame();
}

bool checkStop() {
  while (Serial.available()) {
    char ch = Serial.read();
    if (ch == 'x' || ch == 'X') {
      playing = false;
      queued = false;
      dacWrite(AUDIO_PIN, DAC_BIAS);
      Serial.println("MELODY stopped");
      return true;
    }
  }
  return false;
}

bool playNote(const Note &note) {
  const uint32_t totalMs = note.beats * BEAT_MS;
  const uint32_t soundMs = totalMs - 25;
  const uint32_t count = soundMs * SAMPLE_RATE / 1000;
  const uint32_t ramp = SAMPLE_RATE * 8 / 1000;
  float phase = 0;
  const float step = TAU * note.hz / SAMPLE_RATE;
  uint32_t deadline = micros();
  for (uint32_t i = 0; i < count; ++i) {
    while (int32_t(micros() - deadline) < 0) {}
    float envelope = 1.0f;
    if (i < ramp) envelope = float(i) / ramp;
    else if (count - 1 - i < ramp) envelope = float(count - 1 - i) / ramp;
    const int offset = int(lroundf(AMPLITUDE * envelope * sinf(phase)));
    dacWrite(AUDIO_PIN, uint8_t(DAC_BIAS + offset));
    phase += step;
    if (phase >= TAU) phase -= TAU;
    deadline += SAMPLE_US;
    if ((i & 127U) == 0 && checkStop()) return false;
    // Avoid a catch-up burst if another system task stalls the output.
    if (int32_t(micros() - deadline) > int32_t(4 * SAMPLE_US)) deadline = micros();
  }
  dacWrite(AUDIO_PIN, DAC_BIAS);
  delay(25);
  return !checkStop();
}

void playMelody() {
  playing = true;
  const size_t count = sizeof(melody) / sizeof(melody[0]);
  Serial.println("MELODY start: Twinkle Twinkle Little Star; DAC25 peak offset 2, both amplifier inputs share signal");
  for (size_t i = 0; i < count && playing; ++i) {
    drawProgress(i, true);
    Serial.printf("MELODY note=%u/%u hz=%.2f beats=%u\n", unsigned(i+1), unsigned(count), double(melody[i].hz), melody[i].beats);
    if (!playNote(melody[i])) break;
    delay(1);
  }
  const bool finished = playing;
  playing = false;
  dacWrite(AUDIO_PIN, DAC_BIAS);
  drawProgress(finished ? count : 0, false);
  if (finished) Serial.println("MELODY complete; silent until p or board reset");
}

void setup() {
  dacWrite(AUDIO_PIN, DAC_BIAS);
  Serial.begin(115200);
  delay(400);
  Serial.println("ROVER QUIET MELODY: starts once after 8 seconds. p=replay, x=stop.");
  busReady = Wire.begin(SDA_PIN, SCL_PIN, 100000);
  Wire.setTimeOut(50);
  if (busReady) displayReady = beginDisplay();
  if (displayReady) {
    drawProgress(0, false);
    const uint8_t on[] = {0xAF};
    if (displayReady) displayReady = commands(on, sizeof(on));
  }
  playAt = millis() + 8000;
}

void loop() {
  while (Serial.available()) {
    char ch = Serial.read();
    if (ch == 'p' || ch == 'P') { queued = true; playAt = millis() + 1000; }
    else if (ch == 'x' || ch == 'X') {
      queued = false;
      dacWrite(AUDIO_PIN, DAC_BIAS);
      Serial.println("MELODY stopped");
    }
  }
  if (queued && int32_t(millis() - playAt) >= 0) {
    queued = false;
    playMelody();
  }
  delay(1);
}
