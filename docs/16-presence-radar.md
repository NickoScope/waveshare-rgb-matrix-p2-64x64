# A presence radar: effects that wake up when someone walks in

**Decided 2026-09-14: an Apollo MTR-1 is bought, and the encoder stays.** The
radar lives in its own box and reaches the panel over the network; the two
header pins stay with the knob. Nothing is built on the panel side yet. The
room radar page already exists in the simulator:
`tools/luasim/scripts/room_radar.lua` in the firmware repo.

## Which sensor

The owner remembers "model 2050". No product by that name was found on
hlktech.net, esphome.io or dfrobot.com. The two likely candidates are told
apart by size: **HLK-LD2450 is 15 × 44 mm** [1], **HLK-LD2410C is 16 × 22 mm** [7].
Settled by the purchase: the LD2450, inside the MTR-1.

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

### Already in the house: an Aqara FP2 (checked 2026-09-14)

The owner plugged his FP2 into the Raspberry Pi's USB. It is a Wi-Fi device,
already paired with Home Assistant through HomeKit Controller since June:
device `Presence-Sensor-FP2-8F01`, firmware 1.3.6, room "Гостиная".

- **USB gives it power, nothing more.** On the Pi, `lsusb` lists no Aqara
  device. The FP2 came back in HA over Wi-Fi 15 s after it was plugged in.
  Aqara specifies 5 V 1 A over USB-C [11].
- **The FP2 counts people; our HA path does not carry it.** The owner
  corrected a first reading that said otherwise. Each path gives:
  - **HomeKit, our path today, local:** one occupancy sensor per zone plus a
    light sensor [12][15]. With no zones set up, that is a single presence for
    the whole room: `binary_sensor.presence_sensor_fp2_8f01_presence_sensor_1`
    and `sensor.presence_sensor_fp2_8f01_light_sensor_light_level`.
    HomeKit Controller supports occupancy sensors. The FP2 must leave Apple
    Home before pairing with HA [14].
  - **Aqara cloud Open API:** people count for the whole view and per zone,
    over 10 s and per minute. The HACS integration ha-aqara-devices reads it
    as resources `0.60.85`, `13.120.85` and `13.{120+N}.85` [16].
    - Needs an Aqara developer account, the owner's app keys, message push,
      and a bridge listening on the LAN at :8080. That is a new network
      listener, so only with the owner's explicit yes.
    - Aqara's own resource list sits behind a developer login and was not
      read: **not verified**.
  - **Aqara's V3 trait catalogue** and the local LANLink route through an M3
    hub: occupancy, pose, sleep and vitals, but no count and no
    coordinates [17].
  - **Coordinates:** shown in the Aqara Home app [12]. No path out of the
    stock firmware was found.
  - **ESPHome firmware replacing Aqara's** gives count, zones and target
    positions every 500 ms, locally [18]. The cost: opening the case, a UART
    connection, backing up the calibration, and losing HomeKit, the app and
    the warranty.
- **Not verified:**
  - Matter on the FP2: not in Aqara's specs, and the firmware metadata's
    Matter id is empty.
  - Whether zones added later reach HA without re-pairing. One forum thread
    says they do not.
  - Which firmware brought people counting, and whether it is switched on for
    this unit. It runs 1.3.6, the newest in a public archive.
- **Already publishing for the panel.** Automation
  `automation.matrix_fp2_presence_to_mqtt` sends
  `{"any":bool,"zones":{...},"lux":n,"ts":epoch}`, retained, to
  `nickoscope_matrix/presence/fp2`. It fires when presence changes and when HA
  starts, and has been checked on the broker. It cannot tell an empty room
  from an offline sensor: both give `any:false`.

**How the two split:** the FP2 can drive idea 1 below, sleep and wake, today.
It can add a people count once the cloud route is approved. Only the MTR-1
gives the x/y blips for the radar page without reflashing the FP2. On the panel, presence
should be FP2 `any` OR MTR-1 has_target, with a hold-off before sleep. The
blips come from the MTR-1 alone. They work on different bands (60–64 GHz
[11] vs 24 GHz); whether they disturb each other side by side is not verified.

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

### Chosen: Apollo MTR-1, over the network

Its stock ESPHome config is public [13] and was read the day it was bought:

| On board | What it is for here |
|---|---|
| HLK-LD2450 on the C3's UART, 256 000 baud | presence, moving and still, count; X, Y, speed, angle and distance for three targets; three zones |
| LTR390 light and UV | the panel's brightness can follow the room. Its polling is off (`update_interval: never`) until the "LTR390 Update Interval" number is set |
| SCD40 CO2, temperature, humidity, every 60 s | a card when the air goes stale; the threshold is the owner's call |
| DPS310 pressure and temperature, every 30 s | — |
| RGB LED, buzzer (an API action plays RTTTL) | — |
| Button on GPIO9 | not a control: a self-test after 1 s held, factory reset after 8 s |

The stock firmware talks only to Home Assistant, over the native API; there is
no `mqtt:` in it. Its radar sensors carry no filters of their own, so ESPHome's
default one-second throttle applies [16].

**Stage 1 — nothing flashed on the MTR-1.** A Home Assistant automation
republishes what the panel needs to `nickoscope_matrix/presence`, retained:
present, count, moving, lux. On the panel, one small MQTT consumer in
`src/presence/`: dim when the room empties, wake when someone walks in, stop the
carousel while nobody is watching. The CO2 card needs no firmware at all — Home
Assistant can publish to `nickoscope_matrix/card/air` today. One update a second
is plenty for all of it.

**Stage 2 — the room radar page, live.** Adopt the MTR-1 in the ESPHome
dashboard (its config carries `dashboard_import`), add a package with `mqtt:`
that publishes the three targets as JSON ten times a second straight to the
broker, and lift the throttle on those sensors. ESPHome runs MQTT alongside the
native API — its docs warn only about MQTT *without* the API [26] — so Home
Assistant keeps everything it had. The exact filter override: not verified yet.

### Not chosen: straight onto the header, control moves to Home Assistant

Kept because the pin analysis is right and cost an evening to get right.

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

### Not chosen: a XIAO ESP32-C3 of our own, running ESPHome

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

## Installed, 2026-09-16

- **In Home Assistant:** the device "Apollo MTR-1 53bc60" sits in the living room area (Гостиная) on the ESPHome integration.
  - 79 entities, stem `apollo_mtr_1_53bc60`.
  - Apollo firmware 26.3.2.1 on ESPHome 2026.3.3, LD2450 firmware 2.04.23101915.
  - Online since 16:05:12.
- **Settings as found:**
  - Zone Type `Disabled`, all twelve zone corners 0;
  - Multi Target Tracking on;
  - Timeout 5 s;
  - LTR390 update interval 60 s;
  - **LD2450 Bluetooth on**. See the trap below; switching it off is the owner's call.
- **Zone limits Home Assistant reports:** X −4860…4860 mm, Y 0…7560 mm (the number entities' min and max).
- **First session, 16:05–16:18, from the recorder:**
  - Target 1 X was logged 749 times in 820 s, about once a second, which matches ESPHome's default throttle [16].
  - X ran from −1.32 to +1.35 m and Y from 0.16 to 1.76 m.
  - At most two targets at once; target 3 appeared once.
  - The moving and still counts changed about 330 times each in 13.7 minutes.
  - CO2 still read `unknown` 13 minutes after boot. The `scd40_temperature` and `scd40_humidity` entities have no state.
- **Dashboard:** "Радар MTR-1" at `/presence-radar`, view Гостиная.
  - The live radar is `custom:mtr1-radar-card`, source [`tools/ha/mtr1-radar-card.js`](../tools/ha/mtr1-radar-card.js). It draws the 6 m / ±60° fan, up to three targets with 15 s trails, and zones when Zone Type is not `Disabled`; `range_m` is 4 on the dashboard.
  - The card is registered as an inline module resource, because the SSH user cannot write `/config/www`.
  - Around it: tiles for presence, counts, the three targets, light and air, and the device, plus controls for multi-target tracking, radar Bluetooth, the timeout and the zone mode.
- **Replay page:** a private artifact "Радар гостиной" replays the first session from the recorder, with scale 2/4/6 m, speed and a timeline.
- **Open:**
  - radar Bluetooth;
  - zones, once the owner decides where the sofa and the door are;
  - the CO2 reading;
  - stage 1 (MQTT summary for the panel).

## Firmware shape, when it is built

- `src/presence/`: one state — present, moving, up to three targets with X, Y
  and speed, time last seen. Fed by MQTT from the MTR-1: the retained summary
  from Home Assistant in stage 1, the targets straight from ESPHome in stage 2.
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

## Previews on the first real session (2026-09-16 17:12)

Rendered from `~/panel-backups/2026-09-16-mtr1/mtr1_frames.json` (private, stays out of both repos) through `tools/luasim/presence_feed.py` and `presence_sheet.py` in the fork, window 16:16:52-16:18:22, the richest 90 s.

**What the session holds.** Essentially one person: slot 1 filled 793 of 802 s, a second target appeared for 5 s, slot 3 never. Median range 0.43 m, maximum 1.95 m. The room is empty 9 s in total; 19 s carry no sample, held rather than absent, which is how an HA state behaves between updates.

**Scale.** Recommended 4 m.
- 6 m wastes the top two thirds of the fan: people never leave the bottom 20 px.
- 2 m looks best on this session but is a trap. `in_fan()` drops anyone past 2.0 m and the session already reached 1.95 m, so the panel would show an empty room with a person standing there. The 2 m fan is also 4,124 pixels, which crosses Lua's 4,096-slot array boundary: the table doubles to 8,192 slots and the scene's heap peak goes from 159 KB to 261 KB. At 4 m the fan is 3,969 pixels, 127 short of that cliff.
- Cost with real targets is slightly lower than with the scripted ones: 63,439 instructions average per frame at 6 m against 64,856, 61,431 at 4 m, 60,406 at 2 m.

**The mirror** changes only which side people enter from; geometry and cost are identical. Which way +X points in the room is still unknown and has to be confirmed by walking in.

**Three things the real data exposed.**
1. **Speed units and sign.** `fake_targets()` returns cm/s (mm per 0.1 s), and the scene tests `t.speed > 12`. The LD2450 gives signed mm/s. Passed through raw, everything reads as moving, and a target approaching the sensor (negative) fails the test and gets the "sitting still" ring. The feed must pass `abs(mm/s) / 10`.
2. **No fallback when the feed stops.** The scene holds the last sample forever: a frozen dot, "1 IN ROOM", the still ring pulsing, indistinguishable from someone sitting still. The panel module needs an age limit, about 5 s, and an empty-room state after it.
3. **Jitter.** At 1 Hz the dot teleports between samples, and the 14-step trail collapses onto one pixel while the person is still. Interpolation or smoothing is a design decision, not a bug.

**For the future panel binding:** `fake_targets()` builds a fresh table per target per call and `draw()` calls it 19 times a frame. A binding must reuse one preallocated three-slot table and one position ring, and allocate nothing per frame; internal heap is the scarce resource (KB [22](22-audio-visualizer-onboard-mic.md) §12.3).

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
11. https://www.aqara.com/us/product/presence-sensor-fp2/specs/
12. https://cdn.shopify.com/s/files/1/0710/9220/7830/files/Presence-Sensor-FP2_User-Manual.pdf?v=1723628346
13. https://www.aqara.com/us/product/presence-sensor-fp2/
14. https://www.home-assistant.io/integrations/homekit_controller/
15. https://github.com/ebaauw/fp2-proxy
16. https://github.com/Darkdragon14/ha-aqara-devices/blob/main/custom_components/ha_aqara_devices/fp2.py
17. https://opendoc.aqara.com/en/docs/developmanual/apiDocument/trait-codes.html and https://github.com/absent42/Aqara-LANLink
18. https://github.com/JameZUK/esphome_fp2_ng
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
26. https://esphome.io/components/mqtt/
