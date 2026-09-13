# A presence radar: effects that wake up when someone walks in

An idea, not built. Started 2026-09-14 so it is not lost. The room radar page
already exists in the simulator: `tools/luasim/scripts/room_radar.lua` in the
firmware repo.

## Which sensor

The owner remembers "model 2050". No product by that name was found on
hlktech.net, esphome.io or dfrobot.com. The two likely candidates are told
apart by size: **HLK-LD2450 is 15 × 44 mm** [1], **HLK-LD2410C is 16 × 22 mm** [7].
Measure the board before writing any code.

| | HLK-LD2450 | HLK-LD2410C |
|---|---|---|
| Supply | 5 V, average 120 mA [3] | 5 V, average 79 mA [6] |
| Link | UART 256 000 baud, 3.3 V logic [2] | same [6], plus an OUT pin, high = present [6] |
| Tells you | up to 3 people, each with X, Y in mm and speed [2] | nobody / moving / still, with distance [8] |
| Range, view | 6 m, ±60° across, ±35° up and down [1] | 5 m [7], ±60° [6] |
| Rate | 10 Hz [2] | not verified |
| ESPHome | native `ld2450` [5] | native `ld2410` [9] |

The LD2450 is the more interesting one here: it knows **where** you are, not
only **that** you are.

## What it could do on the panel

Ordered from cheapest to most ambitious.

1. **Sleep and wake.** Empty room: dim to a faint clock. Someone enters: fade
   up. Needs only "present or not" plus a hold-off of a few minutes, so a
   person sitting still is not put in the dark.
2. **Calm or lively by motion.** Moving people get the snake and the Tetris
   clock; people sitting still get the world clock and the plain clock.
3. **Distance picks the page.** Far away, only big digits are readable; up
   close, the flight board's small text is worth showing.
4. **Effects that look at you.** With X and Y: the snake heads toward the
   person, a pair of eyes follows them, particles lean their way.
5. **A room radar page** — drawn in the simulator already: the sensor's own
   fan, people as blips with trails, a ring around whoever sits still.

The carousel should stop when the room is empty: nobody is there to see it.

## How to connect it

### Option 1 — straight onto the header, control moves to Home Assistant

The header U8 has two signal pins, IO45 and IO46 ([11](11-control-and-pins.md)).
Today the encoder has both. Give them to the radar instead, and the knob's job
goes to Home Assistant over the MQTT bus we already have.

| Radar pin | Goes to | Why |
|---|---|---|
| 5V | an M3 power post H2/H3 (the panel's 5 V) | the header has only 3V3, and the radar wants 5 V [3] |
| GND | header GND | |
| TX | **IO45**, as UART RX | IO45 is ignored at reset on this module, so a line that idles high costs nothing |
| RX | **IO46**, as UART TX | lets the firmware send commands: Bluetooth off, zones |

**Both are strapping pins, so what the radar does to them at reset matters.**
A UART line idles high.

- **IO45 is ignored on this module.** On a bare chip it selects VDD_SPI at
  reset, 3.3 V or 1.8 V [11]. But the WROOM-2-N32R16V carries an ESP32-S3R16V,
  and on that chip VDD_SPI "has been set to 1.8 V by eFuse" [24]; with the eFuse
  set, GPIO45 no longer affects it [25]. So the radar's TX, high from the moment
  the radar has power, goes here. It is also why the encoder was safe on it — a
  knob can only pull a pin to ground, which is the default anyway.
- **IO46 still matters, a little.** With GPIO0 it picks the boot mode. In
  normal boot GPIO0 is high and IO46 is ignored; to enter the serial bootloader
  it must be low or floating [10]. The radar's RX is an input, so it can hold
  IO46 high at reset only through a pull-up of its own — not verified. If it
  has one, holding BOOT through a reset will not enter download mode while the
  radar is plugged in. Normal boot is unaffected. Whether esptool's automatic
  reset over USB is: not verified.
- Both pins have weak pull-downs by default [12].
- The first version of this page put the radar's TX on IO46 and kept IO45 for
  later, pending an eFuse read. That was over-cautious and inconsistent with the
  encoder decision; the module datasheet settles it. Confirm on the board anyway:
  `espefuse.py summary` is read-only and should show `VDD_SPI_FORCE = True`.

**What it costs:** the knob. **What remains physical:** the BOOT button on
GPIO0 still works as one button, for "next page".

**What it gives:** one box, the radar at its full 10 Hz with no network in the
way, and presence that keeps working when Wi-Fi does not.

**Firmware work it needs:** today everything about pages sits under
`CONTROL_ENCODER_ENABLED`. The page model has to come out from under it, with
the encoder, the BOOT button, MQTT commands and the radar as separate inputs.
Home Assistant gets MQTT discovery entities: a select for the page, a select for
the clock style, a button for next.

### Option 2 — a separate XIAO ESP32-C3 running ESPHome

No pins on the matrix, the knob stays. **A C3 is enough; an S3 buys nothing
here.** Apollo's MTR-1 ships the same pairing, an LD2450 on an ESP32-C3 with the
radar on GPIO21/20 at 256 000 baud, using ESPHome's own component [13].

| LD2450 | XIAO ESP32-C3 [14] |
|---|---|
| 5V | 5V (5 V out from USB) |
| GND | GND |
| TX | D7 = GPIO20 (RX) |
| RX | D6 = GPIO21 (TX) |

Avoid D0, D8 and D9 on the C3: GPIO2, 8 and 9 are its strapping pins [14]. The
C3's logger defaults to USB_SERIAL_JTAG, so the UART is the radar's alone [15].

```yaml
# https://esphome.io/components/sensor/ld2450/
uart:
  id: uart_ld2450
  tx_pin: GPIO21
  rx_pin: GPIO20
  baud_rate: 256000
  parity: NONE
  stop_bits: 1

ld2450:
  id: ld2450_radar
  uart_id: uart_ld2450
```

It then exposes `target_count`, `target_1`…`target_3` with `x`, `y`, `speed`,
`distance` and `angle`, and `has_target`, `has_moving_target`,
`has_still_target` [5]. **Every sensor is throttled to one update per second by
default**, through a `throttle_with_priority: 1000ms` filter; the old
`throttle` option is gone [16]. Fine for waking up. For eyes that follow you,
override each sensor's filters — the exact syntax is not verified yet.

### Or buy it

| Product | Radar | Chip | Open ESPHome config |
|---|---|---|---|
| Apollo MTR-1 [17] | LD2450 | ESP32-C3 | yes, the native component [13] |
| SCREEK Human Sensor 2A [18] | LD2450 | ESP32-C3 | yes, its own UART parser [19] |
| Everything Presence Lite [20] | LD2450 | ESP32 | yes [21] |

Seeed's own XIAO radar kits use the MR24HPC1 and the LD2410B [22][23]: no X and
Y, so not these.

## Firmware shape, when it is built

- `src/presence/`: one state — present, moving, up to three targets with X, Y
  and speed, time last seen. Fed by a UART parser (option 1) or by MQTT
  (option 2).
- A Lua binding shaped like `fake_targets()` in `room_radar.lua`, so the
  simulator script moves across unchanged.
- Flag `PRESENCE_ENABLED`, the usual `#error` for a missing dependency, and a
  row in `tools/flag_matrix.py`.

## Traps already known

- **The LD2450 sign bit is inverted**: top bit 1 means positive. It is not
  two's complement [2][4].
- **Radar sees behind itself.** Hi-Link suggests a metal plate behind it [3][6].
  A panel on a wall with a room on the other side will count the neighbours.
- **False triggers** from curtains, pets, plants in a draft, air conditioners and
  fans [3][6].
- Mount at 1.5–2 m on a wall [3]. Never point two 24 GHz radars at each other [3].
- Sending "enable configuration" stops the data until "end configuration" [4].
- Bluetooth is on by default [2]. The firmware should switch it off over the RX
  wire; otherwise anyone nearby with the app can reconfigure the radar.
- **Not verified:** whether the LD2450 keeps a person who sits perfectly still,
  and whether the HUB75 panel disturbs the radar at close range. Both are bench
  tests before idea 1 is trusted.

## Sources

1. https://www.hlktech.net/index.php?id=1157
2. https://make.net.za/wp-content/datasheets/HLK%20LD2450%20Serial%20Communication%20Protocol%20v1.03.pdf
3. https://github.com/kavindamihiran/HLK-LD2450/blob/main/hlk_ld2450_datasheet.pdf (Hi-Link's PDF, third-party copy)
4. https://d.hlktech.net/download/HLK-LD2450/1/HLK-LD2450%20operation%20manual.doc..pdf
5. https://esphome.io/components/sensor/ld2450/
6. https://d.hlktech.net/download/HLK-LD2410C/1/HLK%20LD2410C%20Human%20%20Presence%20Sensor%20Module%20Data%20Sheet%20V1.00.pdf
7. https://www.hlktech.net/index.php?id=1095
8. https://shop.ideaelec.com/wp-content/uploads/2025/02/HLK-LD2410C-Serial-communication-protocol-V1.07.pdf (Hi-Link's PDF, third-party copy)
9. https://esphome.io/components/sensor/ld2410/
10. https://docs.espressif.com/projects/esptool/en/latest/esp32s3/advanced-topics/boot-mode-selection.html
11. https://documentation.espressif.com/esp32-s3_technical_reference_manual_en.html — §8.4 VDD_SPI Voltage Control
12. https://documentation.espressif.com/esp32-s3-wroom-2_datasheet_en.html — §4 Boot Configurations, Table 4-1
13. https://github.com/ApolloAutomation/MTR-1/blob/main/Integrations/ESPHome/Core.yaml
14. https://wiki.seeedstudio.com/XIAO_ESP32C3_Getting_Started/
15. https://esphome.io/components/logger/
16. https://github.com/esphome/esphome/blob/dev/esphome/components/ld2450/__init__.py
17. https://apolloautomation.com/products/mtr-1
18. https://shop.screek.io/products/2a
19. https://github.com/screekworkshop/screek-human-sensor/blob/main/2a/yaml/human-sensor-2a-stable-github.yaml
20. https://shop.everythingsmart.io/products/everything-presence-lite
21. https://github.com/EverythingSmartHome/everything-presence-lite/blob/main/common/ld2450-base.yaml
22. https://wiki.seeedstudio.com/mmwave_human_detection_kit/
23. https://wiki.seeedstudio.com/mmwave_for_xiao/
24. https://documentation.espressif.com/esp32-s3-wroom-2_datasheet_en.html — §1.2 Series Comparison (S3R8V/S3R16V inside) and §8 Module Schematics (VDD_SPI set by eFuse)
25. https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/schematic-checklist.html — in-package flash/PSRAM with VDD_SPI_FORCE: GPIO45 no longer affects VDD_SPI
