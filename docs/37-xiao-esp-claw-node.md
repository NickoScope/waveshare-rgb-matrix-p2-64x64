# 37. A XIAO ESP32S3 Sense node running ESP-Claw, wired to the panel over UART

A study, 2026-09-24, at the owner's request ("изучи возможности"). Nothing is
built yet. Sources are at the end; anything not checked against them is
marked "not verified".

## What the pieces are

**ESP-Claw** (github.com/espressif/esp-claw; esp-claw.com).
- **Who and what:** Espressif's own "Chat Coding" agent framework for IoT
  devices, inspired by OpenClaw and written in C. Apache-2.0.
- **Maturity:** v0.1.0 was released 2026-06-12, and the repository was active
  on 2026-09-22 (2.2k stars). A young project.
- **How it works:**
  - The thinking is done by cloud LLMs: "OpenAI-style APIs and
    Anthropic-style APIs" (GPT, Qwen, Claude, DeepSeek). An API key lives on
    the node.
  - What works goes into **Lua scripts on the device**, "for reproducible,
    offline operation".
  - It is event driven, with on-chip memory.
  - Chat channels: Telegram, QQ, Feishu, WeChat.
  - MCP client and server.
- **The XIAO ESP32S3 Sense is an official board**
  (`application/edge_agent/boards/seeedstudio/xiao_esp32s3_sense`), with:
  - the OV2640 camera;
  - the PDM microphone on I2S0;
  - microSD over SPI;
  - 8 MB flash and 8 MB octal PSRAM.

  It installs from the browser ("Flash Online").
- **Lua UART module** (`components/lua_modules/lua_driver_uart`):
  - `uart.new(port, tx, rx, baud)`, then `read`, `read_line`, `write` and
    `available`;
  - an RX ring of 1 KiB and blocking writes;
  - port 1 and up (port 0 is the console).

**The XIAO ESP32S3 Sense** (Seeed wiki).
- **Header:** D0-D3 are GPIO1-4, D4/D5 are GPIO5/6 (I2C), D6/D7 are
  GPIO43/44 (UART TX/RX), and D8-D10 are GPIO7-9 (SPI).
- **Taken on the Sense:** D8-D10 and GPIO21 by the SD card, and GPIO39-42
  plus the DVP pins by the camera and the microphone.
- **Free:** D0-D5 and D6/D7. The console is on the USB-C Serial/JTAG, so D6/D7
  are free for a UART.
- **Power:** the 5V pin accepts input "but you must have some sort of diode
  (schottky...) between your external power source and this pin". Current
  draw: Wi-Fi 100 mA, the camera about 120 mA on average and 347 mA at peak
  (OV3660, 640x480, Seeed's figure).

## The idea: the node as the panel's senses and co-processor

The panel is starved of internal memory: every HTTP request costs internal
heap, and the onboard-microphone visualizer hangs it (debt D-A, docs/22). A
node on a wire takes the heavy and unstable work away:

| Job | Today | On the node |
|---|---|---|
| Presence (LD2450) | Home Assistant, about 1 Hz; P4 planned the radar straight on IO45/46 | the radar on the XIAO's D0/D1 at 256 000 baud; targets forwarded at 10 Hz |
| Sound for the visualizer | the panel's own mics, which hang it | the XIAO's mic: FFT bands sent, the panel only draws |
| Camera | none | people count and presence, a snapshot on request (privacy: the owner's call) |
| An AI brain | OpenClaw on nickol over Wi-Fi and the MCP | ESP-Claw on the node, answering in Telegram, running its own Lua rules even offline |

## The wire

| Panel (header U8) | XIAO | Note |
|---|---|---|
| IO45, the panel's RX | D6 = GPIO43, TX of the XIAO's UART1 | idles high; harmless on IO45, whose VDD_SPI strap is fixed by eFuse (docs/11, measured 2026-09-17) |
| IO46, the panel's TX | D7 = GPIO44, RX | driven only after the panel boots; nothing holds IO46 high at reset, so BOOT+reset still enters download mode |
| GND | GND | common ground |
| 5 V from the panel's supply | 5V pin, **through a Schottky diode** | Seeed's own condition; up to about 350 mA with the camera |

**This takes the same two pins as P4** (the LD2450 straight on the panel).
Either one or the other. With the node, the radar moves to the XIAO, and one
cable carries radar, sound and camera events.

**The protocol** is ours to define: a line of JSON per message, both ways.
- Node to panel:
  - `{"t":"presence","targets":[...]}`
  - `{"t":"bands","b":[...]}`
  - `{"t":"event","what":"person"}`
  - `{"t":"cmd","do":"notify","text":"..."}`
- Panel to node: its state.

On the panel it is one new module on UART1 (IO45/46) that feeds the existing
seams: `presence.cpp` Report[], `vizIngest()`, notify, page show. Nothing big
crosses the wire; a Lua upload keeps going over Wi-Fi.

## For and against

**For:**
- It moves the radar, sound and camera off the memory-starved panel.
- A 10 Hz radar.
- It may close D-A (the mics) without touching the panel's memory.
- It works without the router.
- It is an official board of an official Espressif framework, installed from
  a browser.

**Against:**
- ESP-Claw is 0.1.0 and young.
- It is a second AI agent beside OpenClaw on nickol: roles to decide, and a
  second paid LLM key on a device in the room.
- A camera in the living room: privacy.
- Firmware work on the panel: the UART module and the protocol.
- It takes IO45/46 (P4's pins).
- More power from the panel's 5 V.

**Not verified yet:**
- ESP-Claw's real RAM headroom with the camera, the mic, Wi-Fi and a UART at
  once on 8 MB flash;
- whether its Lua can run an FFT fast enough for the visualizer (a C task
  may be needed);
- the latency of its event router.

## Voice: a wake word, then recognition (checked 2026-09-24)

- **ESP-Claw out of the box has no wake word and no speech recognition.** Its
  audio Lua module (`lua_module_audio`) records WAV or AAC, plays audio, and
  has an analyzer (level and spectrum, good for the panel's visualizer
  bands). Nothing named wake, ASR or STT is in its tree.
- **Espressif ESP-SR WakeNet9 runs on the ESP32-S3.** For one microphone,
  the `wakenet` example uses the engine directly.
  - Cost: WakeNet9 takes 16 KB RAM and 324 KB PSRAM, and 3 ms per 32 ms
    frame (2-channel figure). The one-mic AFE (MR, SR, low cost) takes
    60 KB internal and 740 KB PSRAM, at about 19 % of one core.
  - Ready wake words: "Hi, ESP", "Alexa", "Hi, Lexin", and French, Japanese
    and Chinese ones. **No Russian.**
  - A custom wake word is Espressif's paid training (at least 20,000 corpus
    entries) or a TTS-trained route. MultiNet commands are Chinese or English
    only.
- **microWakeWord (ESPHome / Home Assistant)** trains your own wake word from
  Piper TTS clips, 3-4 syllables, into an INT8 TFLite model for the ESP32-S3.
  It is on-device and needs no cloud. The ESPHome `voice_assistant` then
  streams the phrase to Home Assistant's Assist (STT, intent, answer).
  **A Russian wake phrase is possible this way: not verified.**
- **Recognition (speech to text).** None of this does Russian speech on the
  chip. The phrase after the wake word goes out:
  - to Home Assistant Assist (Whisper locally, or a cloud STT);
  - to a whisper on nickol;
  - or to a cloud STT (Yandex SpeechKit and OpenAI both take Russian).

  The recognised text then comes back to the panel (a command, or a
  notification) over the UART or Wi-Fi.
- **One firmware at a time on one XIAO.** ESP-Claw, ESPHome, or our own
  ESP-IDF (WakeNet plus a stream to STT plus the UART link) cannot run
  together.

## Extra GPIO: what the node adds (checked 2026-09-24)

The owner asked: "подключив его по юарт к панели, мы получим с сенса
дополнительно кучу новых gpio?" Yes, but a handful of pins, not a pile, and
they are the node's pins, not the panel's.

| XIAO pin | GPIO | Free on the Sense? | Also can be |
|---|---|---|---|
| D0-D3 | GPIO1-4 | yes; D0/D1 go to the LD2450 if the radar moves to the node | ADC1_CH0-3, TOUCH1-4 |
| D4/D5 | GPIO5/6 | yes; the I2C pair by Seeed's pinout | ADC1_CH4-5, TOUCH5-6 |
| D6/D7 | GPIO43/44 | taken by the UART to the panel | - |
| D8-D10 | GPIO7-9 | taken by the microSD; free if no card is fitted | ADC1_CH6-8, TOUCH7-9 |

- **The count:**
  - 6 pins are free (D0-D5);
  - 4 are left once the radar sits on D0/D1;
  - 3 more are freed if the SD card is dropped.
- **All the free pins are on ADC1**, the one Espressif recommends ("ADC1 is
  recommended for use"). All are also capacitive touch pins.
  - Espressif's advice, not measured by us: a 0.1 µF capacitor on an ADC
    input, and a 470 Ω-2 kΩ series resistor on a touch pad (510 Ω
    preferred).
  - Espressif also warns that the S3 touch sensor "has not passed the
    Conducted Susceptibility (CS) test".
- **The real way to many pins is the I2C pair on D4/D5.** One bus carries
  many sensors and GPIO expanders. The common expanders are PCF8574 (8
  lines) and MCP23017 (16 lines); those line counts are not checked against
  their datasheets.
- **The panel does not get these pins.** It learns about a button or a sensor
  from a message on the UART protocol above, and it sets a relay or an LED
  the same way.
  - The delay is a few milliseconds: a 40-byte line at 115 200 baud (our
    choice, not decided) is 40 x 10 / 115 200 = 3.5 ms on the wire. That
    leaves out the node's processing time.
  - Fine for buttons, relays, LEDs and sensors. Not for fast signals: PWM
    driven from the panel, timing-critical buses, or anything HUB75.

## What ESP-Claw builds for the Sense (checked 2026-09-24)

These are the build defaults: `components/common/app_claw/Kconfig`, plus the
board's `sdkconfig.defaults.board`.
- **Capabilities, all on:**
  - Core: the core, memory, sessions, agents, skills and the LLM inspector.
  - Automation: the event router and its rules, and the scheduler.
  - Lua.
  - MCP: client and server.
  - Chats: Telegram, QQ, Feishu, WeChat, and local IM.
  - Web: HTTP requests to an allowlist, and web search (Tavily or Brave).
  - Files and system.
- **Lua modules on for the Sense:**
  - Drivers: GPIO, ADC, I2C, UART, touch, MCPWM, PCNT, RMT and LEDC.
  - Hardware on the board: camera, vision (motion detect, colour detect), and
    audio. The board file turns on the camera and audio switches.
  - Scripting: the capability bridge, the event publisher, the HTTP server,
    storage, JSON, image, thread, delay, system, board manager and button.
  - Display: LED strip, display and LVGL. The last two are on but have no
    screen on this board.
- **Off by default:**
  - Radios: BLE and BLE HID.
  - Remote and controls: IR and knob.
  - Screens: LCD and LCD touch.
  - Sensors: IMU, magnetometer, environmental sensor and fuel gauge.
  - Other: SCI, and the system UI, which needs an LCD.
  - Also off: ESPDet object detection (it needs a user `.espdl` model).
  - Turning any of these on is a rebuild. The browser flasher's image is
    assumed to match these defaults: **not verified**.
- **Pins: the board README is wrong about D4/D5.** It says the camera's SCCB
  (GPIO39/40) is "shared with header D4/D5". Two sources say otherwise:
  - the Seeed pin table: D4 = GPIO5 (SDA), D5 = GPIO6 (SCL);
  - Espressif's own Arduino `camera_pins.h` for `CAMERA_MODEL_XIAO_ESP32S3`:
    SIOD = 40, SIOC = 39. GPIO39/40 are on the MTCK/MTDO pads, not the
    header.

  So D4/D5 is a bus of its own: `i2c.new(1, 5, 6)` in Lua. Port 1 is our
  choice, because the board already claims I2C0 for the camera. That a
  second bus on port 0 would clash: not verified.

## A pilot, in order

1. Buy a XIAO ESP32S3 Sense. The LD2450 is already being ordered, for P4.
2. Flash ESP-Claw from the browser and try it alone: Telegram, the camera,
   the mic.
3. On the XIAO, a Lua script: read the LD2450 on D0/D1 and send JSON lines on
   D6/D7. On a laptop, check the stream.
4. On the panel, the UART module on IO45/46 feeding presence. Then the sound
   bands.
5. Decide who is the brain: OpenClaw, ESP-Claw, or both with clear roles.

## Sources

- https://github.com/espressif/esp-claw (README; boards/seeedstudio/xiao_esp32s3_sense/*; components/lua_modules/lua_driver_uart/README.md), read 2026-09-24
- https://esp-claw.com/en/, read 2026-09-24
- https://wiki.seeedstudio.com/xiao_esp32s3_getting_started/ (pins, power, current draw), read 2026-09-24
- Voice, all read 2026-09-24:
  - ESP-Claw: https://github.com/espressif/esp-claw (components/lua_modules/lua_module_audio/README.md)
  - ESP-SR:
    - https://docs.espressif.com/projects/esp-sr/en/latest/esp32s3/wake_word_engine/README.html
    - https://docs.espressif.com/projects/esp-sr/en/latest/esp32s3/benchmark/README.html
    - https://github.com/espressif/esp-sr
    - https://github.com/espressif/esp-skainet (the wakenet example)
  - microWakeWord and HA:
    - https://esphome.io/components/micro_wake_word/
    - https://microwakeword.com/train
    - https://www.home-assistant.io/voice_control/create_wake_word/
- ESP-Claw build and pins, read 2026-09-24:
  - https://github.com/espressif/esp-claw: components/common/app_claw/Kconfig;
    boards/seeedstudio/xiao_esp32s3_sense/{README.md, sdkconfig.defaults.board, board_devices.yaml, board_peripherals.yaml};
    components/lua_modules/lua_driver_i2c/README.md
  - https://github.com/espressif/arduino-esp32/blob/master/libraries/ESP32/examples/Camera/CameraWebServer/camera_pins.h (CAMERA_MODEL_XIAO_ESP32S3)
- https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/schematic-checklist.html (ADC and touch sections), read 2026-09-24
- https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/api-reference/peripherals/gpio.html (GPIO summary table), read 2026-09-24
- Our own: docs/11 (IO45/IO46), docs/16 (LD2450), docs/22 (the mics), docs/26 (the MTR-1 direct-link study), docs/36 P4
