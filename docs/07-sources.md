# Sources

Project rule: every number, threshold and claim about somebody else's hardware must have a
verifiable source. Below is what came from where, and what each source is authoritative for.
Everything checked 2026-09-06 unless noted.

## Vendor primary sources (highest confidence)

| Source | Authoritative for |
|---|---|
| [docs.waveshare.com/RGB-Matrix-Px-64x64](https://docs.waveshare.com/RGB-Matrix-Px-64x64) | panel specifications, GOB definition, terminal polarity warning, SKU table |
| [waveshare.com/wiki/RGB-Matrix-P2-64x64](https://www.waveshare.com/wiki/RGB-Matrix-P2-64x64) | HUB75 pin definitions, batch-to-batch layout warning, Raspberry Pi and Pico examples |
| [waveshare.com/rgb-matrix-p2-64x64.htm](https://www.waveshare.com/rgb-matrix-p2-64x64.htm) | pricing, box contents, the 5 V 4 A supply recommendation |
| [docs.waveshare.com/ESP32-S3-RGB-Matrix](https://docs.waveshare.com/ESP32-S3-RGB-Matrix) | board specifications, peripheral inventory |
| [.../Instructions-For-Use](https://docs.waveshare.com/ESP32-S3-RGB-Matrix/Instructions-For-Use) | menuconfig settings, download mode, TF card limited to MMC |
| [waveshare.com/esp32-s3-rgb-matrix.htm](https://www.waveshare.com/esp32-s3-rgb-matrix.htm) | price, 10 A rating, six-panel cascade claim, box contents |

## Vendor source code (highest confidence for pin maps)

All from [waveshareteam/ESP32-S3-RGB-Matrix](https://github.com/waveshareteam/ESP32-S3-RGB-Matrix), Apache 2.0.

| File | Authoritative for |
|---|---|
| `example/idf_v5.5.2/components/bsp/esp32_s3_matrix/include/bsp/config.h` | **the complete board pin map**: I2C, I2S including the microphone input, power amp, button, TF card |
| `.../bsp/esp32_s3_matrix/idf_component.yml` | dependency list, proving the BSP is built on `esphome/esp-hub75` ^0.3.5 |
| `example/idf_v5.5.2/sdkconfig.defaults` | **HUB75 pin map**, panel dimensions, default two-panel layout |
| `example/arduino_v3.3.7/.../platforms/esp32s3/esp32s3-default-pins.hpp` | **HUB75 pin map**, independent confirmation |
| `example/arduino_v3.3.7/08_Sensor_Test.ino` | I2C pins, sensor addresses, QMI8658 WHO_AM_I value |
| `example/arduino_v3.3.7/09_Music_Player.ino` | I2S pins, speaker, power amp, button, TF card pins |
| `hardware/schematics/ESP32-S3-RGB-Matrix-Schematics.pdf` | module part number and onboard chips |

## Library documentation

| Source | Authoritative for |
|---|---|
| [mrcodetastic/ESP32-HUB75-MatrixPanel-DMA](https://github.com/mrcodetastic/ESP32-HUB75-MatrixPanel-DMA) | latch blanking, clock phase, power and capacitor requirements, the ~13 MHz PSRAM ceiling, the Quad SPI prohibition, Wi-Fi interference |
| `src/platforms/esp32s3/esp32s3-default-pins.hpp` of the same library | upstream ESP32-S3 defaults, proving the board was laid out on them |
| [issue #134](https://github.com/mrcodetastic/ESP32-HUB75-MatrixPanel-DMA/issues/134) | the maintainer's catalogue of common failures, basis of the troubleshooting table |
| [esphome-libs/esp-hub75](https://github.com/esphome-libs/esp-hub75) | memory usage per platform, debug procedure, panel-height to scan-rate mapping |
| [esphome.io/components/display/hub75](https://esphome.io/components/display/hub75/) | every component option with defaults, current formula, strapping pins |
| [kno.wled.ge/advanced/HUB75](https://kno.wled.ge/advanced/HUB75/) | board and binary table, octal PSRAM requirement for 128x128, per-variant limits |
| [WLED v16.0.1](https://github.com/wled/WLED/releases/tag/v16.0.1) | existence of `ESP32-S3_Waveshare_HUB75.bin`, HUB75 fixes |

## Secondary sources (marked FYI in the text)

Used only where no primary source exists. They must not drive decisions.

| Source | What was taken | Caveat |
|---|---|---|
| LED display vendor blogs | properties of GOB technology in general | marketing for **other** products. IP65 claims do **not** apply to this panel: Waveshare claims no water resistance |
| zbotic.in review article | 80–120 brightness for daily use, 50–60 °C in a sealed enclosure | thresholds unverified by measurement or datasheet |
| Industry rule of thumb, pitch in mm equals viewing distance in metres | rough viewing-distance guidance | never checked against a standard |

## Verification status

| Claim | Status | How to close |
|---|---|---|
| ~~HUB75 pin map~~ | **CLOSED.** Confirmed by three sources, two of them Waveshare's own | — |
| ~~Peripheral pin map (I2C, I2S, mic, speaker)~~ | **CLOSED.** Confirmed by the vendor BSP `config.h` and two Arduino examples | — |
| `mic_power_rail` on GPIO46 | **UNVERIFIED.** Present in hub75-studio, absent from the vendor BSP. Possibly an ESPHome-specific addition | read the schematic, or test on hardware |
| Which shift driver the panel needs | **CONTRADICTION**, see #4 below | set GENERIC and look at the screen |
| Whether the configs in `configs/` work | not compiled, not flashed | build and flash |
| Real panel current under load | no measurements | clamp meter on a white field at brightness 128 and 255 |

## Contradictions found while compiling this

1. **Panel current.** Waveshare's datasheet says 5 V / 3 A. The ESPHome formula gives about
   1.9 A for 64x64. The product page recommends a 4 A supply. Design to the datasheet.

2. **Board rating versus cascade claim.** The board is rated 10 A, yet six panels are claimed
   supported, which is 18 A at worst case. The vendor is counting typical brightness.

3. **Panel pricing.** $31.99 for the GOB version on waveshare.com, three dollars more than
   the uncoated one.

4. **Shift driver: GENERIC or FM6126A — unresolved.** Waveshare's own materials disagree
   with each other.

   | Source | Says |
   |---|---|
   | Waveshare user guide (menuconfig) | `Shift Driver IC = Generic` |
   | Waveshare `sdkconfig.defaults` | no driver line, so GENERIC by default |
   | hub75-studio config | no driver line, so GENERIC by default |
   | **7 of 10 Waveshare Arduino examples** | `mxconfig.driver = HUB75_I2S_CFG::FM6126A;` |

   An earlier working hypothesis held that FM6126A was leftover from an unadapted upstream
   sample. That is now weak: `08_Sensor_Test`, `09_Music_Player` and `10_Chinese_Font` are
   all properly configured for 64x64 and still set FM6126A. Only `03_DoubleBuffer`,
   `06_BitmapIcons` and `07_Pixel_Mapping_Test` leave it alone.

   The honest reading: the ESP-IDF branch of Waveshare's materials uses GENERIC, the Arduino
   branch uses FM6126A. **Unresolvable without hardware.** Start with GENERIC; if the screen
   stays black on known-good power, switch to FM6126A.

5. **Default layout in the ESP-IDF example targets two panels, not one.**
   `CONFIG_HUB75_LAYOUT_ROWS=2`, `COLS=1`, `TOP_LEFT_DOWN_ZIGZAG`, i.e. 64x128 stacked
   vertically. Running that example on a single panel requires fixing the layout.

## What the schematic yielded

`hardware/schematics/ESP32-S3-RGB-Matrix-Schematics.pdf`, one page, downloaded and parsed
2026-09-06. Its text layer confirms the **ESP32-S3-WROOM-2-N32R16V** module (32 MB flash,
16 MB octal PSRAM), the **PCF85063** and **SHTC3** chips, the HUB75 signal nets R1, G1, B1,
R2, G2, B2, LAT, OE, CLK and E, and connector J4.

Associating nets with GPIO numbers from the flat text layer was not possible — the
schematic's coordinate typesetting scrambles label order. This does not matter, because the
source-code evidence is stronger: two independent vendor codebases that actually build and
run on this hardware, agreeing pin for pin.
