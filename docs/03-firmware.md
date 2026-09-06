# Firmware: what to choose and how to install

Four paths. The first two need no compiler to get started.

| Path | Difficulty | What you get | Prebuilt binary |
|---|---|---|---|
| **WLED 16.0.1** | low | 200+ effects, web UI, JSON API, Home Assistant integration | **yes** |
| **ESPHome / hub75-studio** | medium | native HA entities, LVGL pages, YAML you control | **no**, build it yourself |
| **ESP-IDF** | high | full control, vendor examples, BSP | sources |
| **Arduino** | medium | fast prototyping, huge ecosystem | sources |

## Path 1: WLED — the recommended start

The board is officially supported upstream. Support landed in WLED 16.0.1, contributed by
netmindz; the pinout is selected at build time by the `WAVESHARE_S3_PINOUT` define.

**File:** `WLED_16.0.1_ESP32-S3_Waveshare_HUB75.bin` from the
[WLED v16.0.1 release](https://github.com/wled/WLED/releases/tag/v16.0.1).

WLED's own documentation describes the board as: octal PSRAM, a dedicated HUB75 driver
board with an onboard audio codec (dual mic, audioreactive) and a microSD slot.

Things worth knowing about WLED on HUB75:

- HUB75 pins **cannot be set** in the UI; they are compiled in. That is why separate
  per-board binaries exist.
- After any HUB75 setting change the display **goes black until reboot**. Expected
  behaviour, not a fault.
- For a 128x128 grid of four panels, WLED's documentation explicitly requires an ESP32-S3
  with octal PSRAM. This board has 16 MB octal, so the requirement is met comfortably.
- On ESP32-S3, audioreactive and HUB75 coexist with no known restrictions. On classic
  ESP32 microphones cause crashes; on S2 the two are mutually exclusive.

## Path 2: ESPHome

**Important:** there is no prebuilt binary for this board. The hub75-studio repository root
ships factory configs only for `apollo-automation-m1-rev4`, `apollo-automation-m1-rev6` and
`adafruit-matrix-portal-s3`. A Waveshare controller package exists at
`packages/controllers/waveshare-esp32-s3-rgb-matrix.yaml`, but the top-level configuration
is yours to write.

**2a. Plain ESPHome.** The `hub75` component is built into the core as of ESPHome 2025.12.
There is no board preset for this board, so all fourteen pins are declared by hand. A
minimal working config is in
[configs/esphome/waveshare-matrix.yaml](../configs/esphome/waveshare-matrix.yaml).

**2b. hub75-studio.** Gives you ready-made LVGL pages: clock, weather, album art, sports
scoreboards, audio spectrum, Pong, effects, video streaming over DDP. You write a top-level
YAML that pulls in their controller package. The project requires ESPHome on ESP-IDF;
Arduino is not supported.

Key `hub75` component options:

| Option | Default | Range |
|---|---|---|
| `brightness` | 128 | 0–255 |
| `bit_depth` | 8 | 4–12 |
| `min_refresh_rate` | 60 | 40–200 Hz |
| `clock_speed` | 20MHZ | 8/10/16/20 MHz |
| `latch_blanking` | 1 | positive integer |
| `shift_driver` | GENERIC | GENERIC/FM6124/FM6126A/ICN2038S/MBI5124/DP3246 |
| `scan_wiring` | STANDARD_TWO_SCAN | plus 1/4 and 1/8 variants |
| `gamma_correct` | — | LINEAR / CIE1931 / GAMMA_2_2 |
| `double_buffer` | false | set false with LVGL |
| `update_interval` | 16 ms | set `never` with LVGL |

Multi-panel layouts use `layout_rows`, `layout_cols` and `layout`, the latter taking
HORIZONTAL, TOP_LEFT_DOWN, TOP_RIGHT_DOWN, BOTTOM_LEFT_UP, BOTTOM_RIGHT_UP and their
ZIGZAG variants.

## Path 3: ESP-IDF, vendor examples

Repository: [waveshareteam/ESP32-S3-RGB-Matrix](https://github.com/waveshareteam/ESP32-S3-RGB-Matrix),
Apache 2.0.

| Directory | Contents |
|---|---|
| `example/idf_v5.5.2` | ESP-IDF 5.5.2 project, including the board support package |
| `example/idf_v5.5.2/components/bsp/esp32_s3_matrix` | **the BSP — authoritative pin map in `include/bsp/config.h`** |
| `example/arduino_v3.3.7` | ten Arduino examples |
| `firmware` | prebuilt binaries |
| `hardware/schematics` | board schematic, one-page PDF |
| `hardware/dimensions` | mechanical drawings |

**Notable finding.** Their ESP-IDF example is built on `esphome/esp-hub75` — the very
library that backs the `hub75` component in ESPHome core. The BSP's `idf_component.yml`
declares it as a dependency at version `^0.3.5`. The ESP-IDF path and the ESPHome path
therefore lead to the same driver, and knowledge transfers directly between them.

Full BSP dependency list, useful if you build on it:

| Component | Version |
|---|---|
| `esphome/esp-hub75` | ^0.3.5 |
| `lvgl/lvgl` | ^9.3 |
| `waveshare/qmi8658` | ^1.0.1 |
| `waveshare/pcf85063a` | * |
| `pedrominatel/shtc3` | ^1.4.0 |
| `esp_codec_dev` | ~1.3.1 |
| `espressif/button` | ^4.1.3 |
| `espressif/esp_lvgl_port` | ^2.0.0 |

**Second finding.** Their example's default layout targets **two** panels
(`LAYOUT_ROWS=2`, `COLS=1`, top-left-down zigzag), i.e. 64x128 stacked vertically. On a
single panel, change both to 1.

The repository is young: created 2026-04-23, three stars, one main contributor. Calibrate
your expectations of community support accordingly.

## Path 4: Arduino

The base library is `mrcodetastic/ESP32-HUB75-MatrixPanel-DMA`, listed in the Library
Manager as `ESP32 HUB75 LED MATRIX PANEL DMA Display`. Most projects in
[06-projects.md](06-projects.md) are built on it.

Waveshare requires board package `esp32 by Espressif Systems` version **3.3.7**.

**The board's pleasant quirk.** Waveshare routed HUB75 to this library's default ESP32-S3
pinout, differing in exactly one pin: E on GPIO9, unassigned upstream. Any sketch on this
library therefore runs with no pin setup — one line, `mxconfig.gpio.e = 9;`. Details in
[02-controller.md](02-controller.md).

Vendor examples:

| Example | Panel height declared | Shift driver set | What it does |
|---|---|---|---|
| `01_SimpleTestShapes` | 32 | FM6126A | text, fills, basic sanity check |
| `02_PatternPlasma` | — | commented out | plasma effect, draw-rate counter |
| `03_DoubleBuffer` | 64 | none | double buffering against animation flicker |
| `04_OtherShiftDriverPanel` | 64 | FM6126A | panels with other driver ICs |
| `05_AnimatedGIFPanel_SD` | 32 | FM6126A | GIF playback from the TF card |
| `06_BitmapIcons` | 64 | none | BMP output |
| `07_Pixel_Mapping_Test` | 16 | none | raw HUB75 control logic |
| `08_Sensor_Test` | 64 | FM6126A | SHTC3, QMI8658 over I2C |
| `09_Music_Player` | 64 | FM6126A | ES8311 playback, buttons, TF card |
| `10_Chinese_Font` | 64 | FM6126A | CJK font rendering |

**Watch the panel height.** Several examples declare 64x32 and need adjusting to 64x64.

**Watch the shift driver.** Seven of ten set `FM6126A`, contradicting Waveshare's own user
guide and ESP-IDF configuration, which both indicate `GENERIC`. See contradiction #4 in
[07-sources.md](07-sources.md).

A smoke test is provided in
[configs/arduino/smoke_test](../configs/arduino/smoke_test/smoke_test.ino).

## Alternative libraries

| Library | When to use it |
|---|---|
| `esphome-libs/esp-hub75` | ESP-IDF component underneath ESPHome's component, and the one Waveshare's own BSP depends on. Supports ESP32/S2/S3/C6/P4, CIE 1931 gamma, double buffering, ghosting mitigation via a previous-row-address technique on the LSB bit plane |
| `hzeller/rpi-rgb-led-matrix` | if the panel moves to a Raspberry Pi |
| `bitbank2/AnimatedGIF` | GIF decoder used by every animation project |
| `mrcodetastic/GFX_Lite` | lighter replacement for Adafruit GFX |

## DMA buffer memory

Figures from the `esp-hub75` documentation for a 64x64 panel at 8-bit depth:

| Platform | Usage |
|---|---|
| ESP32-S3 (GDMA), internal SRAM | ~57 KB single buffer, ~114 KB double-buffered |
| ESP32-P4 (PARLIO), PSRAM | ~284 KB single buffer |

The ESPHome component documentation quotes roughly 24 KB for a 64x32 panel at 8-bit.

**Important ESP32-S3 constraint** from the DMA library documentation: when PSRAM backs the
DMA buffer, bandwidth caps the output clock at roughly 13 MHz, which limits how many panels
you can chain without flicker. Quad SPI PSRAM must never back the DMA buffer — too slow.
This board has octal PSRAM, so the path is open, but 20 MHz is not achievable while running
the buffer out of PSRAM.
