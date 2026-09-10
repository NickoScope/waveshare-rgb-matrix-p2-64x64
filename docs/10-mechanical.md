# Mechanical: what the factory drawing actually says

Waveshare ships a 2D drawing with the panel wiki:
`files.waveshare.com/wiki/RGB-Matrix-P2-64x64/RGB-Matrix-P2-64x64.zip` →
`RGB-Matrix-P2-64x64.dwg` (AutoCAD 2018, AC1032, 1.4 MB).

Everything below is read out of that file — from its DIMENSION objects and from circle
centres — not from the spec table and not from a distributor page. Reproduction commands
are at the end, so any claim here can be checked in a minute.

---

## The headline: the moulded frame is dimensioned 127.8, not 128.0

The drawing carries **two 127.800 dimensions**, horizontal and vertical, on the same view.
That view is not the PCB: it is a moulded frame — stiffening ribs, bosses, corner posts,
a large open window in the middle. A note on the sheet reads
`JXS-P2-128*128 bottom case Back lock screw M1*6`. So the part is *named* 128×128 and
*dimensioned* 127.8.

[01-panel.md](01-panel.md) lists `Dimensions: 128 x 128 mm`, which is what Waveshare's spec
table says. Both statements are true of different things, and the difference matters the
moment you tile two panels.

**What the drawing does not settle:** whether the bare PCB is 128.0 while the moulded frame
sits 0.1 mm inboard on each side, or whether the frame is the outermost surface. The sheet
dimensions the frame; it does not dimension the board edge. So:

| If the outermost surface is… | Two panels butted | Pitch across the seam |
|---|---|---|
| the PCB at 128.0 | 256.0 | 2.0 mm — continuous |
| the moulded frame at 127.8 | 255.6 | 1.8 mm — 10 % short |

At a 2 mm pitch, a 10 % error on one column is visible at normal viewing distance.

**Practical consequence for anyone building a multi-panel enclosure:** clamp
**board edge to board edge**, and do not design as if the moulded frames will meet. If
your mechanical stack-up depends on which surface is proud, measure your own panels —
Waveshare warns on the wiki that board layout varies between production batches, and that
warning is not limited to the silkscreen.

---

## Mounting: six M3 points

Six holes ⌀2.5 (M3 pilot) sit on layer `SCREW`, and six `M3` text labels sit at exactly the
same coordinates. Relative to the part centre:

```
             (0, +56.85)

  (−56.85, +44.00)     (+56.85, +44.00)

  (−56.85, −44.00)     (+56.85, −44.00)

             (0, −56.85)
```

Four on the corners of a 113.7 × 88.0 rectangle, two on the vertical centreline at ±56.85.
Full span 113.7 mm both ways. The sheet separately dimensions 56.85, 56, 44, 29, 15, 8, 48,
80, 112 and 120, all consistent with this grid.

## Perimeter: eight ⌀4 positions per side

Twenty-eight ⌀4.0 circles run around the front view, offset from the 127.8 outline by:

```
3.9 · 23.9 · 39.9 · 59.9 · 67.9 · 87.9 · 103.9 · 123.9
```

on both axes. The row is symmetric about 63.9 = 127.8 / 2; pairs are 3.9↔123.9,
23.9↔103.9, 39.9↔87.9, 59.9↔67.9. Which of these the four bundled magnetic screws use is
not marked on the sheet.

## Other holes on the sheet

| Layer | ⌀ | Count |
|---|---|---|
| 0 | 0.90 | 40 |
| 1 | 4.00 | 28 |
| 0 | 1.30 | 25 |
| 71 | 2.29 | 25 |
| 0 | 3.50 | 12 |
| 2 | 1.294 | 8 |
| SCREW | 2.50 | 6 |
| 2 | 5.97 | 4 |
| 1 | 3.00 | 2 |

## Section A-A

Four dimensions appear in the section zone: **15**, **120**, **4.48**, **12**.

**FYI — 15 is most likely the overall thickness, but the sheet does not label it as such.**
Distributor listings give 14.5 mm. Treat thickness as 14.5–15 and measure your own panel
before committing a mechanical design; the GOB resin layer is exactly the sort of thing
that varies.

**Corroboration, and its limit.** The enclosure work reports confirming 15.000 from the side
view's geometry. Two independent attempts here failed to reproduce that specific rectangle:
a coarse per-view bounding box and a targeted search for a 127.797 by 15.000 pair sharing an
endpoint both came up empty, finding only a single stray 15.019 segment in the section zone.
The `15` dimension **text** is definitely on the sheet, and 15 is consistent with the
distributor's 14.5, so the conclusion is very likely right — but it stays FYI here rather
than being promoted, because it was not independently reproduced.

**What is settled** is that the panel is a **single module of roughly 15 mm**, not a stack of
board plus connectors plus GOB layer counted separately. An earlier enclosure draft reached
59 mm that way; that figure is wrong and was withdrawn. Nothing in this knowledge base ever
used it.

## What the drawing does not contain

**No dimensions for the HUB75 or VH4 connectors** — neither footprint nor height above the
board. The views show where they sit, but no dimension chains reach them. If you need
connector clearance, measure it.

---

## Independently re-extracted, 2026-09-10

The two claims that carry mechanical consequences were pulled a second time, by a different
route, from the same file. Both hold.

| Claim | Result |
|---|---|
| Frame dimensioned 127.8 | **confirmed.** Two DIMENSION entities carry the text `127.8`; their definition points measure 127.800, one on dx, one on dy |
| No 128.0 anywhere on the sheet | **confirmed.** 31 dimensions read, none is 128.0 |
| Six ⌀2.5 holes on layer SCREW | **confirmed.** Coordinates match to the hundredth; span 113.70 on both axes |
| Circle diameter census | **confirmed**, including ⌀4.0 × 28 and ⌀2.5 × 6 |

**One trap worth recording.** Reading the DIMENSION measurement out of group code 42
returns `-1.0` for every dimension in this file — a not-computed sentinel left by the DWG
to DXF conversion. Read the definition points instead (codes 13/23 and 14/24) and take the
distance, or use a library that computes rather than reads. The dimension **text**
(code 1) is present and correct throughout.

Other dimensions on the sheet, with their measured def-point spans: 8, 12, 28, 48, 55.99,
56.85, 80, 112, 120, and 4.48 in the section zone.

---

## Reproducing this

```bash
brew install libredwg          # or: apt install libredwg-tools
dwg2dxf -o matrix.dxf RGB-Matrix-P2-64x64.dwg
```

Then read the DXF with [`ezdxf`](https://ezdxf.mozman.at/): `DIMENSION` entities answer
`get_measurement()` with the dimensioned value, `CIRCLE` gives centre and radius, and
grouping circles by layer separates the hole patterns. Views are laid out along X on the
sheet: `JXS-P4 mask` on the left, the 127.8 outline with the ⌀4 perimeter in the middle,
the six-M3 view below it, section A-A on the right.

`dwg2dxf` prints warnings about unstable MATERIAL and MLEADERSTYLE classes on this file.
They do not affect the geometry.
