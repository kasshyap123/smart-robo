# Smart Robo

**An ESP32-based four-wheeled companion rover, currently in development.**

Smart Robo combines a custom enclosure, distance sensors, an OLED display,
a microphone, speakers, and a companion website. The goal is a rover that can
move, detect nearby obstacles, display expressions, and eventually answer spoken
questions. Full hardware integration and AI conversation are ongoing work.

## My role

This is a team project at RV University. **Tejas L Kasshyap is the primary technical
contributor**, working across hardware development, wiring and component testing,
enclosure CAD, and the companion website.

## What is included

- **ESP32 source:** separate Arduino sketches for display output, distance sensing,
  microphone input, and generated speaker tones/melodies.
- **Mechanical CAD:** editable STEP files, STL reference parts, and CAD build scripts.
- **Website:** an interactive 3D robot explorer and a simulated control panel.
- **Setup documentation:** components, wiring, mechanical assembly, and power notes.

The firmware consists of individual component programs. Integrated driving,
automatic obstacle avoidance, speech recognition, and AI question answering are
still being developed. The website controls run locally in the browser: sensor
readings are sample data and conversation responses are scripted previews.

## Hardware

- Classic ESP32 controller and acrylic four-wheel chassis
- Two fixed HC-SR04 ultrasonic distance sensors
- OLED display and INMP441 I2S microphone
- PAM8403 amplifier and two speakers
- L298N motor driver and custom printed enclosure components

## Explore the project

| Folder | Contents |
| --- | --- |
| [firmware](firmware/README.md) | Component source sketches and setup instructions |
| [cad](cad/README.md) | Rev I CAD and current STL reference parts |
| [website](website/README.md) | 3D explorer, simulated controls, and website CAD source |
| [hardware](hardware/) | Component inventory and bench/provisional wiring maps |
| [docs](docs/) | Wiring, mechanical, power, and repository guides |
| [tools](tools/) | Serial capture utility source |

[Components](docs/BOM.md) · [Wiring](docs/WIRING.md) ·
[Power design](docs/POWER_AND_MOTORS.md) ·
[Mechanical assembly](docs/MECHANICAL_AND_PRINTING.md)

## Run the website locally

From the `website` directory:

```sh
python3 -m http.server 4173 --bind 127.0.0.1
```

Open **http://127.0.0.1:4173** in a browser. Local vendor files are included;
no AI account or service credentials are required. The physical rover is not
connected by this preview.

## Check the website

```sh
cd website
node scripts/build.mjs
node scripts/check.mjs
```

These checks validate source CAD hashes, model buffers, required assets, and
JavaScript syntax. GitHub Actions runs the same website checks on changes.
They do not flash firmware or exercise physical hardware.

## Project milestones

- Complete motor, power-system, and mechanical assembly checks.
- Combine peripherals in integrated ESP32 firmware.
- Connect live control with stop and connection-loss handling.
- Integrate speech recognition and spoken AI responses.

## Credits and licensing

Team project, with primary technical development by Tejas L Kasshyap.
Third-party libraries retain their existing notices. No blanket open-source
license has been selected for original materials; see
[licensing status](LICENSE_STATUS.md).

This public repository contains source, CAD, website assets, and setup guides.
Audio recordings/samples, embedded recitation audio, prebuilt firmware binaries,
test logs, validation-result files, and historical test records are excluded.
