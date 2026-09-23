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

### Also tried, 2026-09-23: one DMA frame — rejected

One DMA frame instead of two, with pages drawing into PSRAM and the changed rows copied at
each flip, timed to the scan through the GDMA descriptor the DMA is on. It frees 64 KB, but a
probe on the panel counted frames shown half old and half new. Without timing, 63 % were
mixed. With the best timing, 1-2 % were still mixed, every one of them row 0 written while
the scan was on row 31. Double buffering has none by construction, and the owner keeps it
(branch feat/frame-in-psram, parked).

### Won elsewhere, 2026-09-23: page and effect state in PSRAM (2.5.6)

The inventory that should have come first: `nm`/`size` over every object file showed 67 KB
of our own statics in internal RAM, 54 KB of it in 48 objects of 256 B or more. Of the 34.8 KB
of page and effect state moved to PSRAM, 22.6 KB came from upstream code and 12.2 KB from ours.
Most of the run-time pressure is ours: the fetch tasks, the broker, MQTT and the yacht stream.
The move uses `PSRAM_ARRAY()`/`PSRAM_OBJECT()` in `src/util/psram_state.h`: a reference to a
zeroed PSRAM block, allocated by the global constructors, trivial types only.

| Radio pool (internal DMA-capable heap) | 2.5.5 | 2.5.6 |
|---|---|---|
| Free, ordinary running | 13.3–15.2 KB | 30–50 KB (median 48 KB, 2 h 20 min) |
| Lowest since boot | 172 B | 21.5 KB |
| Failed Wi-Fi allocations | 3 → 9 in 20 min; network lost ~3 min at 11:28 with no test running | 0 |
| Self-test, normal pace | WARN (twice) | PASS (also `--stress`) |

The HUB75 frames, double buffering and colour depth are unchanged. Other levers were checked
against the sources and ruled out:
- frames in PSRAM: the library lowers the bus clock and the colour depth;
- task stacks in PSRAM: FreeRTOS asserts internal stacks, and the prebuilt config has no
  external stacks;
- `.bss` in PSRAM through `EXT_RAM_ATTR`: `CONFIG_SPIRAM_ALLOW_BSS_SEG_EXTERNAL_MEMORY` is off;
- mbedTLS: already in PSRAM since 2026-09-14.

**Rules, enforced from 2026-09-23** (AGENTS.md section 7 in the fork):
1. New page or effect state goes to PSRAM. `tools/ram_budget.py` runs at every commit that
   touches `src/` and in `release.py`. It fails on a new internal object of 256 B or more that
   is not listed with a reason, or on a total `.dram0` more than 1 KB over the budget in
   `tools/ram_budget.json`. Both numbers are our policy, not a standard.
2. Network work takes turns (lock/broker); a new long-lived connection is measured first. The
   yacht stream alone holds ~16 KB.
3. Every change is measured against the baseline in the same conditions: health self-test at
   normal and stress pace, and a `dmaMin` log over a long run, compared with 21.5 KB.
4. Check the sdkconfig for the board's own memory type (`tools/sdk/esp32s3/<type>/include/`),
   not the top-level one.

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
| Portal `/`, 128 KB | 1765 ms | 18.9 KB gzip, 0.14 s; a revalidation gets a 304 (`8c5f8cf`) |
| `/panel.js`, 100 KB | 987 ms | 31.4 KB gzip, 0.21 s |
| `/portal.js`, 44 KB | 537 ms | 15.7 KB gzip, 0.17 s; the settings arrive separately from `/api/portal`: 6.3 KB, 0.11 s |
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

Both done since `8c5f8cf`: the page is one static gzip for every build, and
its values come from `/api/portal`. Checked on the panel:
- all 105 settings the old template filled read the same from `/api/portal`;
  the other 42 controls on the page are file pickers, search boxes, or Panel
  controls that `panel.js` fills;
- in a browser the form filled in and Save was enabled;
- internal heap was 40 KB right after `/api/portal` was served;
- no request held `loop()` for more than 200 ms.

## Over-the-air updates, checked 2026-09-14

**Partitions: moved to 32MB on 2026-09-15, 18:46–18:54, over USB, with `tools/flash/repartition_32mb.py`.**
- **What the tool did:**
  - read the old LittleFS in download mode and verified it on the chip;
  - extracted 5 files (3 animations, 2 icons), 3 484 452 B;
  - built a 23 986 176 B littlefs image (block 4096, name_max 255, disk v2.1) and re-mounted it to verify;
  - checked that the old LittleFS was unchanged since the read;
  - `pio upload` wrote the bootloader, the new table, `boot_app0` and the app;
  - wrote the image at 0x910000 and ran `verify_flash` (digest matched).

  The FS write took 300 s.
- **After the reboot:**
  - LittleFS 23 986 176 B total, 20 459 520 B free, all three animations listed;
  - the market record written for the first time (`wrote 87260 B in 1061 ms`);
  - 69 market payloads accepted, 0 refused;
  - no crash this boot.
- **OTA state:** `app0` / `undefined`, as expected for an image flashed over USB (upstream notes the same). The next OTA gets the normal pending-verify path.
- **Watch:** `minFreeHeap` was 12 532 B at 74 s of uptime, lower than the ~33 KB seen before. Check whether it comes from the first boot's work or recurs.
- **Rollback image:** `~/panel-backups/2026-09-15-before-32mb/flash_full.bin` (private); `restore-old` writes it back.
- **Core dump offset:** the read command below now uses `0x1FF0000`, not `0xFF0000`.

**Partitions: the plan as it was (2026-09-15).**
Upstream v2.3.1 declares the whole 32MB part with arduino-esp32's
`large_littlefs_32MB.csv` (Keralots 86955e61, flash access checked at
0x00F00000, 0x01800000 and 0x01FE0000 with IDF 4.4.7). Our env follows in
`feature/market-dashboard`.

| Partition | `default_16MB.csv` (now) | `large_littlefs_32MB.csv` (next) |
|---|---|---|
| nvs | 0x9000, 20K | 0x9000, 20K (unchanged: settings and WiFi survive) |
| otadata | 0xe000, 8K | 0xe000, 8K |
| app0 / app1 | 0x10000 / 0x650000, 6.25MB each | 0x10000 / 0x490000, 4.5MB each (the image is 2.15MB) |
| spiffs (LittleFS) | 0xc90000, 3.4MB | 0x910000, 23.9MB |
| coredump | 0xFF0000, 64K | 0x1FF0000, 64K |

Why: the animations fill 3.4MB (12KB free on 2026-09-15). The market
record's free-space guard (doc 18) then skips the record.

How:
- Only a USB flash changes the table; OTA cannot.
- LittleFS moves, so its files are copied first: a full 32MB backup, the old
  filesystem extracted, a new 23.9MB image built and verified.
- Then the app with the new table is flashed, then the image
  (`tools/flash/repartition_32mb.py`).
- The core dump read command below changes to offset `0x1FF0000`.

**The backup before the move (2026-09-15 18:28).**
- **Full dump.** `read_flash 0 0x2000000` over USB at 921600 took 470 s, into `~/panel-backups/2026-09-15-before-32mb/flash_full.bin`. The file is private: it holds NVS with the WiFi credentials, sits outside every repository, and has mode 600. Size 33 554 432 B, sha256 prefix `ec13f02b01a49ccf`. Its table at 0x8000 decodes to `default_16MB.csv`.
- **Read check.** A second read of a static region, the first 1 MB of app1 at 0x650000, matched byte for byte (14.4 s).
- **LittleFS moves between boots.** A second read of the spiffs region, taken after one boot, differed in exactly 2 of 864 blocks (720, 721). They carry the same littlefs revision header, and the new read holds more committed data. The firmware appended to a metadata pair while it ran; this was not a read error.
- **Consequence for the move.** The files are copied from a read made with the chip held in download mode (`--after no_reset`) right before flashing, so the firmware never runs between that read and the new table.

**Partitions until then.** `default_16MB.csv` from arduino-esp32:
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

**Reaching the panel.** `http://NickoScope-64x128.local/` - the portal, `/api/info`,
`/api/diagnostics` and `/update`. The IP moves (192.168.4.43 in the older notes,
192.168.4.62 on 2026-09-17), so use the name.

**Crash reports.** On a panic the SDK writes an ELF core dump to flash
(`CONFIG_ESP_COREDUMP_ENABLE_TO_FLASH`). At the next boot `src/utils/crash_report.cpp`
checks its checksum, reads the summary, keeps it in NVS `crash` and erases the
dump. **Since 2026-09-17 this is the module sent upstream as PR #7**, copied
here byte for byte so a later merge from upstream is a no-op; `src/health` keeps
only the OTA rollback. The old record in the NVS namespace `health`, written by
the version before it, stays there unread.

`/api/info` → `lastCrash` holds:
- `task`;
- `cause` and `causeName`: the Xtensa EXCCAUSE, named after ESP-IDF's
  `panic_arch.c`, the pseudo causes (interrupt watchdog, double exception)
  included;
- `pc` and `addr`;
- up to sixteen backtrace addresses, and `backtraceCorrupted` when the SDK
  says so;
- `elfSha256`: the first 16 hex digits of the crashed image's ELF SHA-256,
  and `sameFirmware`: whether that is the firmware running now;
- `resetReason` and `bootTime`, for the boot that found it, and `thisBoot`.

**An `abort()` or failed assert reads as `StoreProhibited` at address 0, with
`pc` in `panic_abort`.** The panic path writes to address 0 on purpose. The
rollback test image confirms it: its `pc` resolved to `panic_abort` at
`panic.c:408`, called from the deliberate abort in `boot_health.cpp`. **The
report now names those cases itself**: `abort()`, or `Task watchdog` when the
reset reason is the task watchdog - but only when `sameFirmware` is true, since
`panic_abort` moves between builds. For the task watchdog, `task` and the
backtrace belong to whatever its interrupt stopped, not to the task that hung;
which task failed to feed it is only in the serial log.

Decoding a backtrace needs the ELF whose SHA-256 starts with `image`. Keep
the ELF of every image that goes onto the panel: `~/AnimatedPixelClock-elf/`.

To read a dump by hand before a health build has booted and erased it
(this resets the panel):

```bash
~/.platformio/penv/bin/python ~/.platformio/packages/tool-esptoolpy/esptool.py --chip esp32s3 --port /dev/cu.usbmodem2101 read_flash 0x1FF0000 0x10000 coredump.bin
```

```bash
~/.platformio/penv/bin/python -m esp_coredump --chip esp32s3 info_corefile --core coredump.bin --core-format raw --gdb ~/.platformio/packages/tool-xtensa-esp-elf-gdb/bin/xtensa-esp32s3-elf-gdb .pio/build/matrix-waveshare-rgb/firmware.elf
```
