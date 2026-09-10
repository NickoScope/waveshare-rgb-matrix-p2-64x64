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

## How deep it has to be: 20 mm at the edge

**The panel is one 15 mm module, not a stack of layers.** It is worth stating plainly
because it is easy to get wrong: the pixels, the GOB resin and all the electronics are
already inside the moulded case, and the side view on the factory drawing measures
15.000 × 127.797 in drawing units. The distributor's 14.5 for the whole module and this
15.0 for the case agree with each other. Add up "board + connectors + GOB" as separate
layers and you triple-count the same part and land near 60 mm, which is what the first
version of this sheet did.

The brief caps the panel at 20 mm at the edge, so the stack is:

| | mm |
|---|---|
| face frame, overlapping the field by ≤ 0.5 | 1.5 |
| the matrix module, whole | 15 |
| ribbon lying flat | 1.5 |
| back wall | 2.0 |
| **total** | **20.0** |

That leaves 3.5 mm behind the panel. A flat ribbon fits in it; nothing else does. The
HUB75 and VH4 shells almost certainly do not, so each gets a local pocket in the back
wall with the cable bent right at the shell — the trick the MatrixPortal enclosures use,
where the ribbon is folded into a Z with a sharp bend at each end.

**The controller cannot live behind the panel.** A 50 × 42 board has nowhere to go in
3.5 mm. It sits in a local boss in the back wall: the edge stays 20 mm, the boss runs
30–32 mm deep, and it hides in the gap the wall hanger already leaves. The alternative
found in the field — MatrixPortal-style cases and the Adafruit-derived ones — is a flat
28–35 mm back over the whole area, which is simpler to print but abandons the 20 mm edge.

Power is split from the matrices' point of view: the 5 V adapter feeds a distribution
point, and each matrix takes its own VH4 lead from there. Matrix current never crosses
the controller board. HUB75 enters the near panel and a short jumper carries it to the
far one, so the only cable crossing the seam is one ribbon behind the boards.

## Status

M0 — composition options and layout, both sheets done. Not yet designed: the controller
boss, the wall mount, the light-leak contour and the swappable 20 mm bottom strip. M2 does
not close until the panels arrive and the module thickness and connector standoff are
measured on the real hardware.

## Licence

Same as the rest of this repository. The Waveshare drawing referenced in the docs is not
redistributed here — the download URL is in [../docs/10-mechanical.md](../docs/10-mechanical.md).
