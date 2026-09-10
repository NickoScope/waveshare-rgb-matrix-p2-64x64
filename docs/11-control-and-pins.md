# Physical control, and the pins left to do it with

## The budget

Of the 45 GPIOs on an ESP32-S3, this board and this chip variant leave **two**
that are free without a caveat.

| | Count | Which |
|---|---|---|
| Taken by the board | 27 | HUB75 (14), I2S (6), I2C (2), TF slot (4), BOOT button (1) |
| Blocked by the chip | 14 | GPIO26–32 SPI0/1 flash & PSRAM; GPIO33–37 octal PSRAM; GPIO19–20 USB |
| Free, with a caveat | 2 | GPIO45, GPIO46 — strapping pins |
| **Free and clean** | **2** | **GPIO10, GPIO13** |

Sources: the board pin map in [02-controller.md](02-controller.md), verified
against Waveshare's own firmware; GPIO restrictions from the *ESP32-S3
Datasheet* §2.3.4 and §2.3.5 and the ESP-IDF GPIO reference for esp32s3.

Two points from those that bite here:

- **GPIO33–37 are gone because the PSRAM is octal.** The module is
  ESP32-S3-WROOM-2-N32R16V, and the datasheet is explicit: with octal flash or
  PSRAM those five pins carry DQ4–DQ7 and DQS.
- **GPIO19/20 are gone because there is no UART bridge on this board.** Native
  USB is the only way to flash it, so USB_D± cannot be repurposed.

**FYI, needs checking against the WROOM-2 datasheet specifically:** the
ESP32-S3-WROOM-1 datasheet notes that on R16V parts VDD_SPI is 1.8 V, and
therefore **GPIO47 and GPIO48 run at 1.8 V**, not 3.3 V. Those two are this
board's I2C bus. If that carries over to WROOM-2, anything added to that bus
must tolerate 1.8 V logic — which would rule out casually hanging a 3.3 V I2C
part off it. Read before designing anything onto I2C.

## The encoder needs three pins and there are two

An EC11 with a push switch needs A, B and SW. Three ways out:

| | How | Cost |
|---|---|---|
| **Share GPIO0** (chosen) | A=10, B=13, SW parallel with the BOOT button on GPIO0 | A knob held through reset enters download mode. Recovers on the next reset — and flashes the board without opening the case |
| I2C expander | A PCF8574 or similar on the existing bus | An extra part, and the 1.8 V question above must be settled first |
| Strapping pin | SW on GPIO45 with a pull-down | GPIO45 sets VDD_SPI voltage at boot. Held high at power-up, the board does not come up at all. Worse failure than download mode |

GPIO0 is chosen because its failure mode is recoverable and its side effect is
useful. Both alternatives stay open if the hardware says otherwise.

## Gestures

| Gesture | Meaning |
|---|---|
| Rotate | change the value this page is about |
| Short press | toggle this page's second axis |
| Long press (700 ms) | go to the next page |

| Page | Rotate | Short press |
|---|---|---|
| Clock | — | — |
| Flight board | step through the six whitelisted airports | arrivals ⇄ departures |
| Yacht radar | scroll the vessel table | sort by range ⇄ by size |

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

Measured, module linked: **1048 bytes flash, 40 bytes RAM.**

## Not verified

None of this has met hardware. In particular: whether GPIO10 and GPIO13 are
actually brought out to the board's expansion header, and whether the 1.8 V
note applies to WROOM-2. Both are first checks when the panels arrive.
