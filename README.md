# Waveshare RGB-Matrix-P2-64x64 + ESP32-S3-RGB-Matrix

Knowledge base for the Waveshare **RGB-Matrix-P2-64x64-B** LED panel (SKU 33838, GOB
version) driven by the Waveshare **ESP32-S3-RGB-Matrix** controller board (SKU 34422).

Everything here is traced to a primary source. The complete board pinout was verified
against Waveshare's own firmware sources and the board schematic, not copied from a forum
post.
See [docs/07-sources.md](docs/07-sources.md) for the full audit trail.

Compiled 2026-09-06.

## The story so far

It started with the Apollo M-1, a ready-made LED display for Home Assistant. It looks
great, but it isn't cheap, so I wanted to know what's inside. The panel turned out to be a
stock Chinese 64×64 HUB75 panel that dozens of brands resell, and Waveshare sells the same
one for noticeably less. The controllers are a different story: Apollo's and Waveshare's
are two independent designs ([full comparison](docs/08-apollo-m1-comparison.md)).

So I ordered four 64×64 panels and two of Waveshare's own ESP32-S3-RGB-Matrix controllers.
I went denser than Apollo: 2 mm pitch, 128×128 mm per panel, and the LEDs are sealed under
clear resin (GOB), so bumping them isn't a disaster. Two panels side by side make a 128×64
screen, so I'll end up with two independent displays.

While the parcel is in the post, I've been digging through the documentation. Here's what
I found and what I'm going to do with it.

### The hardware

The Waveshare controller is packed: ESP32-S3, 32 MB of flash, 16 MB of fast PSRAM,
microphones, a speaker output, a real-time clock, a temperature and humidity sensor, an
accelerometer and an SD slot. The most important part is a buffer chip that lifts the
signals from 3.3 V to the 5 V the panel expects. On a bare ESP32 without one, panels often
flicker and ghost; here that whole class of problems is solved before you start.

I checked the pinout against three different Waveshare sources and they all agreed. I still
nearly got it wrong. I worked out which pins the firmware didn't use and assumed they were
free. Then I opened the board schematic: the expansion header has just four pins — two
GPIOs, ground and 3.3 V — and the pins I'd counted as free are actually the interrupt lines
for the clock and the accelerometer. Lesson learned: code tells you what the firmware does,
only the schematic tells you what the board is. The schematics now live
[in this repo](reference-drawings/) ([pin budget](docs/11-control-and-pins.md)).

Worth knowing up front:

- Power doesn't pass along the chain. Each panel has its own socket, and Waveshare's advice
  is 4 A per panel even though the spec table says 3 A. Two panels need an 8 A supply.
- The driver library officially goes up to 128×64. You can do 128×128 with four panels,
  but that's past the official line and you lose colour depth.
- A Raspberry Pi is out: the main library for these panels doesn't run on the Pi 5,
  because the way its GPIOs work changed. For this job the ESP32-S3 is the best choice
  right now, and it's what the library's author recommends too.
- One question the documentation can't settle: which driver chip the panel uses. The
  sources disagree, so I'll find out with firmware once the panels arrive.

And one funny find. For small text I picked the tiny Picopixel font, and in it the letter U
differs from V by a single pixel. On the airport board, ZURICH read as ZVRICH. One dot in
the font fixed it.

### What I'm building: a fork of AnimatedPixelClock

The base is [AnimatedPixelClock](https://github.com/Keralots/AnimatedPixelClock) by
Keralots: an open clock for exactly this kind of 128×64 ESP32-S3 screen, with about fifteen
animated styles — Mario, Tetris, Snake, Pac-Man and more. It's MIT-licensed, so I can build
on it freely. [My fork](https://github.com/NickoScope/AnimatedPixelClock/tree/board/waveshare-esp32-s3-rgb-matrix)
adds:

- **An airport board.** Arrivals and departures at Nice: Home Assistant fetches the data and
  sends it to the screen over MQTT. Each line has the time, flight, airport code, city and
  status in words — "landed", "delayed". I tested it with live data and it immediately broke
  a couple of things made-up data never would. For example, the API gives Blagnac as
  Toulouse's "city", which is the suburb the airport is in.
- **A yacht radar for the Bay of Cannes.** I brought the idea over from my oscilloscope
  project. The left half is a map of the bay, the right a list of the nearest yachts from
  AIS data. The map isn't hand-drawn: depths and terrain come from open datasets, the sea is
  coloured by depth and the Esterel hills are shaded. It's all baked into an image in
  advance, so the controller has nothing to calculate.
- **One knob for everything.** A rotary encoder at the bottom of the case. Turn it to change
  the clock style or the airport, or to scroll the yachts; a short press switches mode
  within a page, a long press moves to the next page.
- **Lua for my own effects.** A Lua interpreter already lives in my other projects, and
  that's where I write effects and games. I brought it over and built a simulator so I can
  write effects on the computer without flashing the board. To try it out there's a
  Minecraft-style scene with a full day and night in one minute, a Tetris clock (at each new
  minute the digits burn away like completed lines and are rebuilt by falling pieces) and a
  snake clock whose digits crawl off the bottom and back in from the top
  ([why and how](docs/14-lua.md)).
- **An enclosure.** A white wall-mounted case for 3D printing, with a strip at the bottom
  for the knob, is being designed alongside ([enclosure/](enclosure/)).

### Where things stand

The code is written, it compiles and it runs in the simulator, but nothing has been tested
on hardware yet — the panels are still on their way. The [bring-up plan](docs/12-bringup.md)
goes step by step: the controller with no panels first, then one panel to settle the driver
question, then two, and only then the features one at a time. The big open question is
whether there's enough fast memory for both the picture and Lua. Only a real board will
tell.

When they arrive, I'll write up what worked first time and what didn't.

## Quick start

If the hardware has not been powered up yet, read in this order:

1. [The panel](docs/01-panel.md) — specs, pinout, what GOB actually gives you
2. [The controller](docs/02-controller.md) — **the verified pin map**, peripherals, power
3. [Best practices](docs/04-best-practices.md) — **read this before first power-on**
4. [Firmware](docs/03-firmware.md) — pick a path and get something on screen

## Contents

| Document | Covers |
|---|---|
| [01-panel.md](docs/01-panel.md) | RGB-Matrix-P2-64x64-B: specifications, HUB75 pinout, GOB coating, box contents |
| [02-controller.md](docs/02-controller.md) | ESP32-S3-RGB-Matrix: SoC, memory, power budget, **complete verified pin map** |
| [03-firmware.md](docs/03-firmware.md) | WLED, ESPHome, ESP-IDF, Arduino — what to choose and how to install |
| [04-best-practices.md](docs/04-best-practices.md) | Power, ghosting, flicker, brightness, memory, wiring |
| [05-troubleshooting.md](docs/05-troubleshooting.md) | Symptom → cause → fix |
| [06-projects.md](docs/06-projects.md) | Community projects worth building on |
| [07-sources.md](docs/07-sources.md) | Every source, every contradiction found, what is still unverified |
| [08-apollo-m1-comparison.md](docs/08-apollo-m1-comparison.md) | How this hardware compares to the Apollo Automation M-1 |
| [09-upstream-contributions.md](docs/09-upstream-contributions.md) | Roadmap for contributing this board back to the AnimatedPixelClock project |
| [10-mechanical.md](docs/10-mechanical.md) | Mechanical facts read out of the factory drawing |
| [11-control-and-pins.md](docs/11-control-and-pins.md) | The GPIO budget from the schematic, the encoder and its gestures |
| [12-bringup.md](docs/12-bringup.md) | Gated bring-up: from the box to a working panel |
| [13-code-practices.md](docs/13-code-practices.md) | AnimatedPixelClock's network stack and guards, read against NickoScope32 |
| [14-lua.md](docs/14-lua.md) | Putting a Lua interpreter on this panel, from our three existing ones |
| [15-ulanzi-awtrix.md](docs/15-ulanzi-awtrix.md) | What the Ulanzi pixel clocks and the AWTRIX firmware got right, and what to borrow |

## Ready-to-use configs

| File | Purpose |
|---|---|
| [configs/esphome/waveshare-matrix.yaml](configs/esphome/waveshare-matrix.yaml) | Minimal ESPHome config: one 64x64 panel, onboard sensors, brightness entity |
| [configs/arduino/smoke_test/smoke_test.ino](configs/arduino/smoke_test/smoke_test.ino) | Smoke test: prove the panel is alive before building anything around it |

Pin assignments in both files are verified. **Neither config has been compiled or flashed**,
so treat them as reviewed drafts rather than tested artifacts.

## The one thing worth knowing up front

Waveshare laid this board out on the **default ESP32-S3 pinout of the
`mrcodetastic/ESP32-HUB75-MatrixPanel-DMA` library**. Thirteen of fourteen pins match
upstream exactly. The single difference is pin E, which upstream leaves unassigned
(`-1`) because only 1/32-scan panels need it, and which Waveshare routed to GPIO9.

Practically: any sketch built on that library runs on this board with no pin configuration
at all. One line is enough.

```cpp
mxconfig.gpio.e = 9;
```

## Enclosure

An open design for a 128 x 64 wall panel built from two of these matrices lives in
[enclosure/](enclosure/): the design brief, three front-composition options and the split
scheme. The mechanical constraints behind it come out of the factory drawing —
[docs/10-mechanical.md](docs/10-mechanical.md).

## Code practices

[13-code-practices.md](docs/13-code-practices.md) — a read of AnimatedPixelClock's
network stack and compile-time guards, checked line by line against NickoScope32 V1b.
Most of it turned out to be already there; the two genuine gaps are named.

## Lua scripting

[14-lua.md](docs/14-lua.md) — what our three existing Lua implementations (H743,
Main-S3, Watch) teach about putting an interpreter on this panel, the safety
architecture worth copying verbatim, and the one risk that is ours alone.

## Bring-up

[12-bringup.md](docs/12-bringup.md) — the gated sequence from the box to a working
panel, and which of the ten open questions each phase settles. Read it before
the panels are unpacked.

## Physical control

[11-control-and-pins.md](docs/11-control-and-pins.md) — the GPIO budget from the
schematic (the header has two GPIOs, and that is all), why the encoder switch shares the
BOOT button, and the gesture map.

## Flight board simulation

Lives with the firmware, not here:
[NickoScope/AnimatedPixelClock](https://github.com/NickoScope/AnimatedPixelClock/tree/board/waveshare-esp32-s3-rgb-matrix/sim),
branch `board/waveshare-esp32-s3-rgb-matrix`, directory `sim/`.

## Fact-checking convention

| Marker | Meaning |
|---|---|
| unmarked | verified against a primary source, cited in 07-sources.md |
| FYI | secondary source or industry practice — must not drive decisions |
| UNVERIFIED | taken from a third-party config or a blog, needs checking against hardware |
