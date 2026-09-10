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

**The panel is one module, not a stack of layers.** Worth stating plainly because it is
easy to get wrong: the pixels, the GOB resin and all the electronics are already inside the
moulded case. Add up "board + connectors + GOB" as separate layers and you triple-count the
same part and land near 60 mm.

How thick that module is, is still **not a confirmed fact**. The drawing's side view of the
case is 138 separate `LINE` entities on layer `2` whose overall extent is 14.9996 × 127.7968
— but there is no closed outline, no segment of either length, and the sheet's own `15.0`
dimension does not attach to that view (its witness points land at X 379.741 / 394.741,
where no geometry lives — possibly an artefact of the DWG → DXF conversion). What *is*
firmly attached to that view are `12.0` and `4.4775`, both measured from its front edge.
So: **treat the thickness as 14.5–15 and measure your own panel.** The extent and the
distributor figure agree with each other, and neither is a dimensioned value.

The working depth is 30 mm until the hardware is in hand and can be measured:

| | mm |
|---|---|
| face frame, overlapping the field by ≤ 0.5 | 1.5 |
| the matrix module, whole | 15 |
| cavity: connector shells, ribbon, controller board | 11.5 |
| back wall | 2.0 |
| **total** | **30.0** |

If the connector shells turn out to sit flush inside the module, the same stack closes at
**20 mm** (1.5 + 15 + 1.5 + 2.0), so the design is kept so that shrinking it later changes
only the depth of the back — not the principle. For comparison, MatrixPortal-style cases and
the Adafruit-derived ones run 28–35 mm flat across the whole back.

Power is split from the matrices' point of view: the 5 V adapter feeds a distribution point,
and each matrix takes its own VH4 lead from there. Matrix current never crosses the
controller board. HUB75 enters the near panel and a short jumper carries it to the far one,
so the only cable crossing the seam is one ribbon behind the boards.

## The knob

The panel picks its own airport for the flight-board page, so it needs a control of its
own rather than only a dashboard. An EC11-size encoder with a push switch sits at the right
end of the 20 mm bottom strip. Its body is 13.2 × 12.4 in plan, which clears the 20 mm strip
by nearly 4 mm a side; depth was the real question and the strip cavity is 26.5 mm. The
catalogue shaft is 20 mm, which is long for a thin panel — shorten it to 8–10 mm, and keep
the knob at ⌀12–14 so the strip still reads as a strip.

It all rides on the swappable insert, so a different set of controls means reprinting one
insert rather than the shell.

## Status

M0 — composition options and layout, both sheets done. Not yet designed: the wall mount,
the light-leak contour and the swappable bottom strip itself. M2 does not close until the
panels arrive and the module thickness and connector standoff are measured on the real
hardware.

## Licence

Same as the rest of this repository. The Waveshare drawing referenced in the docs is not
redistributed here — the download URL is in [../docs/10-mechanical.md](../docs/10-mechanical.md).
