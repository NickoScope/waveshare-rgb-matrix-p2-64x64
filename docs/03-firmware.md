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

### Tried on this board, 2026-09-14: rejected

`-DSPIRAM_DMA_BUFFER` on the Waveshare build (2 × 64×64 chained, 8-bit, double-buffered).

| | Internal SRAM buffers | PSRAM buffers |
|---|---|---|
| Internal heap free at the end of `setup()` | 37.0 KB | 167.7 KB |
| Internal SRAM the display still takes | ~147 KB (with the buffers) | 15.4 KB |
| Refresh the driver reports | 84 Hz | 84 Hz |
| Picture | clean | **stripes and flicker on every page** (owner, by eye) |
| TLS to the two pinned hosts (RTT, AeroAPI) | handshakes succeed | **every handshake failed**: `-9984`, X509 certificate verification failed |

Measured with `MEM_TRACE` checkpoints in `setup()`: internal free after each step, printed
over serial. The Wi-Fi connect step costs 46.5 KB in both builds.

The TLS failures are the stranger result. Both hosts served the same chain as in the morning,
when the same code verified it. The failures began with the DMA reading from PSRAM, alongside
mbedTLS, which also allocates there (`tls_psram.cpp`). The cause is **not established**, and
the build was reverted before it could be.

**Verdict:** the DMA buffers stay in internal SRAM. Internal heap has to be won elsewhere.

## Where loop() stalls — measured on the panel, 2026-09-14

`loop()` renders every page, so anything slow inside it freezes the picture.
The firmware now names the slowest part of each 10 s window: `/api/info`
reports `loopSlowPart` and `loopSlowPartMs`. Any part over 200 ms also prints
`[loop] <part> took N ms` on serial, with the URI when the part is the web
server.

| What | Before | After |
|---|---|---|
| Clock style change | ~1 s seen twice, blamed on the 129-key settings write | the write was not the cause; one key now, 0–3 ms, and style changes stay under 15 ms |
| Entering the yacht radar | 636 ms: the AIS TLS handshake inside `loop()` | 16–38 ms: the websocket runs on a task that lives with the page |
| Portal `/`, 128 KB | 1765 ms | open |
| `/panel.js`, 100 KB | 987 ms | open |
| `/portal.js`, 44 KB | 537 ms | open |
| API polls, 0.1–4 KB | 22–60 ms | — |

**Page transfers.** The web server is synchronous, so a page transfer holds
`loop()` for its whole length. Measured: 70–100 KB/s from the panel to a Mac
on the same Wi-Fi.

A likely limit is lwIP's 5760-byte send buffer
(`CONFIG_LWIP_TCP_SND_BUF_DEFAULT` in arduino-esp32 2.0.17's sdkconfig). It is
precompiled, so it cannot be changed from the sketch. Not measured
separately.

Sending fewer bytes is the lever:
- **Static assets:** gzip them; they are already cached for a year.
- **`/`:** it is a template carrying ~70 `%V_*%` settings tokens, so it
  would first need its values fetched as JSON.

## Over-the-air updates, checked 2026-09-14

**Partitions.** `default_16MB.csv` from arduino-esp32:
- two app slots, `app0` and `app1`, 6.4 MB each;
- `otadata`;
- `spiffs`, 3.4 MB;
- a 64 KB `coredump` partition at `0xFF0000`.

The module carries 32 MB of flash; the table uses the lower 16 MB. The
firmware is 2.29 MB, and `/api/info` reports `otaFreeBytes` of 6,553,600.

**Updating.** `POST /update` takes a multipart upload. Either use the portal's
update page (drop a `firmware.bin`), or run from a computer:

```bash
curl -F firmware=@.pio/build/matrix-waveshare-rgb/firmware.bin http://<panel-ip>/update
```

It answers `OK`, restarts after a second, and boots the other slot. There is
no `ArduinoOTA`/`espota`, so PlatformIO cannot upload over the network by
itself.

**Tested on the panel:**
- Upload: 2,292,032 B in 28.3 s, about 81 KB/s, the same rate the portal pages
  get.
- Back up on the new build 38 s after the upload started.
- A software reboot after that stayed on the new build.

**Rollback, as built from `8ec3045`.**
- The SDK is built with `CONFIG_BOOTLOADER_APP_ROLLBACK_ENABLE=1`. Out of
  the box, arduino-esp32 2.0.17 confirms every image in `initArduino()`
  (`cores/esp32/esp32-hal-misc.c`: the weak `verifyRollbackLater()` returns
  false). That runs before `setup()`, so rollback would only catch an image
  that fails even earlier.
- `src/health` overrides `verifyRollbackLater()` to return true and confirms
  the image itself once it has run: a minute up, Wi-Fi connected, and 200
  frames drawn (or the display off). The minute is a choice, not a measured
  figure.
- An image that crashes, or hangs until the task watchdog panics, before
  then is rolled back on the reset that follows. A hang that never resets
  stays until power is cycled.
- `/api/info` → `ota`:
  - `partition`;
  - `state`: `pending`, `valid`, or `undefined` when flashed over USB;
  - `rolledBackFrom`;
  - `confirmedAtS`.
- **Tested over OTA, 2026-09-14:**
  - The release image booted `pending` and confirmed itself after 60 s and
    3180 frames.
  - An image built with `-DHEALTH_ROLLBACK_TEST` aborts at 20 s, before it
    can confirm. It booted in `app1`, aborted, and the next boot came up in
    `app0`, reported as "rolled back from app1".

**No authentication.** `/update` takes a firmware from anyone on the home
network, like every other route of this portal. **Not changed.**

**Crash reports.** On a panic the SDK writes an ELF core dump to flash
(`CONFIG_ESP_COREDUMP_ENABLE_TO_FLASH`). At the next boot `src/health` reads
its summary, logs it, keeps it in NVS `health`, and erases the dump.

`/api/info` → `lastCrash` holds:
- `task`;
- `cause` and `causeName`: the Xtensa EXCCAUSE, named after ESP-IDF's
  `panic_arch.c`;
- `pc` and `addr`;
- up to eight backtrace addresses;
- `image`: the first 16 hex digits of the crashed image's ELF SHA-256;
- `bootReason` and `seenUtc`, for the boot that found it.

**An `abort()` or failed assert reads as `StoreProhibited` at address 0, with
`pc` in `panic_abort`.** The panic path writes to address 0 on purpose. The
rollback test image confirms it: its `pc` resolved to `panic_abort` at
`panic.c:408`, called from the deliberate abort in `boot_health.cpp`.

Decoding a backtrace needs the ELF whose SHA-256 starts with `image`. Keep
the ELF of every image that goes onto the panel: `~/AnimatedPixelClock-elf/`.

To read a dump by hand before a health build has booted and erased it
(this resets the panel):

```bash
~/.platformio/penv/bin/python ~/.platformio/packages/tool-esptoolpy/esptool.py --chip esp32s3 --port /dev/cu.usbmodem2101 read_flash 0xFF0000 0x10000 coredump.bin
```

```bash
~/.platformio/penv/bin/python -m esp_coredump --chip esp32s3 info_corefile --core coredump.bin --core-format raw --gdb ~/.platformio/packages/tool-xtensa-esp-elf-gdb/bin/xtensa-esp32s3-elf-gdb .pio/build/matrix-waveshare-rgb/firmware.elf
```
