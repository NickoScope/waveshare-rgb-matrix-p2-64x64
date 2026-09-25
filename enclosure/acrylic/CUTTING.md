# LED MATRIX enclosure v1 — laser cutting job

**File:** `LEDMX_case.dxf` · units **millimetres** · scale 1:1
**Material:** clear acrylic (PMMA), **4 mm**, one sheet
**Assembled size:** 334.6 × 177.8 × 33 mm

## Layers

| layer | operation | path length |
|---|---|---|
| `CUT` | cut through | 988 cm |
| `ENGRAVE` | engrave, separate low-power pass, ~0.4 mm deep | short |

The dot grid is **cut through**, not engraved: those holes are the speaker
grille, the lettering and the ventilation all at once.

## Seven parts

| part | size | notes |
|---|---|---|
| FRONT | 334.6 × 177.8 | window, dot grid, encoder, speaker bolts, feet |
| REAR | 334.6 × 177.8 | **MIRRORED**; vents, magnet relief, standoffs, feet |
| RAIL TOP | 326.6 × 33 | fingers into both plates |
| RAIL BOTTOM | 326.6 × 33 | as above |
| RAIL LEFT | 158.8 × 33 | as above |
| RAIL RIGHT | 158.8 × 33 | as above |
| FIT COUPON | 184 × 34 | **must be cut — see below** |

## The rear plate is mirrored on purpose

The drawing views every part from the side where X grows. For the front that
is the view from outside; for the rear it is the view from **inside**, so the
rear plate is output mirrored. Cut it as drawn and its engraving would land on
the inner face and read backwards.

## Cut the coupon FIRST

It sets two numbers at once, and both have to come off **the same sheet on the
same machine** as the enclosure.

**1. Finger fit.** A tongue the full thickness of the sheet on the left, seven
slots engraved 3.30 … 3.90 on the right. Find the one the tongue enters snug
but without force, and report that number.

The drawing currently carries **3.70**. That is a *calculation* for a 0.15 mm
per-side kerf, **not a measurement**:

```
slot_actual = slot_drawn + 2 × kerf        finger_actual = sheet thickness
⇒ slot_drawn = sheet thickness − 2 × kerf
```

Neither quantity is knowable in advance, and neither is needed separately —
the coupon measures exactly the combination in the formula.

**2. Dot web.** Three rows of six ⌀2.0 holes beside the slot gauge. The web
between them is **1.2 mm**, thinner than the 2.3 mm used on the NickoScope32
grilles. Check it does not crumble before the whole lettering row is cut.

## What is where

| part | feature | why it matters |
|---|---|---|
| FRONT | window 256.6 × 128.6 | the two matrices drop **into** it and sit flush with the face; the plate's 4 mm are taken by the first 4 mm of the matrix, not added to the depth |
| FRONT | dot grid ⌀2.0 at 3.2 pitch | speaker grille + "NickoScope Matrix" + ventilation, one grid |
| REAR | ⌀26 relief | the speaker is 28 mm deep against a 25 mm cavity; it enters the rear plate's thickness by 3 mm and stops 1 mm short of the outer face — **nothing protrudes** |
| REAR | two staggered vent rows | slots that would hit a standoff are omitted |
| both plates | 3 mm feet | the panel also stands: base 255 mm wide × 33 deep |

The lettering row is 80 columns wide — the same count fits across the 128-pixel
display above it — and measures exactly 256.0 mm, the width of the screen.

## Kerf compensation

Applied **only to the joint slots**. Every other contour is nominal: the
window, the dot grid, the vents, the relief. Do not apply a global machine
compensation on top of them.
