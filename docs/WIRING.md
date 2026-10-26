# Wiring — separate bench setups from the proposed final harness

Use GPIO labels, not physical header positions or wire colours. Unplug USB and
other power before changing wiring. Grounds shared by logic devices must be
connected, while speaker output terminals are not grounds.

## OLED bench

| OLED | ESP32 |
|---|---|
| VCC | 3V3 |
| GND | GND |
| SDA | GPIO21 |
| SCL | GPIO22 |

## Repaired INMP441 bench

| Microphone | ESP32 |
|---|---|
| VDD / VCC | 3V3 |
| GND | GND |
| SCK / BCLK | GPIO26 |
| WS / LRCLK | GPIO27 |
| SD | GPIO34 |
| L/R | GND (left channel) |

Use Mic_Serial_Bench with OLED disconnected for the last verified setup. Nonzero
samples alone are not a microphone acoustic pass; the owner also correlated speech
and quiet with changing levels. dBFS is relative digital level, not calibrated SPL.

## One HC-SR04 bench — repeat separately for each sensor

VCC -> USB-powered ESP32 5V/VIN, GND -> common GND, TRIG -> GPIO13.
ECHO -> two 1k resistors in series -> junction -> three 1k resistors in series -> GND.
GPIO35 connects to the junction. The nominal divided high is 3.0 V from a 5 V Echo.
Do not connect Echo directly to the ESP32. Use a separate divider for each sensor.
Use Sonar_OLED_Bench and leave the OLED at 21/22. GPIO13 here is a bench choice;
it is reserved for a buzzer in the different provisional final map.

## Quiet PAM8403 two-input bench

| Connection | Destination |
|---|---|
| PAM supply + | USB-powered ESP32 5V/VIN, brief low-level test only |
| PAM supply - | Common ESP32 GND |
| PAM middle input GND | Common ESP32 GND |
| GPIO25 | Series 104 / 0.1 uF nonpolar ceramic capacitor |
| Other capacitor end | Shared L and R **audio-input** node |
| Left speaker | L OUT+ and L OUT- only |
| Right speaker | R OUT+ and R OUT- only |
| 100 uF supply capacitor + | PAM supply + |
| 100 uF striped negative | PAM supply - |

Never join the output channels, join their negative speaker terminals, or connect
an output to GND/GPIO. A shared mono input is different from paralleled outputs.
The internal DAC tests deliberately use a tiny signal: original bias 128 +/-2,
DMA tests bias 128 +/-4 codes. Do not run full-amplitude unrelated audio with this
bench power arrangement. Final amplifier supply, coupling/attenuation and noise
performance still require a separate design/test.

During the noise-isolation test only the ESP32 end of the GPIO25 audio-feed wire
was moved to GND, leaving the series capacitor and L/R input node in place.
The repeating burp stopped, while some disturbance remained. Restore that feed
to GPIO25 with USB unplugged before evaluating normal playback. This does not
prove a defective DAC, speaker, solder joint or copper material.

## Motor wiring started

One motor's two wires go to OUT1 and OUT2. Either ordering is acceptable for a
first direction test; reversing the wires reverses rotation. This does not
specify power/input jumpers or authorize connecting the battery yet. See the
[power and motor plan](POWER_AND_MOTORS.md).

## Proposed integrated map — not the bench map

See [hardware/provisional_pin_map.csv](../hardware/provisional_pin_map.csv).
This is a design proposal, not uploaded integrated firmware. In particular:
bench sonar TRIG13 conflicts with proposed buzzer13; final sonar triggers move to
4 and 23. DMA internal DAC uses I2S0 on classic ESP32; simultaneous microphone
input must be allocated to I2S1 and tested. Do not combine sketches unchanged.
