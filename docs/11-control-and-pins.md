# Physical control, and the pins left to do it with

## The budget

**Corrected 2026-09-10 from the vendor schematic.** The first version of this
page counted pins the firmware did not use and called the leftovers free. That
was wrong in the way counting always is when the drawing is available and you
did not open it.

The expansion header **U8 is four pins: IO45, IO46, GND, 3V3.** That is the
entire budget for anything added to this board.

| | Count | Which |
|---|---|---|
| Taken by the board | 29 | HUB75 (14), I2S (6), I2C (2), SD (4), BOOT (1), RTC_INT (1), IMU_INT (1) |
| Blocked by the chip | 14 | GPIO26–32 flash/PSRAM; GPIO33–37 octal PSRAM; GPIO19–20 USB |
| **On the header** | **2** | **GPIO45, GPIO46** |

Two pins that a firmware grep reports as free are not: the vendor pin table
assigns **IO10 to RTC_INT** and **IO13 to IMU_INT**, for the PCF85063 alarm and
the QMI8658 interrupt. Neither reaches the header. Using them means giving up
those interrupts and soldering to the module.

Both header pins are strapping pins, and both are survivable:

- **GPIO45** selects VDD_SPI voltage on a bare chip, and **not on this module.**
  The WROOM-2 datasheet (§1.2, §8) puts an ESP32-S3R16V in the N32R16V and says
  its VDD_SPI is set to 1.8 V by eFuse; the ESP32-S3 hardware design guidelines
  say GPIO45 then no longer affects VDD_SPI. Its level at reset does not matter,
  whatever is wired to it. **Documented, not yet read off our board:**
  `espefuse.py summary` is read-only and should show `VDD_SPI_FORCE = True`.
  (Settled 2026-09-14 from the module datasheet; before that this line said
  UNVERIFIED.)
- **GPIO46** gates ROM message printing at boot, and together with GPIO0 picks
  the boot mode: normal boot ignores it, but download mode needs it low or
  floating (esptool, *Boot Mode Selection*). So anything that holds it high at
  reset stops "hold BOOT through reset" from working, and nothing else.
- **Both carry 10 kΩ pull-downs on the board** (schematic R59 on IO45, R60 on
  IO46; the pull-up positions R57 and R58 are not fitted). An internal pull-up
  loses to them, so anything on these pins must drive them *up*: a knob's common
  goes to 3V3, not GND, and the firmware reads A and B active-high. Found on the
  bench on 2026-09-14, when a knob wired common-to-GND read 0 on both lines at
  rest and gave no steps.

That Waveshare chose exactly these two for the header is itself evidence: they
are the pins the board has left.

Sources: `reference-drawings/controller/ESP32-S3-RGB-Matrix-Schematics.pdf` —
its pin-assignment table and the U8 connector — plus the *ESP32-S3 Datasheet*
§2.3.4–2.3.5 for the chip-level restrictions.

**FYI, still to check:** the WROOM-1 datasheet notes that on R16V parts VDD_SPI
is 1.8 V and **GPIO47/48 run at 1.8 V** with it. Those two are this board's I2C
bus. Confirm against the WROOM-2 datasheet before hanging a 3.3 V part on it.

## One more input: an IR receiver (2026-09-14)

The owner wants an IR receiver, which needs one GPIO. The vendor pin table
assigns every GPIO the board brings out, so a pin can only be taken from a
function this firmware does not use.

Checked on the vendor schematic in `reference-drawings/controller/`. The
schematic has the pin table, the RTC, IMU and SD_CARD blocks, and the module
pinout, where bottom-edge pads 15–26 are IO3, IO46, IO9, IO10, IO11, IO12,
IO13, IO14, IO21, IO47, IO48, IO45.

| Pin | Today | Verdict |
|---|---|---|
| **IO14** (module pad 22) | `SD_CS`. Runs through **R47 (0 Ω)** to the TF socket's pin 2 CD/D3; **R41 10 k** pulls that line up on the socket side | **Best.** The card runs in 1-bit MMC on IO1/44/17 and never uses CS. Not a strapping pin, not flash or PSRAM. **Remove R47** and IO14 is free while the card keeps its D3 pull-up. Solder the receiver to R47's module-side pad, or to module pad 22 |
| **IO10** (module pad 18) | `RTC_INT` from PCF85063ATL pin 4 | **Good second choice.** The NXP datasheet (Rev. 7.3, Table 3) makes INT an *open-drain* output, so a receiver can share the line while the RTC's interrupts stay off; the firmware clears them at boot. The RTC is a DFN2626, so the joint has to be on the module pad |
| IO13 (module pad 21) | `IMU_INT` from QMI8658 INT1 | **Avoid.** The QMI8658C's INT pins are push-pull and low by default; the A and B variants start high-Z. Which variant is fitted is not known |
| IO0 | BOOT, and the knob's switch | taken |
| IO45/46 | header, encoder A/B | taken |

**Why not leave R47 in:** with R47 fitted, the receiver would also drive the
card's D3. After the card is up that does nothing, but a remote pressed while
the card initialises (CMD0) holds D3 low, which asks the card for SPI mode. The
mount would then fail. Taking R47 out removes that case.

**Finding R47 on the board:** the silkscreen has no designators. In continuity
mode, one end of the 0 Ω part beside the TF slot rings to the socket's pin 2
(CD/D3), and its other end rings to module pad 22.

**Wiring:**
- receiver VCC to the header's 3V3 and GND to its GND;
- OUT to IO14, with the ESP's internal pull-up on;
- choose a receiver rated for 3.3 V supply.

**Firmware, not built yet:** RMT receive on GPIO14. SD code must never touch
GPIO14 (the clip-gallery helper has been told).

**Not verified:**
- that R47 is the part the continuity test finds;
- the fitted QMI8658 variant;
- anything on hardware.

## The encoder needs three pins and the header has two

| | How | Cost |
|---|---|---|
| **A=45, B=46, SW on GPIO0** (chosen) | both header pins for the quadrature, the switch wired to the BOOT button pad | The switch is a solder joint, not a header pin. A knob held through reset enters download mode and recovers on the next one — and flashes the board without opening the case |
| Give up an interrupt | SW on IO10 or IO13 | Costs the RTC alarm or the IMU interrupt, and still needs soldering to the module |
| I2C expander | on the existing bus | An extra part, and the 1.8 V question above must be settled first |

Pressing BOOT during normal operation now registers as a short press, so it
changes the clock style, the board direction or the sort order depending on the
page — and queues a deferred NVS write. That is a consequence of sharing, not a
bug, but it is worth knowing before someone pokes the button to see what it does.

## Gestures

| Gesture | Meaning |
|---|---|
| Rotate | change the value this page is about |
| Short press | toggle this page's second axis |
| Long press (700 ms) | go to the next page |

| Page | Rotate | Short press |
|---|---|---|
| Clock | step through all 15 styles | Custom rotation ⇄ the style you were on |
| Flight board | step through the six whitelisted airports | arrivals ⇄ departures |
| Yacht radar | scroll the vessel table | sort by range ⇄ by size |

### The clock styles are a generated list, not a range

`settings.clockStyle` runs 0–16 but the valid set is neither contiguous nor in
numeric order: **4** is a legacy alias of 3 and is not offered, **13** was
retired (Missile Command), and **9**, Custom rotation, sits last in the UI
rather than between 8 and 10.

So the knob does not iterate a range. `tools/clock_styles_gen.py` reads the
`<option>` block out of the firmware's own web page and generates the table,
which makes the browser and the knob incapable of disagreeing. A pre-commit
check regenerates and refuses the commit if it went stale.

Order as generated: Mario, Standard, Large, Space Invaders, Arkanoid, Pac-Man,
Snake, Tetris, Asteroids, Dino, Matrix Rain, Weather, Bomberman, TRON, Custom
rotation.

### Two things the clock page needs to be usable

**The name is shown.** A band across the bottom for 1.6 s after a change.
Snake and Pac-Man are a couple of seconds of animation apart, so without it the
knob gives no feedback until the clock happens to do something recognisable.

**The save is deferred.** `saveSettings()` rewrites the whole settings blob in
NVS. Spinning through fifteen styles would be fifteen writes for fourteen
choices nobody made, so the write waits 2.5 s for the knob to stop.

Long press carries page switching, not the "force refresh" the flight board
note in [09](09-upstream-contributions.md) originally gave it. That note
predates there being more than one page; switching is the one action every page
needs, and a refresh is better fired by the page itself when a selection
settles, with no gesture at all.

The long press fires **on the threshold, not on release**, so the page changes
under the finger. A gesture that waits for release feels broken.

## Decoding

Quadrature by transition table, in `src/control/control.cpp` in the firmware
repo. A detent is four state changes; the table scores each transition +1, −1
or 0, and only a complete ±4 counts. Illegal transitions — which is what
contact bounce looks like — score 0 and cancel out, so the encoder needs no RC
filtering. The switch is debounced at 25 ms.

Events go through a small ring buffer. A fast twist can outrun a frame, and a
knob that drops detents feels broken.

## Cost

Measured, modules linked:

| | Flash | RAM |
|---|---|---|
| Encoder driver + page dispatch | 1048 B | 40 B |
| Clock style control | 2304 B | — |

## Not verified

None of this has met hardware. In particular: whether GPIO10 and GPIO13 are
actually brought out to the board's expansion header, and whether the 1.8 V
note applies to WROOM-2. Both are first checks when the panels arrive.
