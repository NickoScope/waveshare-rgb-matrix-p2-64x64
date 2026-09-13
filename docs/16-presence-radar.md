# A presence radar: effects that wake up when someone walks in

An idea, not built. Written 2026-09-14 so it is not lost.

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
5. **A room radar page.** The yacht radar already draws blips with trails on a
   map; the room is a smaller map, and three people are three blips.

The carousel should stop when the room is empty: nobody is there to see it.

## How to connect it

The header U8 has two signal pins, IO45 and IO46, and the encoder uses both
([11](11-control-and-pins.md)). So:

| Option | Pins on the matrix | Good for | Cost |
|---|---|---|---|
| **A. Through Home Assistant** (start here) | none | ideas 1–3 now | the sensor needs its own small ESP with ESPHome; MQTT topic `nickoscope_matrix/presence` on the bus we already have |
| B. Straight into the matrix | one: the radar's TX into a GPIO (RX only, no config) | ideas 4–5 at the full 10 Hz | there is no free header pin; take IO10 (RTC interrupt) or IO13 (IMU interrupt) from a pad and give that interrupt up |
| C. Move the knob to I2C | frees IO45/46 for the radar | everything, cleanly | I2C is GPIO47/48, and whether they run at 1.8 V is open question 6 in [12](12-bringup.md) |

Option A first: no soldering, no pin fight, and it proves which effects are
worth it. ESPHome throttles every sensor to one update a second by default [5],
fine for waking up, too slow for eyes that follow you; lower it if idea 4 is
tried over MQTT.

## Firmware shape, when it is built

- `src/presence/`: one state — present, moving, up to three targets with X, Y
  and speed, time last seen. Fed by MQTT (option A) or by a UART parser
  (option B).
- A Lua binding, so effects in `luasim` can be written against a fake person
  before a real one exists.
- Flag `PRESENCE_ENABLED`, with the usual `#error` for a missing dependency
  and a row in `tools/flag_matrix.py`.

## Traps already known

- **The LD2450 sign bit is inverted**: top bit 1 means positive. It is not
  two's complement [2][4].
- **Radar sees behind itself.** Hi-Link suggests a metal plate behind it [3][6].
  A panel on a wall with a room on the other side will count the neighbours.
- **False triggers** from curtains, pets, plants in a draft, air conditioners and
  fans [3][6].
- Mount at 1.5–2 m on a wall [3]. Never point two 24 GHz radars at each other [3].
- Sending "enable configuration" stops the data until "end configuration" [4].
- **Not verified:** whether the LD2450 keeps a person who is sitting perfectly
  still, and whether the HUB75 panel disturbs the radar at close range. Both
  are bench tests before idea 1 is trusted.

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
