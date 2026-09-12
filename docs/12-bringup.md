# Bring-up: from the box to a working panel

Ordered, gated. Each step has a pass criterion and a single thing it proves. Do
not skip forward: with two panels and an unresolved driver chip, a black screen
has four possible causes and no way to tell them apart.

Everything below is **untested** — it is a plan written from the datasheets and
the vendor sources, not a log of what happened. Fill in results as you go.

## What is on the board by now

Built and pushed, none of it hardware-verified. Flash 1 753 541 of 6 553 600 —
**26.8 %**, so nothing here is constrained by space.

| | Flag | Cost |
|---|---|---|
| Flight board, fed over MQTT | `FLIGHTBOARD_ENABLED` `FB_MQTT_ENABLED` | 7.4 KB |
| Yacht radar, AIS over TLS | `YACHTRADAR_ENABLED` | 31.1 KB |
| Encoder and page dispatch | `CONTROL_ENCODER_ENABLED` | 3.4 KB |
| Lua 5.4.8, boot self-test only | `NSLUA_ENABLED` | 91 KB |
| Cards, notifications, icons, carousel | `MQTT_BUS_ENABLED` `CARDS_ENABLED` `CAROUSEL_ENABLED` | 8.4 KB |

Two things are **not** built and will not be tested: the pages have no HTTP
route or button, only the knob; and the Lua runtime is not connected to the
display at all — it runs one self-test at boot and nothing else.

Before flashing anything, run `python3 tools/flag_matrix.py` in the firmware
repo. It builds twelve flag combinations and asserts that three of them are
*refused* by the dependency guards. It exists because the obvious way to check
this silently reported success for builds that never ran.

## Before the boxes are opened

Have these to hand, because stopping mid-phase to find one is how a bring-up
turns into an evening:

- a 5 V supply rated from the **recommendation**: 8 A for two panels
- a multimeter — three separate measurements below need one
- an EC11 encoder, and something to solder with, for the BOOT pad
- the MQTT broker's host, user and password, and the AIS key, for `provision`
- a USB-C cable that carries data, not only power

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
- 3V3 comes from an **MP1605GTF-Z** buck; C27 is a convenient place to measure it.

---

## What this is meant to settle

Eight questions are open. The phase that answers each is in the last column.

| # | Question | Why it is still open | Phase |
|---|---|---|---|
| 1 | `FM6126A` or `GENERIC` shift driver | Sources disagree; the balance moved to FM6126A but it is not proof. Contradiction #4 in [07](07-sources.md) | 2 |
| 2 | `clkphase = false`? | Fixes a dropped rightmost column on some batches | 2 |
| 3 | Does USB-CDC enumerate? | No UART bridge on this board; marked UNVERIFIED in `platformio.ini` | 1 |
| 4 | ~~Are GPIO10/13 on the header?~~ **Answered from the schematic: no.** Header U8 is IO45, IO46, GND, 3V3 | IO10 is RTC_INT, IO13 is IMU_INT. Encoder moved to 45/46 — see [11](11-control-and-pins.md) | — |
| 5 | `mic_power_rail` on GPIO46 | In hub75-studio, absent from the vendor BSP | 1 |
| 6 | Do GPIO47/48 run at 1.8 V? | R16V parts set VDD_SPI to 1.8 V. That is this board's I2C bus | 1 |
| 7 | TLS session heap for the AIS websocket | Allocated at runtime, never measured | 6 |
| 9 | **Can a Lua heap share PSRAM with the HUB75 DMA?** | Both want the same bandwidth-limited memory. Never measured | 6b |
| 10 | Do the two watchdog fixes hold? | Written by hand after an audit, never run on hardware | 6 |
| 8 | The two enclosure measurements | The 3D session is waiting on them | 7 |
| 11 | Do cards and notifications render as drawn? | The protocol round-trips on the live broker; the layout has only been drawn on the host | 6c |
| 12 | Does the icon store survive a power cut? | Atomic write and rename, never tested against a real yank of the cable | 6c |

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
with it off.

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

**Goal:** see the three pages before adding the network.

```bash
pio run -e matrix-waveshare-rgb -t upload
```

The pages are reachable only through the encoder, so without Phase 5 you will
land on the clock. That is fine — the clock is what proves the render path.

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

Before that, one measurement decides whether GPIO45 is safe to drive at all:

```bash
esptool.py --port <port> summary | grep -i vdd_spi
```

If `VDD_SPI_FORCE` is burned, the GPIO45 strap no longer selects the flash
voltage and the pin is free. If it is not burned, do **not** put an encoder on
it — a knob left in the wrong position at power-up would set VDD_SPI wrongly
and the board would not come up.

| Test | Pass |
|---|---|
| Rotate | one style per detent, no skipped or doubled steps |
| Direction | clockwise goes forward. If reversed, swap A and B |
| Short press | jumps to Custom rotation and back |
| Long press, 700 ms | moves to the next page, **while still held** |
| Press BOOT deliberately | should behave as a short press - it shares the pin |
| Hold the knob through a reset | expect download mode. Confirm it recovers |

**Gate:** all three pages reachable and the knob does not drop detents.

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
pages. Record: reboots, heap at start and end, and whether the image degrades.

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
| Anything surprising | [05](05-troubleshooting.md) |
