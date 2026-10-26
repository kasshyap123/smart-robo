// Classic ESP32 USB bench: GPIO25 -> series104 -> both PAM8403 inputs.
// Hardware-timed DAC output; no OLED, microphone, motors, or battery power.
#include <Arduino.h>
#include <math.h>
#include <string.h>
#include "driver/dac_continuous.h"
#include "esp_err.h"
#if !defined(CONFIG_IDF_TARGET_ESP32)
#error "Use classic ESP32 GPIO25 for this bench wiring."
#endif
#if !CONFIG_DAC_DMA_AUTO_16BIT_ALIGN
#error "This sketch needs automatic 8-bit DAC buffer alignment."
#endif

constexpr uint32_t SAMPLE_RATE = 32000;
constexpr uint32_t BEAT_MS = 280;
constexpr uint8_t BIAS = 128;
constexpr float AMPLITUDE = 4.0f; // Modest +6dB versus the original peak-offset2 test.
constexpr float TAU = 6.28318530718f;
struct Note { float hz; uint8_t beats; };
constexpr float C = 523.251f, D = 587.330f, E = 659.255f;
constexpr float F = 698.456f, G = 783.991f, A = 880.000f;
const Note melody[] = {
  {C,1},{C,1},{G,1},{G,1},{A,1},{A,1},{G,2},
  {F,1},{F,1},{E,1},{E,1},{D,1},{D,1},{C,2},
  {G,1},{G,1},{F,1},{F,1},{E,1},{E,1},{D,2},
  {G,1},{G,1},{F,1},{F,1},{E,1},{E,1},{D,2},
  {C,1},{C,1},{G,1},{G,1},{A,1},{A,1},{G,2},
  {F,1},{F,1},{E,1},{E,1},{D,1},{D,1},{C,2}
};
constexpr size_t MAX_NOTE_SAMPLES = SAMPLE_RATE * BEAT_MS * 2 / 1000;
uint8_t noteBuffer[MAX_NOTE_SAMPLES];
uint8_t quietBuffer[512];
dac_continuous_handle_t dac = nullptr;
bool ready = false, queued = true, playing = false, stopped = false;
uint32_t playAt = 0;

bool writeSamples(uint8_t *data, size_t count) {
  size_t written = 0;
  const esp_err_t error = dac_continuous_write(dac, data, count, &written, 1500);
  if (error != ESP_OK || written != count) {
    Serial.printf("DAC_WRITE_FAILED error=%s loaded=%u expected=%u\n",
                  esp_err_to_name(error), unsigned(written), unsigned(count));
    ready = false;
    queued = false;
    playing = false;
    return false;
  }
  return true;
}

void readCommands() {
  while (Serial.available()) {
    const char c = Serial.read();
    if (c == 'x' || c == 'X') {
      stopped = true;
      playing = false;
      queued = false;
      Serial.println("MELODY stopped; queued samples drain to steady bias");
    } else if ((c == 'p' || c == 'P') && !playing) {
      stopped = false;
      queued = true;
      playAt = millis() + 1000;
    }
  }
}

void playMelody() {
  playing = true;
  stopped = false;
  const size_t noteCount = sizeof(melody) / sizeof(melody[0]);
  Serial.println("DMA_MELODY start: Twinkle Twinkle Little Star; GPIO25; 32kHz; peakoffset4");
  for (size_t n = 0; n < noteCount && ready && playing; ++n) {
    const uint32_t totalMs = uint32_t(melody[n].beats) * BEAT_MS;
    const size_t total = SAMPLE_RATE * totalMs / 1000;
    const size_t sound = SAMPLE_RATE * (totalMs - 25) / 1000;
    const size_t ramp = SAMPLE_RATE * 12 / 1000;
    float phase = 0.0f;
    const float step = TAU * melody[n].hz / SAMPLE_RATE;
    for (size_t i = 0; i < total; ++i) {
      int value = BIAS;
      if (i < sound) {
        float envelope = 1.0f;
        if (i < ramp) envelope = float(i) / ramp;
        else if (sound - 1 - i < ramp) envelope = float(sound - 1 - i) / ramp;
        value += int(lroundf(AMPLITUDE * envelope * sinf(phase)));
        phase += step;
        if (phase >= TAU) phase -= TAU;
      }
      noteBuffer[i] = uint8_t(value);
    }
    Serial.printf("DMA_MELODY note=%u/%u hz=%.2f\n", unsigned(n+1), unsigned(noteCount), double(melody[n].hz));
    if (!writeSamples(noteBuffer, total)) break;
    readCommands();
  }
  const bool completed = ready && playing && !stopped;
  playing = false;
  if (completed) Serial.println("DMA_MELODY complete; constant-bias samples continue during silence");
}

void setup() {
  Serial.begin(115200);
  delay(400);
  memset(quietBuffer, BIAS, sizeof(quietBuffer));
  dac_continuous_config_t config = {};
  config.chan_mask = DAC_CHANNEL_MASK_CH0;
  config.desc_num = 8;
  config.buf_size = 1024;
  config.freq_hz = SAMPLE_RATE;
  config.offset = 0;
  config.clk_src = DAC_DIGI_CLK_SRC_DEFAULT;
  config.chan_mode = DAC_CHANNEL_MODE_SIMUL;
  esp_err_t error = dac_continuous_new_channels(&config, &dac);
  if (error == ESP_OK) error = dac_continuous_enable(dac);
  if (error != ESP_OK) {
    Serial.printf("DAC_INIT_FAILED %s\n", esp_err_to_name(error));
    return;
  }
  ready = true;
  Serial.println("DMA_AUDIO_STARTED GPIO25 32000Hz codes124..132; no OLED/microphone");
  Serial.println("One melody after 8 seconds; p=replay x=stop; slightly louder than original test.");
  playAt = millis() + 8000;
}

void loop() {
  readCommands();
  if (!ready) { delay(100); return; }
  if (queued && int32_t(millis() - playAt) >= 0) {
    queued = false;
    playMelody();
  }
  if (ready) writeSamples(quietBuffer, sizeof(quietBuffer));
}
