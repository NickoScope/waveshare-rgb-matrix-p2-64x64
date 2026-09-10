# Bring-up: from the box to a working panel

Ordered, gated. Each step has a pass criterion and a single thing it proves. Do
not skip forward: with two panels and an unresolved driver chip, a black screen
has four possible causes and no way to tell them apart.

Everything below is **untested** — it is a plan written from the datasheets and
the vendor sources, not a log of what happened. Fill in results as you go.

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
| 8 | The two enclosure measurements | The 3D session is waiting on them | 7 |

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
- Check the ribbon orientation against the keying before pushing it home.

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
5. Only then suspect the pin map. It was verified against three independent
   vendor sources ([02](02-controller.md)), so it is the least likely cause.

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

**Gate:** a stable clock for ten minutes with no reboot.

---

## Phase 5 — the encoder

**Goal:** question 4, and the gesture map.

Wire A → **GPIO45** (header U8 pin 1), B → **GPIO46** (pin 2), common → GND
(pin 3). The switch has no header pin: solder it to the **BOOT button pad**,
in parallel with the button.

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

**Test the ugly cases deliberately**, because they are what the audit was about:

- broker unreachable → the page should say so and the board must **not** reboot
- Wi-Fi dropped mid-session → recovery without a reset
- wrong AIS key → must not become a five-second reconnect loop

**Gate:** both pages populated, and no reboot in any of the three failure tests.

---

## Phase 7 — the measurements the enclosure is waiting for

The 3D session has a measurement protocol and cannot finalise depth without
real numbers. Do this **before** anything goes into a case, with the panels
still accessible.

Measure and report: the assembled panel-plus-controller depth stack, and the
actual seam gap between two mounted panels. The enclosure is currently working
to 30 mm and will freeze only once these land.

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
| Anything surprising | [05](05-troubleshooting.md) |
