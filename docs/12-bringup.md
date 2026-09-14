# Bring-up: from the box to a working panel

Ordered, gated. Each step has a pass criterion and a single thing it proves. Do
not skip forward: with two panels and an unresolved driver chip, a black screen
has four possible causes and no way to tell them apart.

Everything below is **untested** — it is a plan written from the datasheets and
the vendor sources, not a log of what happened. Fill in results as you go.

## What is on the board by now

Built and pushed, none of it hardware-verified. Flash 1 764 213 of 6 553 600 —
**26.9 %**, so nothing here is constrained by space.

| | Flag | Cost |
|---|---|---|
| Flight board, fed over MQTT | `FLIGHTBOARD_ENABLED` `FB_MQTT_ENABLED` | 7.4 KB |
| Yacht radar, AIS over TLS | `YACHTRADAR_ENABLED` | 31.1 KB |
| Encoder and page dispatch | `CONTROL_ENCODER_ENABLED` | 3.4 KB |
| Lua 5.4.8, boot self-test only | `NSLUA_ENABLED` | 91 KB |
| Cards, notifications, icons, carousel | `MQTT_BUS_ENABLED` `CARDS_ENABLED` `CAROUSEL_ENABLED` | 8.4 KB |
| World clock, the page after the clock | `WORLDCLOCK_ENABLED` | 2.3 KB flash, 4.1 KB RAM |

Three things are **not** built and will not be tested: the pages have no HTTP
route or button, only the knob; the Lua runtime is not connected to the
display at all — it runs one self-test at boot and nothing else, so the
simulator's effects (Tetris and snake clocks, Minecraft, the room radar) are
not on the panel; and presence from the Apollo MTR-1 has no firmware yet —
phase 6e says what to do before it does.

Before flashing anything, run `python3 tools/flag_matrix.py` in the firmware
repo. It builds fourteen flag combinations, asserts that four of them are
*refused* by the dependency guards, and then builds the `provision` and
bring-up images. Those two were added after the bring-up image had silently
stopped linking — found on 2026-09-14, the day the hardware arrived. It exists because the obvious way to check
this silently reported success for builds that never ran.

## Before the boxes are opened

Have these to hand, because stopping mid-phase to find one is how a bring-up
turns into an evening:

- a 5 V supply rated from the **recommendation**: 8 A for two panels
- a multimeter — three separate measurements below need one
- an EC11 encoder, and something to solder with, for the BOOT pad
- the MQTT broker's host, user and password, and the AIS key, for `provision`
- a USB-C cable that carries data, not only power
- `espefuse.py`, for one read in phase 5. It ships with PlatformIO's esptool
  package (`~/.platformio/packages/tool-esptoolpy/`), and Homebrew has it too
- for phase 6e: the **Apollo MTR-1**, admin access to Home Assistant, and
  `mosquitto_sub` on the Mac

## Open these first

Both live in [`reference-drawings/controller/`](../reference-drawings/):

| Drawing | What you will need it for |
|---|---|
| `ESP32-S3-RGB-Matrix-Schematics.pdf` | the pin-assignment table (top right), connector J1, the two buffers, the power path |
| `ESP32-S3-RGB-Matrix-2D.pdf` | board outline and mounting, for phase 7 |

There is **no schematic for the panel** and that is not an oversight — see the
[drawings README](../reference-drawings/README.md) for where that was searched.

What the schematic already settles, so you do not measure it:

- **Header U8 is `1 = IO45, 2 = IO46, 3 = GND, 4 = 3V3`.** Four pins, and that is
  the entire expansion budget.
- **J1, the HUB75 output, is a keyed 2×8 header at 2.54 mm.** Keyed, so it only
  goes in one way — but the ribbon can still be reversed end for end.
- **The signals are level-shifted by two SN74HC245DBR** (U11, U12), and those
  buffers run from **USB_5V**. The HUB75 logic level therefore follows the
  board's own 5 V rail, not its 3.3 V one. This matters in phase 2.
- **The board's 5 V has two entrances that are the same net:** the USB-C
  connector and the M3 screw posts H2/H3 in `Screen_Power`. Nothing on the
  drawing ORs or diode-isolates them, so feeding both at once back-feeds one
  into the other. Pick one.
- **The board has two USB-C sockets, silkscreened USB and POWER** (seen on the
  hardware, 2026-09-14). Which of them shares the USB_5V net with the posts has
  not been traced. Until it is: one USB-C at a time, and flash through **USB**.
- 3V3 comes from an **MP1605GTF-Z** buck; C27 is a convenient place to measure it.

---

## What this is meant to settle

Fifteen questions are open; 3, 4 and 4b are answered. The phase that answers each is in the last column.

| # | Question | Why it is still open | Phase |
|---|---|---|---|
| 1 | `FM6126A` or `GENERIC` shift driver | **The chips say FM6124HJ** (read off the panels 2026-09-14), and the library gives FM6124 and FM6126A the same init. Test A confirms it on screen — [07](07-sources.md) #4 | 2 |
| 2 | `clkphase = false`? | Fixes a dropped rightmost column on some batches | 2 |
| 3 | ~~Does USB-CDC enumerate?~~ **Yes, on the board, 2026-09-14.** The USB socket shows up as Espressif's USB JTAG/serial (303A:1001), esptool flashes through it, and `Serial` prints over it | — | 1 ✓ |
| 4 | ~~Are GPIO10/13 on the header?~~ **Answered from the schematic: no.** Header U8 is IO45, IO46, GND, 3V3 | IO10 is RTC_INT, IO13 is IMU_INT. Encoder moved to 45/46 — see [11](11-control-and-pins.md) | — |
| 4b | ~~Does the GPIO45 strap matter?~~ **Answered from the WROOM-2 datasheet: no.** VDD_SPI on the S3R16V is fixed at 1.8 V by eFuse | **Confirmed on the board 2026-09-14:** `VDD_SPI_FORCE = True`, VDD_SPI on the 1.8 V LDO | 1 ✓ |
| 5 | `mic_power_rail` on GPIO46 | In hub75-studio, absent from the vendor BSP | 1 |
| 6 | Do GPIO47/48 run at 1.8 V? | VDD_SPI is 1.8 V on this module (WROOM-2 datasheet §8); whether 47/48 follow it is what is open. That is this board's I2C bus | 1 |
| 7 | TLS session heap for the AIS websocket | Allocated at runtime, never measured | 6 |
| 9 | **Can a Lua heap share PSRAM with the HUB75 DMA?** | Both want the same bandwidth-limited memory. Never measured | 6b |
| 10 | Do the two watchdog fixes hold? | Written by hand after an audit, never run on hardware | 6 |
| 8 | The two enclosure measurements | The 3D session is waiting on them | 7 |
| 11 | Do cards and notifications render as drawn? | The protocol round-trips on the live broker; the layout has only been drawn on the host | 6c |
| 12 | Does the icon store survive a power cut? | Atomic write and rename, never tested against a real yank of the cable | 6c |
| 13 | Does the world clock's night line match the real sky? | The C module matches the Lua prototype pixel for pixel on the host; neither has seen NTP time on the board | 6d |
| 14 | Does presence reach the panel and put it to sleep and wake it correctly? | Nothing written yet: neither the Home Assistant automation nor `src/presence/` | 6e |
| 15 | Does the LD2450 keep a person who sits perfectly still? | Not in any source read; the radar reports still targets, but for how long is unknown | 6e |
| 16 | Does the running panel disturb the radar? | A HUB75 panel is a large, fast-switching load next to a 24 GHz sensor. Never tried | 6e |
| 17 | Can the MTR-1 send its targets ten times a second over MQTT? | Stock firmware throttles to once a second and has no `mqtt:`; the override syntax is not verified | 6e |

---

## Phase 0 — before any power

**Goal:** do not destroy anything in the first thirty seconds.

- Inspect all four panels. Waveshare warns that **silkscreen and layout vary
  between production batches**. Photograph each board's markings; if the four
  are not from one batch, note which is which before anything goes in a case.
- Identify JIN (from controller) and JOUT (to next panel) on every panel. They
  are not interchangeable and the connectors do not stop you.
- Size the supply from the **recommendation, not the table**: Waveshare states
  3 A in the specs and 4 A in the supply advice. Two panels = 5 V 8 A.
  Power reaches each panel through its own VH4 socket; it does **not** chain.
- Check the ribbon orientation against the keying before pushing it home. J1 is
  keyed, but a 16-way ribbon reversed end for end still seats.
- Decide **now** which 5 V entrance you will use — USB-C or the M3 screw posts.
  They are the same net on the schematic. Not both.

**Gate:** connectors identified, supply rated, batches recorded.

---

## Phase 1 — the controller alone, no panel attached

**Goal:** prove the board enumerates and can be flashed at all, while a mistake
still costs nothing.

```bash
cd ~/AnimatedPixelClock
pio run -e provision -t upload     # no -DPROV_* flags: it will just report
```

**Pass:** the port appears, upload completes, and the serial monitor prints the
provisioning banner.

**If the port never appears** — that is question 3 answered the hard way. The
board has no UART bridge, so the fallback is the ROM download mode: hold BOOT
(GPIO0) while plugging USB. If that also fails, drop
`-DARDUINO_USB_MODE=1 -DARDUINO_USB_CDC_ON_BOOT=1` and reflash over the ROM
loader.

While here, with no panel connected and nothing to damage:

- **Question 5**, `mic_power_rail`: read GPIO46 at boot and after; compare with
  microphone behaviour later. Cheap to check now, awkward later.
- **Question 6**, the 1.8 V I2C: measure the idle voltage on GPIO47/48 with a
  meter. 3.3 V or 1.8 V is a five-second measurement that decides whether
  anything can ever be added to that bus.
- **The two rails**, while a meter is already out: 3V3 at C27 (buck output) and
  5 V at the buffer supply pin of U11 or U12. The second one is the number that
  decides the HUB75 signal level, so it is worth knowing before a panel is
  attached rather than after a bad picture.

**Gate:** the board flashes and re-flashes reliably. Do not proceed otherwise —
every later step assumes you can iterate.

### Result — 2026-09-14

**Passed, after one fix.**

- esptool: ESP32-S3 (QFN56) rev v0.2, 40 MHz crystal, 32 MB flash, "Embedded
  PSRAM 16MB (AP_1v8)". The module is marked `MCN32R16V`.
- eFuse: `VDD_SPI_FORCE = True`, VDD_SPI on the 1.8 V LDO — question 4b confirmed.
- **The first image boot-looped.** Every boot ended in
  `assert failed: do_core_init startup.c:328 (flash_ret == ESP_OK)` right after
  `Octal Flash Mode Enabled`. The env had `memory_type = qio_opi` — quad flash,
  octal PSRAM — and this module's flash is octal too. Fixed to `opi_opi` in the
  fork; `provision` then boots and prints its report over USB (question 3).
- **A boot-looping board drops off USB too often for a normal upload** ("No
  serial data received"). `esptool.py --port <port> --after no_reset
  --connect-attempts 15 chip_id` caught it and left it in the bootloader, and
  the upload went through straight after. Holding BOOT while plugging in is the
  manual way.
- The header silkscreen reads GND, 3V3, IO46, IO45 — the schematic's U8 order.
- Photos of the controller and panels as they arrived:
  [photos/2026-09-14-arrival](../photos/2026-09-14-arrival/README.md).
- The two rails, by the owner's meter: about 5 V between the 5V and GND posts,
  about 3.3 V on the header's 3V3. As expected; exact figures not recorded.
- Not yet measured: question 5 (GPIO46) and question 6 (GPIO47/48).

---

## Phase 2 — ONE panel

**Goal:** settle the driver chip. This is the phase that matters most.

Connect a **single** panel to the controller. In `bringup/hello_matrix.cpp` set
`PANELS = 1`. This is deliberate: with two panels a blank screen could be panel
one, panel two, the ribbon, the chain, the driver init or the pin map, and
nothing distinguishes them.

```bash
pio run -e matrix-waveshare-rgb-bringup -t upload
```

**Test A — driver chip (question 1).** Flash once with `USE_FM6126A` on and once
with it off. Our panels' column drivers are marked `FM6124HJ`, which the library
initialises through the same routine as FM6126A — so expect the picture with it
**on**, and treat *off* as the comparison.

**Power the panel before the controller boots.** The library writes the driver
registers once, in `shiftDriver()`, before DMA starts; a panel that gets power
afterwards has missed them. If in doubt, press RESET on the controller.

| What you see | Conclusion |
|---|---|
| Image only with FM6126A | It is FM6126A. Set `cfg.driver` and record it |
| Image both ways | It is GENERIC-compatible; prefer GENERIC — fewer init writes |
| Image neither way | Not the driver. Go to the black-screen ladder below |

**Test B — clock phase (question 2).** Look at the **rightmost column**. If it
is missing or smeared, set `cfg.clkphase = false` and reflash. Note that
ghosting and a dropped column look similar; the column is a phase problem, a
general haze is brightness or signal.

**Test C — colour order.** Red, green and blue full-screen in turn. Wrong order
is a swapped pair in the pin map, not a panel fault.

**Test D — geometry.** A single-pixel border and a diagonal. Rows appearing in
the wrong order means the E line is wrong — this panel is 64 rows at 1/32 scan
and **E is mandatory**.

### If the screen is dead black

In this order, one change at a time:

1. Power. Measure 5 V **at the panel's VH4**, under load, not at the supply.
2. Ribbon reversed or in JOUT rather than JIN.
3. Toggle `USE_FM6126A`.
4. Brightness — start low, but not zero.
5. **The buffer supply.** U11 and U12 run from USB_5V, so if that rail is low —
   a thin cable, a shared supply sagging under the panels — the HUB75 signals
   are low with it, and the symptom is a dim, unstable or dead panel that looks
   like a driver or wiring fault. Measure at the buffer, not at the supply.
6. Only then suspect the pin map. It was verified against three independent
   vendor code sources **and** the schematic's own pin table
   ([02](02-controller.md)), so it is the least likely cause.

**Gate:** one panel showing correct colours, full geometry and all 64 rows.
Record the driver and clkphase answers in [07](07-sources.md) — contradiction #4
gets closed here.

---

## Phase 3 — two panels chained

**Goal:** prove the chain and find the seam.

Panel 1 JOUT → panel 2 JIN. Restore `PANELS = 2`.

**Test E — the seam.** Draw a horizontal line across the full 128 px and a
vertical line at x = 63 and x = 64. Look for: a gap, a doubled column, or the
right half being a copy of the left (that last one means the chain length is
still 1 in the config).

**Test F — refresh under load.** Full white, then a moving pattern. Flicker
that appears only at full white is the supply sagging, not the panel.

**Gate:** 128 × 64 as one continuous canvas. Photograph the seam — the 3D
session needs to know whether the gap is optical or physical.

---

## Phase 4 — our firmware, offline

**Goal:** prove the render path before adding the network.

```bash
pio run -e matrix-waveshare-rgb -t upload
```

The pages are reachable only through the encoder, so without Phase 5 you will
land on the clock. That is fine — the clock is what proves the render path. The
world clock, flight board and yacht radar all need the network for anything
beyond their empty state.

**Expect:** the clock in whatever style the settings hold. Both halves of the
canvas in use. No tearing on the animated styles.

**Watch for:** the panel freezing rather than going dark. That is the shape a
blocked `loop()` takes — the DMA keeps scanning the last buffer. Today's audit
fixed two such paths, but this is where a third would show.

**The serial log carries the first Lua evidence.** At boot the runtime runs a
self-test and prints one line:

```
[nslua] self-test PASSED
```

`FAILED` with a message means the interpreter is wrong. **`runtime unavailable
(no PSRAM?)`** means `psramFound()` returned false — which would also mean the
HUB75 driver has no PSRAM to put a framebuffer in, so that message is a much
bigger problem than Lua.

**Gate:** a stable clock for ten minutes with no reboot, and the self-test
passing.

---

## Phase 5 — the encoder

**Goal:** question 4, and the gesture map.

Wire A → **GPIO45** (header U8 pin 1), B → **GPIO46** (pin 2), common → GND
(pin 3). Pin 4 is 3V3 if the encoder needs it; ours does not, the internal
pull-ups are enough. The switch has no header pin: solder it to the **BOOT
button pad**, in parallel with the button.

The header's four-pin order is on the schematic in the `GPIO` block, connector
U8 — worth a glance before soldering, because the drawing is the only place it
is written down.

GPIO45 is safe to use. The module datasheet settles it: the ESP32-S3R16V in
the WROOM-2-N32R16V has VDD_SPI fixed at 1.8 V by eFuse, so the GPIO45 strap is
ignored ([11](11-control-and-pins.md) has the sources). A knob could not have
changed the strap anyway: it only ever pulls a pin to ground, which is the
default. Confirm it on the board once — read-only, nothing is burned:

```bash
espefuse.py --port <port> summary | grep -i vdd_spi
```

Expect `VDD_SPI_FORCE = True`. If it says False, stop and ask before wiring
anything to the header. (Earlier versions of this page gave the command as
`esptool.py summary`, which is not an esptool command.)

| Test | Pass |
|---|---|
| Rotate | one style per detent, no skipped or doubled steps |
| Direction | clockwise goes forward. If reversed, swap A and B |
| Short press | jumps to Custom rotation and back |
| Long press, 700 ms | moves to the next page, **while still held** |
| Press BOOT deliberately | should behave as a short press - it shares the pin |
| Hold the knob through a reset | expect download mode. Confirm it recovers |
| Long press through every page | clock → world clock → flight board → yacht radar → any cards → clock |
| Rotate or press on the world clock | nothing happens — the page takes no input, by design |

**Gate:** every page reachable and the knob does not drop detents.

---

## Phase 6 — the network

**Goal:** feed the two data pages, and question 7.

```bash
pio run -e provision -t upload \
  --project-option="build_flags=-DPROV_MQTT_HOST=\"…\" -DPROV_MQTT_USER=\"…\" -DPROV_MQTT_PASS=\"…\" -DPROV_AIS_KEY=\"…\""
pio run -e matrix-waveshare-rgb -t upload
```

**Flight board.** The retained payload should land within milliseconds of
subscribing — verified against the live broker on 2026-09-10, 1060 bytes, 15
flights. If the page says `NO DATA` rather than a reason, the status text is
wrong, not the transport.

**Yacht radar.** Watch the free heap across entering and leaving the page
several times. This is question 7: the TLS session is the largest unmeasured
allocation in the firmware. Heap that does not return on leaving is a leak.

**Test the ugly cases deliberately.** These are not hypothetical: an audit on
2026-09-10 found two paths that blocked `loop()` past the 15 s watchdog, which
`panic=true` turns into a reboot loop rather than a slow page. Both were fixed
by hand and **neither fix has ever run on hardware.** This is the phase that
proves them.

| Do this | Must happen |
|---|---|
| Point the broker at an address that accepts TCP and never answers | `CONNECTING`, then a retry. **No reboot** — this is the `PubSubClient` busy-wait fix |
| Open the radar with the network unplugged | `NO WIFI`, no reboot — this is the TLS-handshake fix |
| Store a wrong AIS key, open the radar, wait a minute | Must not settle into a five-second reconnect loop |
| Pull Wi-Fi mid-session, restore it | Both pages recover without a reset |
| Broker unreachable | The page names the reason rather than saying `NO DATA` |

Watch the reset reason across all of it: `GET /api/diagnostics` reports it, and
a `TG0WDT` or `TG1WDT` there means a watchdog fired and one of the fixes did
not hold.

**Gate:** both pages populated, and **no reboot in any of the five tests**.

---

## Phase 6b — the Lua bench

**Goal:** the one question that decides whether an interpreter belongs on this
board at all, and the reason nothing was built on top of it yet.

The Lua heap allocates from **PSRAM**, and on this board the HUB75 DMA
framebuffer may live there too. PSRAM bandwidth is already the binding
constraint — the driver caps at ~13 MHz because GDMA gets half of it, sharing
round-robin with the CPUs. A script allocating during a frame competes with the
refresh that is lighting the panel.

Nobody has measured this. It is the first thing to measure, before a single
effect is wired to the display.

| Measure | How |
|---|---|
| Baseline refresh | the driver reports its calculated rate at init — write it down |
| Free PSRAM before and after | `ESP.getFreePsram()` around `nslua_run` |
| Flicker under load | run a script that allocates hard — build a large table in a loop — while the clock renders, and **look at the panel** |
| Frame time | how long the clock's render takes with and without a script running |

**If the panel flickers under script load**, in order of preference:

1. Move the Lua heap to internal SRAM. We use 25 % of 320 KB, and the
   allocator is one line in `nslua.cpp` — `MALLOC_CAP_SPIRAM` becomes
   `MALLOC_CAP_INTERNAL`.
2. Or keep the framebuffer in internal SRAM. At 128 × 64 it fits, and PSRAM
   then belongs to Lua alone.

Both cannot have it. Which one wins is a measurement, not an opinion.

**Gate:** a number for each row above, written into `docs/14-lua.md`. A
flickering panel is not a failure of this phase — it is its result.

## Phase 6c — cards, notifications and icons

**Goal:** questions 11 and 12. The wire protocol is already proven against the
live broker; what has never happened is a panel drawing one.

Publish from the Mac with the tools in the firmware repo, or from Home
Assistant — the payloads are the same either way.

| Do this | Expect |
|---|---|
| Publish a card with `title`, `text` and `color` | it appears in the knob's page walk, after the fixed pages |
| Publish one with `progress` | a bar along the bottom, filled to that fraction |
| Publish text far too long for one line | two centred lines, broken at a space — not a clipped line |
| `python3 tools/icon_tool.py publish drop.i16 drop`, then a card with `icon: "drop"` | 16 × 16 picture on the left, text centred in what is left |
| Publish an empty payload to the card topic | the page disappears, and the knob's page count shrinks under you without a crash |
| Publish a card with `lifetime: 30` and then stop | it removes itself half a minute later |
| Publish to `.../notify` with `hold: true` | it takes the whole screen and waits for a press |
| **Pull the power while an icon is being written** | the icon is either the old one or the new one, never half of one. This is what the temp-file-and-rename is for, and it has never been tested |
| Leave the panel alone for a minute | the pages start advancing by themselves; touch the knob and they stop |

**Watch the free heap** across a few dozen card updates. Cards are a fixed
array and icons are one cached buffer, so nothing should grow — if it does, the
JSON parser is holding something.

**Gate:** every row above behaves, and the heap is flat after fifty updates.

## Phase 6d — the world clock

**Goal:** question 13. Needs Wi-Fi for NTP; nothing else.

| Do this | Expect |
|---|---|
| Boot with Wi-Fi off, long press to the page after the clock | an all-night map and `--:--`, not a confident 01:00 in 1970 |
| Let NTP sync | the time appears and the lit half jumps into place within a minute |
| Compare with any live day/night map (timeanddate.com has one) | the night line within one dot, 5.6°, of the reference |
| Watch the six cities | Cannes breathes; Moscow, New York, London, Dubai and Almaty are steady orange 2×2 dots |
| Watch for flicker | none: the page drops to 10 fps, and only the home dot moves between minutes |

**Gate:** the line agrees with the reference at two times of day at least six
hours apart.

## Phase 6e — presence: the Apollo MTR-1

**Goal:** questions 14–17. The MTR-1 is its own box on Wi-Fi — an LD2450
radar on an ESP32-C3 with ESPHome, plus light, CO2 and pressure sensors — and
it needs nothing from the panel's header, so the encoder keeps IO45/IO46. The
plan and its sources are in [16](16-presence-radar.md).

**The firmware for this phase is not written.** The first part needs none, and
it is the part that decides whether the rest is worth writing.

### The MTR-1 alone, in Home Assistant

| Do this | Expect |
|---|---|
| Add it through the ESPHome integration | `LD2450 Presence`, `Presence Target Count`, `Target-1 X`/`Y`, `CO2` and `LTR390 Light` appear |
| Set the `LTR390 Update Interval` number | `LTR390 Light` starts reporting. Its polling is off in the stock config |
| Walk in and out of the fan | presence follows within about a second — the stock throttle is one update a second |
| **Sit perfectly still for five minutes** (Q15) | presence stays on. If it drops, sleep needs a longer hold-off, or the idea needs rethinking |
| Stand behind the MTR-1, then in the next room | how much it sees behind itself and through the wall. Hi-Link warns it does. This decides where it may hang |
| Hang it where it will live, next to the running panel; compare the panel on full white with the panel off (Q16) | no ghost targets, and presence does not flap when the panel changes |

### Stage 1 — presence drives the panel (Q14)

Needs two things that do not exist yet: a Home Assistant automation that
republishes presence, target count, motion and lux to `nickoscope_matrix/presence`
(retained), and `src/presence/` in the firmware.

| Do this | Expect |
|---|---|
| `mosquitto_sub -v -t 'nickoscope_matrix/presence'`, then walk in | a retained message with present, count, moving and lux |
| Leave the room | the panel dims after the hold-off — not the moment the radar loses you |
| Walk back in | full brightness again within a couple of seconds |
| Stay out while the carousel is running | it stops advancing |
| Darken the room, then light it | brightness follows the light sensor without visible steps |
| **Stop Home Assistant** | the panel stays awake. No data must mean awake, never asleep |
| Optional: publish a card to `nickoscope_matrix/card/air` from an automation on `CO2` | the card appears — this needs no new firmware, cards already work |

**Gate for stage 1:** a whole day with the panel sleeping and waking on its own,
and not one false sleep while somebody is in the room.

### Stage 2 — the live room radar (Q17)

Needs the MTR-1 adopted in the ESPHome dashboard with an `mqtt:` package that
publishes the three targets, the throttle lifted on those sensors, and the room
radar reaching the panel. That last part is a Lua script today, so it waits on
phase 6b and on the runtime being connected to the display — or on a C port,
as the world clock got.

| Measure | Pass |
|---|---|
| Messages a second on the targets topic | about ten, the radar's own rate |
| Home Assistant after the `mqtt:` package goes in | every entity still there; the native API is untouched |
| MTR-1 uptime across a day | no reboot every fifteen minutes. ESPHome's docs warn of exactly that when MQTT runs **without** the native API |
| Walk a line across the fan | the blip on the panel follows you, and its trail is where you walked |

**Gate for stage 2:** set when it is built.

## Phase 7 — the measurements the enclosure is waiting for

The 3D session has a measurement protocol and cannot finalise depth without
real numbers. Do this **before** anything goes into a case, with the panels
still accessible.

**The controller half is already known** — from `ESP32-S3-RGB-Matrix-2D.pdf`,
and it does not need the hardware in hand:

| | |
|---|---|
| Board | 50.01 × 42 mm, corner radius R2 |
| PCB | 1.6 mm |
| Tallest side | 8.5 mm |
| Opposite side | 5.6 mm |
| Mounting | 2 × M2.5, centres 42.54 mm apart |

So what still has to be measured is only what the drawing cannot say: **the
assembled panel-plus-controller depth stack** once the ribbon and its bend are
real, and **the actual seam gap** between two mounted panels. The enclosure is
working to 30 mm and freezes only once those two land.

---

## Phase 8 — soak

Twenty-four hours on the clock page, then twenty-four with the encoder cycling
pages, then — once stage 1 of phase 6e exists — twenty-four with presence
putting the panel to sleep and waking it. Record: reboots, heap at start and
end, whether the image degrades, and every false sleep.

The library silently trades colour depth for refresh rate; if the picture looks
poorer than on day one, that is where to look first.

**Gate:** no reboots, heap flat.

---

## Recording results

Every answer above belongs back in this repository, not in a chat log:

| Answer | Goes to |
|---|---|
| Driver chip, clkphase | [07](07-sources.md), close contradiction #4 |
| GPIO46, GPIO47/48, header pins | [02](02-controller.md), [11](11-control-and-pins.md) |
| TLS heap | `src/yachtradar/README.md` in the firmware repo |
| Depth and seam | the enclosure's measurement protocol |
| PSRAM contention, refresh rates | [14](14-lua.md), and the allocator decision into the firmware |
| Watchdog behaviour under the five failure tests | [05](05-troubleshooting.md) |
| `VDD_SPI_FORCE` as read off the board | [11](11-control-and-pins.md) |
| Still person, behind the wall, next to the panel, 10 Hz over MQTT | [16](16-presence-radar.md) |
| Anything surprising | [05](05-troubleshooting.md) |
