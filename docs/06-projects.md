# Community projects

Things to build on instead of starting from scratch. All run HUB75 on ESP32, most on the
same DMA library.

## Turnkey firmware

### hub75-studio
[pavlov-net/hub75-studio](https://github.com/pavlov-net/hub75-studio) · MIT · 24 stars ·
latest release v0.7.1, 2026-04-19

ESPHome plus LVGL. The closest project to this hardware: a Waveshare controller package is
already written, though no prebuilt binary ships for it.

Pages: album art with track info, sports scoreboards via ha-teamtracker, clock and weather,
real-time audio spectrum, presence radar for the MSR-2, countdown timers, QR codes, Pong,
effects (fireworks, fireplace, aurora), GIF and YouTube streaming through media-proxy.

Reusable components you can lift piecemeal: `lvgl-ddp-stream`, `lvgl-canvas-fx`,
`lvgl-page-manager`.

### WLED
[wled/WLED](https://github.com/wled/WLED) · EUPL-1.2

An official build exists for this board. Over two hundred effects, web UI, JSON API, iOS and
Android apps, Home Assistant integration out of the box. Version 16 added Pixel Forge:
on-device image-to-GIF conversion, a scrolling-text builder with time and temperature
substitution, and a Pixel Paint per-pixel editor that previews live on the panel itself.

### Tronbyt
[tronbyt/server](https://github.com/tronbyt/server) · 197 stars

A local replacement for the Tidbyt cloud service after the company was acquired and pull
requests stopped being merged. Apps are written in Starlark via
[pixlet](https://github.com/tronbyt/pixlet), rendered to WebP and pushed to the device.
Community app catalogue at [tronbyt/apps](https://github.com/tronbyt/apps). Home Assistant
integration lives in `tronbyt/TronbytAssistant`.

Supported hardware includes the MatrixPortal S3 and Raspberry Pi with panels. The firmware,
[tronbyt/firmware-esp32](https://github.com/tronbyt/firmware-esp32), uses the `esp-hub75`
library from version 1.5.0 — the same one underneath ESPHome's component and Waveshare's
own BSP.

Operating model: the server renders the image, the device displays it. Without the server
the device does not update.

## Clocks and information panels

### DigiFrame
[manoharc07/DigiFrame](https://github.com/manoharc07/DigiFrame)

Closest to this hardware in intent: 64x64, ESP32-S3 N16R8, a Waveshare P2.5 64x64 panel.
NTP clock, weather via Open-Meteo with no API key, a living ambient scene, looping GIFs,
scrolling messages, themed celebrations on chosen dates.

Four control surfaces: a cloud-hosted static page over Web Bluetooth, an on-device web
dashboard, a Telegram bot, and Home Assistant over MQTT with auto-discovery.

Architecturally interesting for its core split: core 1 owns the panel, the GIF decoder and
the web server; core 0 runs Telegram, weather and MQTT; a shared `control.h` layer holds one
implementation per action so every front end behaves identically, and core-0 tasks marshal
work to core 1 through a command queue rather than touching the panel directly.

A good model to copy if we write our own.

### esp32-morphing-clock
[bogd/esp32-morphing-clock](https://github.com/bogd/esp32-morphing-clock) · GPL-3.0

Morphing-digit clock. Date, time, weekday, outdoor temperature over MQTT, a TSL2591 light
sensor driving automatic brightness, five-day forecast, OTA triggered by an MQTT message,
and a watchdog for automatic recovery. Ships with a shield schematic and laser-cut acrylic
enclosure drawings.

### FamilyClock
[goguelnikov/FamilyClock](https://github.com/goguelnikov/FamilyClock) · GPL-3.0

Family clock on 64x32. Seven screens: clock, weather, next event, day's schedule, moon
phase, notes, birthdays. Fully configurable through a web interface with seven tabs, nine
colour themes, a REST API, and real-time brightness control.

Worth reading for its code structure: separate services for NTP, weather and calendar, one
class per screen, and a screen rotation manager.

### HUB75-Pixel-Art-Display
[mzashh/HUB75-Pixel-Art-Display](https://github.com/mzashh/HUB75-Pixel-Art-Display)

A pixel-art player. GIFs from flash, NTP clock, scrolling text, a web UI with upload and
delete, authentication and remote reboot. Configured by default for exactly a 64x64
1/32-scan panel, i.e. ours.

### matrix-display
[aslak3/matrix-display](https://github.com/aslak3/matrix-display)

A Home Assistant data panel over MQTT with auto-discovery. Interesting for its portability:
one codebase builds for RP2040, RP2350 and ESP32, with board configuration factored into
cmake files. Data is pushed by HA automations rather than pulled by the device, which buys
a lot of flexibility.

## Adjacent ecosystem

Different matrix hardware, but the ideas and protocols transfer.

| Project | Hardware | Why it is interesting |
|---|---|---|
| [AWTRIX 3](https://github.com/Blueforcer/awtrix3) | Ulanzi TC001, 32x8 | the reference design for HA integration over MQTT: apps as topics, JSON payloads, automatic rotation, icons from the LaMetric gallery |
| [PixelIt](https://github.com/pixelit-project/PixelIt) | ESP8266/ESP32, WS2812B | JSON API, a Node-RED node, an ioBroker adapter, HA auto-discovery |
| [Pixelix](https://github.com/BlueAndi/Pixelix) | ESP32, WS2812B and TFT | plugin architecture, REST and MQTT APIs, limited HUB75 support |

The AWTRIX model deserves separate study: each "app" is an MQTT topic like
`awtrix/custom/name` carrying JSON with text, icon and duration. The device cycles through
them by itself, and an empty payload removes an app. Simple, effective, and easy to
reproduce on our own hardware.

## Ideas this hardware unlocks

The peripherals Apollo does not have open up things none of the projects above do:

- **Voice assistant.** Two microphones, ES7210 echo cancellation and a speaker on board.
  The hub75-studio controller package for this board already wires up `micro_wake_word`
  and `voice_assistant`.
- **Motion input.** The QMI8658 IMU gives tilt and shake as a control surface without
  buttons, plus physics effects such as falling sand.
- **Standalone timekeeping.** The PCF85063 RTC with a battery holds time without a network.
- **Local climate.** The SHTC3 reports temperature and humidity right at the panel, no
  external sensors needed.
- **Offline player.** The TF card slot allows GIF playback with no Wi-Fi and no server.
