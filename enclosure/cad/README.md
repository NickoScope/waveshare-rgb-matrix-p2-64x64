# CAD — parametric model (stage M1)

Written with [build123d](https://github.com/gumyr/build123d) 0.11 in algebra mode.
Run anything here from a venv that has `build123d` and `trimesh`.

```bash
python case_c_lib.py     # the parameter base, prints what is still unmeasured
python case_body.step.py
python back_cover.step.py
python mockups.step.py   # the bought hardware, for clearance checks only
python verify.py         # every check; exits non-zero on a violation
python render.py         # PNG views, no OpenGL needed
python sheet.py          # one sheet: all parts and all sections
python full_section.py   # the full vertical section through the controller
```

| File | What it is |
|---|---|
| `case_c_lib.py` | every dimension, each tagged with where it came from |
| `case_body.step.py` | the case: face plate, window, walls, 12 bosses, encoder seat |
| `back_cover.step.py` | the removable cover: matrix posts, controller pad, relief |
| `mockups.step.py` | panels, controller, encoder — **not printed parts** |
| `verify.py` | fit, clearance, single-solid and watertight checks |
| `render.py` | a small z-buffer rasteriser, since pyglet isn't available here |
| `sections.step.py` | four cut fragments through the assembly |
| `sheet.py` | contact sheet: every part on its own, then the sections |
| `full_section.py` | the full vertical section, on its own sheet with a legend |
| [`MEASURE.md`](MEASURE.md) | what to measure when the panels arrive, in what order |

## Every dimension says where it came from

`case_c_lib.py` tags each value `ЧЕРТЁЖ` (read off the factory drawing),
`ТЗ` (a decision in the brief) or `ОБМЕР` (a guess awaiting measurement).
`verify.py` prints the `ОБМЕР` list on every run, and nothing on that list may
be frozen into a printable file. Six values are on it today; the one that
matters most is `CONN_STACK` — the HUB75 shell **with the ribbon plugged in**.

## The back comes off, not the front

The face is the case — plate, window and walls in one part. What unscrews is the
**back cover**, from behind, eight M3 into brass inserts in the body's bosses, heads
countersunk flush because the panel hangs on a wall. Eight, not twelve: four corners
plus the middle of each side, so every side gets three screws because the corners serve
two sides at once. The widest gap between neighbours is 134 mm, along the top and bottom
— that is the number to watch on the first print, since it is the seal cord that has to
stay evenly squeezed across it. Nothing is visible from the front,
and servicing never disturbs the bevel, the light seal, or how the matrices sit against
the face — the three things the looks depend on.

The cover also carries the matrices, and that is forced: all six M3 points sit *inside*
the panel outline, reachable only from behind, so no post can reach them from the face
side. Pull the cover and the matrix block comes with it. What presses the matrices
against the face plate is the cover being drawn down at its perimeter, through the light
seal cord — which is also what takes up the tolerance on post length.

The fixing bosses are placed off the window edge, not off the plate edge. In the plane
of the face there is only 7.1 mm of flat land; but the bevel lives entirely in the 2.5 mm
of plate, and deeper down the window is already narrow, leaving about 12 mm between its
edge and the wall. The bosses grow from the back of the plate into exactly that band —
2.3 mm clear of the window and 2.3 mm clear of the wall, which `verify.py` checks.

## The drawing is of an accessory, not of the panel

Worth saying plainly, because it invalidates two things I had leaned on. The whole factory
sheet is the **mounting frame** — `JXS-P2-128*128 bottom case` — which ships as an
accessory. The panel can be installed without it, and this design does exactly that.

So: the six M3 points belong to *the frame*, not to the panel. On a bare panel they may
not exist at all. `USE_FRAME_M3` is therefore `False`, and the panels are held by pressure
instead — the seat locates them, the tongues push them together in plane, and ribs on the
cover press them against the face plate, including one rib along the seam itself.
`verify.py` fails outright if that flag is turned back on without the frame being confirmed.

The 127.8 outline is the frame's too. What the frame *does* tell us is worth keeping: it
closes over the panel and all its electronics, so **the panel with everything soldered to
it fits within 15 mm**. That is a ceiling, and a useful one.

## What sets the depth — and it is not the panel

Face plate, panel and cover come to 2.5 + 15 + 2.0 = **19.5 mm**. So a 20 mm case would
be enough — for the panel. The controller is what sets the depth: a 50 × 42 board about
9 mm tall behind the panel puts the minimum at **28.5 mm**, and 30 is that with a little
air. `verify.py` prints all three numbers on every run.

Twenty is reachable, but only by moving the controller out of the panel — into a separate
box on a cable, or a stand. That is a decision about the product, not about the shell, so
the model keeps `DEPTH` as one parameter and will rebuild at any value.

## The back is flat — no relief

An earlier version put a raised band across the back wall for the connectors. It came out
of a mistake: I added 15 mm of module to a 9 mm connector height, as if the shells stood
on top of a finished module. They stand *inside* it. The moulded frame on the factory
drawing **is** the housing over the electronics, and the soldered shells are already
within its 15 mm — the profile shows the bulk of that frame at 12 mm, with only a single
feature reaching 15.

So the number to measure is not connector height, it is **how far the mated ribbon stands
proud of the module**, and only that has to fit the 10.5 mm cavity. At the working figure
it fits with room to spare, `relief_depth()` returns zero, and the cover is flat.

The function stays in place. If the measurement comes back larger than the cavity, the
relief reappears on its own and shows up on the sheets — that is the point of keeping the
depth a computed value rather than a drawn feature.

## How the panels are located

Screws through the M3 grid hold the panels *down*; they do not decide *where* the panels
are. That is what the seat does — ribs standing 3 mm proud of the back of the face plate.

The seat cannot simply be a pocket cut to size, because the outermost surface may be the
board (128.0) or the moulded frame (127.8) and nobody knows which yet. A pocket at 255.6
would not accept boards; one at 256.0 would leave 0.4 mm of slop with frames, and the seam
would drift open. Referencing off one edge is worse still — I built that first and it
fails: with frames the whole slack lands on the far edge, the panel stops short of the
window, and a slit opens in the corner.

So the seat is cut to the **larger** candidate and the panels are pushed **towards the
centre** by sprung tongues on the cover, two per side. The seam then closes whatever the
measurement turns out to be, the slack splits evenly between the outer edges, and the
bezel overlap stays positive both ways — 0.5 mm with boards, 0.3 mm with frames.
`verify.py` computes both cases and fails if either goes to zero.

The tongues pass *through* gaps in the seat ribs rather than around them; both parts read
the same `clamp_positions()`, so a tongue cannot end up butted against a rib. That is a
mistake the intersection check caught, not one I foresaw.

## Two places where the model does not follow the brief literally

**The bevel is cut at 70°, not the 45° §4.2 asks for.** The same section requires
a ±70° viewing angle. At 45° the window edge would shade the outermost pixel at
wide angles, so 45° cannot satisfy the requirement it sits next to. The model
takes the angle from the panel's own viewing angle and opens the window by
`WALL_FRONT × tan(70°)` = 6.87 mm a side. Change `VIEW_ANGLE` to alter it.

**The bottom strip is 26.9 mm tall, not 20.** §4.4 asks for 20 mm of *free*
strip. The bevel opens downward too and eats its 6.87 mm out of the strip, so
the structural height is the free height plus that. `verify.py` measures what is
actually free and fails if it drops below 20.

## What the model does not have yet

Splitting for the print bed (§8) belongs to M2 — both parts are still whole,
284 × 168.9, and `verify.py` says so without calling it a violation. Also
missing: the wall mount, the light-leak contour beyond the seal groove, the
swappable insert as a separate part, and the thermal path.
