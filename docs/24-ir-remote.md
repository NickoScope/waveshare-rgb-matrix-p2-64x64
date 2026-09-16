# The infrared remote

**Status 2026-09-16 21:33:** flashed and **working on the panel**, driven from
the serial console. **No receiver is soldered**, so everything below the decoder
- the receiver, real NEC frames, learning from a real remote - has still never
run. The pin it will use is the knob's, and that is deliberate.

The owner's plan, stated on 2026-09-16: *"скоро будем переходить с энкодера на
IR управление"*. This is the panel side of that, built in advance, as a
plug-and-play module behind a flag.

## The decision that shapes everything

**The remote is not a second control scheme. It is the same knob.**

The panel's gestures live in one state machine, `src/control/control.cpp`:
a detent browses, a click selects, a long press is the same as a click. The
remote produces exactly those two things — detents and a button *level* — and
hands them to that machine. Single press, long press, browse, enter and every
page's behaviour then follow by construction. The alternative, a second
implementation of the gestures on the IR side, is how two control paths drift
apart over a year.

Ported from NickoScope32 ADD-79 (`src/ir_remote.{h,cpp}`, v33.55.0), which is
where the shape came from: learned codes rather than hard-coded ones, a map in
NVS so a remote survives a reflash, and a simulator that injects a slot at the
level a real frame reaches.

What is ours, and different:

| | NickoScope32 | Here |
|---|---|---|
| The rules | inside the `.cpp`, with Arduino and the decoder library | `ir_map.h`, plain C++, 150 host checks |
| The console | a web page at `/ir` | a serial console **and** the portal card; the grammar is host-tested too |
| The receiver | always compiled | its own flag, so a build carries the module with no library and no heap |
| The seam | `main.cpp` reads the module from `loop()` | the encoder's own 1 kHz task reads it, so the event queue keeps its single producer |

## The hardware problem, and the number to check first

**This board has no free GPIO.** The expansion header U8 is four pins — IO45,
IO46, GND, 3V3 — and the knob holds both signals. The vendor pin table gives
IO10 to RTC_INT and IO13 to IMU_INT, and neither reaches the header
([11-control-and-pins.md](11-control-and-pins.md),
[02-controller.md](02-controller.md)). So the receiver's pin is **IO45, the
knob's own**, and a build that asks for both is refused at compile time.

Then the electrical catch. Read off the sources on 2026-09-16:

| Fact | Source |
|---|---|
| A Vishay receiver's OUT is an open collector with a **30 kΩ pull-up inside the package**; supply 2.0–5.5 V, so 3V3 is in range; V<sub>OSL</sub> ≤ 100 mV at 0.5 mA; I<sub>O</sub> ≤ 5 mA | Vishay datasheet [82459](https://www.vishay.com/docs/82459/tsop48.pdf) rev 2.4, block diagram and the electrical table, read in full |
| This board pulls IO45 and IO46 **down** with 10 kΩ (R59, R60; the pull-up positions R57, R58 are not fitted) | Waveshare schematic, via `src/control/control.cpp` |

Those two in series divide the supply:

| | |
|---|---|
| idle line, as wired | 3.3 × 10 / (30 + 10) = **0.83 V** |
| what the ESP32-S3 needs to read a one | 0.75 × VDD = **2.48 V** |
| with an external **2.2 kΩ** from OUT to 3V3 | 3.3 × 10 / (10 + 2.05) = **2.74 V**; 1.6 mA sunk when the receiver pulls down, inside its 5 mA rating |

**CALCULATED, NOT MEASURED.** Without the pull-up the line would sit low for
ever and the decoder would see one endless burst. This is the first thing to put
a meter on when a receiver is soldered. The datasheet's own application circuit
also asks for a series resistor and a capacitor on V<sub>S</sub> "in case there
are strong ripple or spikes on the supply line" — next to a HUB75 panel
switching amps, fit them.

Pick a **38 kHz** part (TSOP4838 / TSOP2238 and relatives): NEC, the format of
the owner's remote, uses a 38 kHz carrier.

## The timings, and where they come from

Vishay application note [80071](https://www.vishay.com/docs/80071/dataform.pdf)
rev 2.3 (26-Jun-2024), "Data Formats for IR Remote Control", THE NEC CODE, read
in full: the carrier is 38 kHz, a frame opens with a 9 ms leader and a 4.5 ms
pause, and a held key repeats **in a 108 ms time slot**. Every timing in the
module is derived from that one number:

| Constant | Value | Why that number |
|---|---|---|
| `kHoldMs` | 250 ms | the button is released once frames stop. Outlives one dropped repeat (2 × 108 = 216 < 250) and not two |
| `kRepeatFreshMs` | 200 ms | a NEC repeat carries no code, so it extends the last slot — but only while that slot is still the one being held |
| `kRotAccMax` | 3 detents | the seam drains at 1 kHz; this only fills if the sampling task is starved, and dropping the excess beats spinning the display after the remote stopped |
| `kLearnWindowMs` | 15 s | long enough to pick the remote up and aim it |

The same numbers were in the module this was ported from; the difference is that
here they trace to the note rather than to the other firmware.

## The module

`src/ir/`, behind `-DIR_ENABLED`, with `-DIR_RX_ENABLED` for the receiver
itself. Files, flags, the console and the cost are in
[src/ir/README.md](https://github.com/nickolaykolev/AnimatedPixelClock/blob/feature/market-climate-audio/src/ir/README.md)
in the firmware repo.

Eight slots. Three of them — turn left, turn right, press — are the knob's and
reach the state machine through the seam. Five are reserved: they are learned,
counted and reported, and nothing acts on them yet.

Codes are learned, never hard-coded, and live in their own NVS namespace
(`irmap`). A code lives in one slot only: learning it again moves it, and the
move is reported, so a remote whose buttons were mixed up cannot fire two
things at once.

## Testing it with no receiver

The simulator is not a debug hook on the side: it enters at exactly the level a
decoded frame does, so the seam, the state machine and every page are
exercised. On the serial port at 115200:

```
ir                  what the module knows
ir cw 3             three detents clockwise - the display should browse
ir ok               a click
ir ok 1200          held past the 1 s threshold: a long press
ir learn ok         open the window, then press the button on the remote
ir clear all
```

Nothing else reads `Serial` while `loop()` runs — the Improv window in
`src/network` closes before it begins — and lines that do not start with `ir`
are left alone. The portal's Remote card does the same over HTTP.

## What has been checked, and how

| | |
|---|---|
| The rules and the console grammar | `tools/ir/check_ir.py`, **150 checks, all passing**: a button that survives one dropped repeat and not two, a repeat frame that extends only the slot still held, detents drained exactly once, a learned code living in one slot only, every comparison holding across the millis() wrap, and a parser that truncates rather than overruns |
| Every build combination | `tools/flag_matrix.py`, **53 of 53 behaved as intended**, re-run on the fixed code (e3b5f65) at 2026-09-16 21:46. Four of those rows are this module's: it builds alone, it builds with the receiver, and the two that must be refused are refused - the receiver beside the knob, and the receiver without the module. A run in between reported 52 of 53 and named no row: it shared the build directory with an audit's own clean build, which is a known way to produce a false failure. Worth recording as a habit: **one PlatformIO build at a time, and never pipe the matrix through `tail`** - I did, and the truncated log could not say which row had gone red |
| What the receiver library costs with the flag off | **Measured, not assumed:** `nm` on `firmware.elf` finds 0 `IRrecv` / `IRsend` / `decodeNEC` symbols. PlatformIO compiles the library because it is in `lib_deps`; the linker keeps none of it |
| The panel image | builds; RAM 31.5 %, flash 48.1 % |

One mistake worth recording, because the matrix is what caught it: the module's
`#include` had been added inside the `PRESENCE_ENABLED` block in `main.cpp` and
`web.cpp`. The panel's own build has presence, so it compiled and looked fine -
and a build with `IR_ENABLED` alone could not see `irBegin`. Two rows of the
matrix went red and named it. Without that script it would have shipped.

## What it did on the panel, 2026-09-16 21:33

Flashed as 2.4.0 and driven from the serial console at 115200. The proof is not
that the module answered - it is that the **encoder's own counters** moved, and
they are incremented inside the encoder's `push()`, past the seam:

| Typed | The encoder's counters | The display |
|---|---|---|
| `ir cw` | cw 0 → 1 | opened the football clock |
| `ir cw 3` | cw 1 → 4 | walked on to the snake clock |
| `ir ccw 2` | ccw 0 → 2 | back to minecraft |
| `ir ok` | click 0 → 1 | |
| `ir ok 1200` | long 0 → 1 | a long press, from the same state machine as the knob's |
| `ir ok 99999999999` | long 1 → 2, held true, then released on its own | the audit's clamp: five seconds, not weeks |
| `ir sim bright_up` | nothing moved, and the panel said so | a reserved slot is accepted and does nothing |
| `ir sim nope` | refused with a readable line | |
| `ir learn ok` | window opened, 13.5 s left, and the panel said there is no receiver to hear it | |

Hit counts after the run matched exactly what was typed: CCW 2, CW 4, OK 3,
BRIGHT_UP 1. Free internal heap 35.2 KB after boot, `loopMaxMs` 6, no failed
allocations, no crash.

The two long-lived bugs the audit found cannot be reproduced on a bench - they
need 25 days of uptime - so this run is not what closes them. The host test is.

## What the audit found, and the lesson in it

The module passed 150 host checks and every build combination, and the audit
still found two blockers. Both were the same mistake, and both would have
fired on a panel with no remote in the room at all.

| Finding | What would have happened |
|---|---|
| **The button had a deadline, and deadlines rot.** `okDown()` compared a signed difference against "held until", which starts at zero. Past 24.85 days of uptime that difference reads negative — "still held" | Any panel running a month would have read the knob's own button as permanently pressed. The whole interface, not just the remote |
| **A simulated hold was unbounded.** `/api/ir/sim?slot=OK&hold=…` took the number straight from the query string | One unauthenticated GET on the LAN pins the button down for weeks |
| **Freshness was signed too.** A repeat frame checked "was the last frame recent?" with a signed difference | A repeat arriving after a month-old press read as recent and produced a detent out of nowhere |

The fix was not three patches but removing the class: a deadline is no longer
compared at all. The button is a start plus a span, the span is zeroed the
moment it runs out, and zero means "not held". Ages — how long ago something
happened — are unsigned. Four host cases now run the module at 25.5 days of
uptime.

**The rule that caused it was mine, and it was wrong as an absolute.** The
header said "every comparison against millis() is a signed difference", carried
over from the firmware this was ported from, where it had been the fix for the
opposite bug. Signed is right for a deadline you keep refreshing; unsigned is
right for an age. Stating it as a law produced three bugs that all passed the
tests written under the same law.

One more, worth recording because it is a process failure rather than a code
one: the same commit quietly deleted 85 of the 198 lines of `platformio.ini` —
the comments recording why the flash mode is `opi_opi`, why `SPIRAM_DMA_BUFFER`
is refused, why the platform is pinned. Restored from the previous commit.

## What is not done

- **The receiver has never run.** No TSOP is soldered; everything below the
  decoder is verified by the host test and the simulator only.
- **The pull-up above is arithmetic, not a measurement.**
- The reserved slots do nothing yet.
- **RC5/RC6 toggle bit.** Those remotes flip a bit in the code on every press,
  so such a remote would answer every other press. NEC — the owner's — does
  not. Masking it per protocol is queued, not done. (Carried over from ADD-79,
  where it was logged as a LOW finding.)
