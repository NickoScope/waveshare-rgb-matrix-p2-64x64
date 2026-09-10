# Controller: Waveshare ESP32-S3-RGB-Matrix

SKU 34422. $24.99 on waveshare.com. Board size 50 x 42 mm.

## Key specifications

| Parameter | Value |
|---|---|
| SoC | ESP32-S3-N32R16, Xtensa LX7 dual core, up to 240 MHz |
| Module | ESP32-S3-WROOM-2-N32R16V (confirmed on the schematic) |
| SRAM / ROM | 512 KB / 384 KB |
| Flash | **32 MB** |
| PSRAM | **16 MB, octal** |
| Radio | Wi-Fi 2.4 GHz 802.11 b/g/n, Bluetooth 5 LE |
| Supply voltage | 5 V |
| **Maximum current rating** | **10 A** |
| Power inputs | two |
| Supported resolutions | 64x64, 64x32, 80x40, 96x48 |
| Maximum cascade | 6 x 64 x 64 |
| Operating temperature | -40 … +85 °C |

PSRAM mode is confirmed by the hub75-studio config: `mode: octal`, `speed: 80MHz`.

## Onboard peripherals

| Component | Function |
|---|---|
| ES8311 | low-power mono audio codec |
| ES7210 | audio ADC with echo cancellation |
| Dual microphones | array for noise suppression and echo cancellation |
| Speaker header | 8 Ω 5 W speaker included in the box |
| QMI8658 | 6-axis IMU, 3-axis accelerometer + 3-axis gyroscope |
| SHTC3 | temperature and humidity |
| PCF85063 | real-time clock, SH1.0 battery connector |
| TF card slot | **MMC mode only** |
| SN74HC245 | octal bus transceiver with three-state outputs on the HUB75 lines |
| USB Type-C | power, flashing, debugging |
| RST and BOOT buttons | BOOT is user-programmable |
| GPIO header | expansion |

The SN74HC245 buffer matters more than it looks. It lifts the ESP32's 3.3 V logic to what
the panel expects. On a bare ESP32 without a buffer, that mismatch is a classic source of
ghosting and flicker on longer ribbons — a whole class of problems this board removes.

## Complete pin map

**VERIFIED 2026-09-06 against Waveshare's own firmware sources.** Three independent
sources agree pin for pin.

| Source | File |
|---|---|
| Waveshare, ESP-IDF BSP | `example/idf_v5.5.2/components/bsp/esp32_s3_matrix/include/bsp/config.h` |
| Waveshare, ESP-IDF example | `example/idf_v5.5.2/sdkconfig.defaults` |
| Waveshare, Arduino examples | `platforms/esp32s3/esp32s3-default-pins.hpp`, `08_Sensor_Test.ino`, `09_Music_Player.ino` |
| hub75-studio, community | `packages/controllers/waveshare-esp32-s3-rgb-matrix.yaml` |

### HUB75

| Signal | GPIO | Signal | GPIO |
|---|---|---|---|
| R1 | 4 | A | 18 |
| G1 | 5 | B | 8 |
| B1 | 6 | C | 3 |
| R2 | 7 | D | 42 |
| G2 | 15 | E | 9 |
| B2 | 16 | LAT | 40 |
| OE | 2 | CLK | 41 |

### I2C — sensors and codecs

| Signal | GPIO |
|---|---|
| SDA | 47 |
| SCL | 48 |

Bus runs at 400 kHz on port 0. Device addresses: PCF85063 `0x51`, SHTC3 `0x70`.
The QMI8658 address is probed at runtime, identified by a WHO_AM_I value of `0x05`.

### I2S — audio

| Signal | GPIO | Note |
|---|---|---|
| SCLK / BCLK | 43 | bit clock |
| MCLK | 12 | master clock |
| LCLK / LRCLK / WS | 38 | word select |
| DOUT | 21 | to speaker, ES8311 |
| DSIN | **39** | **from microphones, ES7210** |
| Power amp enable | 11 | `BSP_AUDIO_PA_REVERTED` is false |

I2S port 0.

### TF card — 1-bit MMC

| Signal | GPIO |
|---|---|
| D0 | 17 |
| CMD | 44 |
| CLK | 1 |
| D1, D2, D3 | not connected |
| SPI CS (alternate path) | 14 |

D1 through D3 being unconnected is why the documentation states MMC 1-bit mode only.

### Button

| Signal | GPIO |
|---|---|
| BOOT / main button | 0 |

Used with `INPUT_PULLUP` in the Arduino examples.

### Still unverified

One pin from the hub75-studio config has no counterpart in Waveshare's BSP:
`mic_power_rail` on **GPIO46**. It may be an ESPHome-specific addition. **UNVERIFIED.**
Every other pin in that community config matched Waveshare's sources exactly, so it is
probably right, but it has not been confirmed.

## Why these pins

Waveshare laid the board out on the **default ESP32-S3 pinout of the
`mrcodetastic/ESP32-HUB75-MatrixPanel-DMA` library**. Comparing against upstream
`src/platforms/esp32s3/esp32s3-default-pins.hpp` shows thirteen of fourteen pins identical.
Exactly one differs:

| Pin | Upstream | Waveshare |
|---|---|---|
| E | `-1` (unassigned) | **9** |

Upstream leaves E unassigned because only 1/32-scan panels need it. Waveshare routed it
to GPIO9.

**The time-saving consequence:** any sketch built on that library runs here with no pin
configuration whatsoever. One line covers it:

```cpp
mxconfig.gpio.e = 9;
```

That is precisely what Waveshare does in `01_SimpleTestShapes` — the other thirteen pins
come from the library defaults.

## Recommended driver settings

From Waveshare's own user guide:

| Setting | Value |
|---|---|
| Panel width / height | 64 / 64 |
| Scan wiring pattern | Standard |
| Shift driver IC | Generic |
| Bit depth | 8 |
| Output clock speed | 20 MHz |
| Minimum refresh rate | 60 Hz |
| Default brightness | 128 |
| Display rotation | 0° |

**Caveat on the shift driver.** The user guide and the ESP-IDF configuration both point at
`GENERIC`, but seven of Waveshare's ten Arduino examples explicitly set `FM6126A` — including
four correctly configured for a 64x64 panel. Their own materials disagree with each other.

Since 2026-09-10 there is outside evidence: the AnimatedPixelClock project runs two Waveshare
P2.5 64x64 panels on this same DMA library and marks `FM6126A` as verified on real hardware,
alongside `clkphase = false` to stop the rightmost column dropping. Those are P2.5 panels and
ours is the P2 GOB, so it is not proof, but the balance has moved. See contradiction #4 in
[07-sources.md](07-sources.md).

Start with `GENERIC` anyway — one reflash settles it, and a wrong init sequence is
indistinguishable from a wiring fault. If the screen stays black on good power, `FM6126A` is
the first thing to change.

## Flashing mode

If the port is not detected:

1. Hold BOOT
2. Plug in USB
3. Release BOOT

Press RESET after the upload finishes.

## About the current headroom

The 10 A rating does not square with the claimed six-panel cascade: 6 x 3 A = 18 A. The
manufacturer is evidently counting typical brightness rather than a full white field.

For a 2x2 build from these panels the worst case is 4 x 3 = 12 A, already above the board's
rated 10 A. Either cap brightness, or feed the panels directly from the supply instead of
routing all the current through the board.

## Versus the Apollo M-1 Rev6 controller

| | Apollo M-1 Rev6 | Waveshare |
|---|---|---|
| Flash | 16 MB | 32 MB |
| PSRAM | 8 MB octal | 16 MB octal |
| Current on 5 V | ~3 A | 10 A |
| Microphone | $6.99 add-on, one | two onboard |
| Audio out, IMU, RTC, climate, SD | none | all present |
| Panels in cascade | 4 | 6 |
| Price | $27.99 | $24.99 |

Cheaper and better specified on every line. It loses only on software readiness, see
[03-firmware.md](03-firmware.md).
