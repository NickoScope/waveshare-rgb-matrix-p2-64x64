# Enclosure: a wall panel built from two of these matrices

An open design for a 128 × 64 wall panel — two RGB-Matrix-P2-64x64-B tiled side by side,
driven by the ESP32-S3-RGB-Matrix board, printed on a desktop FDM machine in white.

Work in progress. The hardware is on order and not yet in hand, so every dimension that
depends on the physical panels is parametric and marked for measurement on arrival.

| File | What it is |
|---|---|
| [`TZ_KORPUS_C_LED_MATRIX_RU.md`](TZ_KORPUS_C_LED_MATRIX_RU.md) | the design brief (Russian) — requirements, tolerances, acceptance criteria |
| [`M0_kompozicii.svg`](M0_kompozicii.svg) · [`.png`](M0_kompozicii.png) | three front-composition options and the split scheme |
| [`m0_sheet.py`](m0_sheet.py) | generates that sheet; edit the `VAR` table to try other proportions |
| [`M0_komponovka.svg`](M0_komponovka.svg) · [`.png`](M0_komponovka.png) | the layout sheet — rear view, front-to-back section, and the seam detail |
| [`m0_layout.py`](m0_layout.py) | generates the layout sheet; `LAYERS` holds the depth stack |

## The two problems that shape this enclosure

**The seam between the panels.** At a 2 mm pitch a tiled pair only looks like one picture
if the pitch stays 2.0 mm across the joint. That puts a hard constraint on the mechanics:
no rib, no gap and no wall between the panels, and clamping from the outer ends inward.
It also depends on a number the spec table gets wrong — see
[../docs/10-mechanical.md](../docs/10-mechanical.md), where the factory drawing turns out
to dimension the moulded frame at 127.8, not 128.0. The design clamps **board edge to
board edge** and does not assume the moulded frames meet.

**Nothing may cross the face.** The active area alone is 256 mm wide, which is more than a
250 mm build plate takes, so the shell has to be split — but a seam running across the
picture is exactly what the first problem forbids.

The answer on the sheet: a narrow, long part fits on the plate **diagonally**, so a rail
of L × W prints in one piece when L + W ≤ 354. A 284 × 12 top rail comes to 296 and fits.
The frame therefore becomes four whole rails plus corner pieces, all seams land in the
corners and on the back, and the face stays unbroken. A seam down the middle was rejected
on purpose: it would fall exactly on the panel joint the whole design is trying to hide.

## How deep it has to be

The layout sheet stacks it up: 3 mm face frame, a 4 mm bevel opening outward, 2 mm of GOB
and pixels, the matrix board, the HUB75 and VH4 connectors standing off it, the controller
and its loom, a 3 mm back wall, and a gap to the wall for the hanger — about 59 mm in all.

**37 of those 59 mm are not yet a measured fact** — the board, the connectors standing off
it, and the controller with its loom. The board thickness is 14.5–15 depending on which
source you read, and the factory drawing dimensions neither connector. So the depth stack
is written as named parameters, not numbers, and those three are drawn dashed on the sheet.
The 10 mm gap behind the back wall is dashed too, but it is a choice, not an unknown.

Power is split from the matrices' point of view: the 5 V adapter feeds a distribution
point, and each matrix takes its own VH4 lead from there. Matrix current never crosses the
controller board. HUB75 enters the near panel and a short jumper carries it to the far one,
so the only cable crossing the seam is one ribbon behind the boards.

## Status

M0 — composition options and layout, both sheets done. Not yet designed: the controller
bay, the wall mount, the light-leak contour and the swappable 20 mm bottom strip. M2 does
not close until the panels arrive and the open dimensions are measured.

## Licence

Same as the rest of this repository. The Waveshare drawing referenced in the docs is not
redistributed here — the download URL is in [../docs/10-mechanical.md](../docs/10-mechanical.md).
