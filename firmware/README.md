# ESP32 component source

Target: classic ESP32, Arduino board ESP32 Dev Module. These are separate component
sketches, not integrated rover firmware. Open the `.ino` file matching its folder.
Keep local `.h` files beside that sketch and upload one sketch at a time.

## Included programs

- `USB_Check`: USB heartbeat and serial echo.
- `OLED_Connection_Check`: display I2C acknowledgement check.
- `OLED_Bench`: visible OLED pattern.
- `Sonar_OLED_Bench`: one HC-SR04 distance sensor with OLED output.
- `Mic_Serial_Bench`: INMP441 microphone level sampling over serial.
- `Mic_OLED_Bench` and `Mic_Stereo_Diagnostic`: earlier diagnostic source.
- `Speaker_Right_Bench` and `Speaker_Serial_Bench`: generated beep output.
- `Speaker_Melody_Bench`, `Speaker_Melody_Serial_Bench`, and
  `Speaker_Melody_DMA_Bench`: melody synthesis source.

Audio recordings, embedded speech samples, precompiled binaries, and test-result
records are not included. The speaker programs generate tones from code.

## Setup

Install Arduino IDE and Espressif's ESP32 board package. The source was prepared
for the classic ESP32; select ESP32 Dev Module and your actual USB port.
The original source used Espressif Arduino core 3.3.12 and serial speed 115200.
The package index is:

https://espressif.github.io/arduino-esp32/package_esp32_index.json

For each component, follow its source comments and the
[current wiring notes](../docs/WIRING.md). Historical diagnostic source can use
different pin assignments; do not treat all sketches as one combined harness.
Use the [power notes](../docs/POWER_AND_MOTORS.md) before connecting motor power.

## Current scope

Individual component programs are included. Motor integration, simultaneous
peripherals, live browser control, speech recognition, and AI answers remain
ongoing work. The generated-tone DAC programs use classic ESP32 GPIO25. Combined
microphone and DMA output still require explicit peripheral allocation and checks.
