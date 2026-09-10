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

- **GPIO45** selects VDD_SPI voltage. This module has in-package flash and PSRAM
  with VDD_SPI fixed at 1.8 V by the `VDD_SPI_FORCE` eFuse, and the ESP32-S3
  hardware design guidelines state that the strap then no longer affects it.
  **UNVERIFIED** — read the eFuse with `esptool.py summary` before trusting it.
- **GPIO46** gates ROM message printing at boot. Cosmetic; it does not stop a
  boot.

That Waveshare chose exactly these two for the header is itself evidence: they
are the pins the board has left.

Sources: `reference-drawings/controller/ESP32-S3-RGB-Matrix-Schematics.pdf` —
its pin-assignment table and the U8 connector — plus the *ESP32-S3 Datasheet*
§2.3.4–2.3.5 for the chip-level restrictions.

**FYI, still to check:** the WROOM-1 datasheet notes that on R16V parts VDD_SPI
is 1.8 V and **GPIO47/48 run at 1.8 V** with it. Those two are this board's I2C
bus. Confirm against the WROOM-2 datasheet before hanging a 3.3 V part on it.

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
