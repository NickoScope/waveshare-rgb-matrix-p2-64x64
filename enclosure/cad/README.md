# CAD — parametric model (stage M1)

Written with [build123d](https://github.com/gumyr/build123d) 0.11 in algebra mode.
Run anything here from a venv that has `build123d` and `trimesh`.

```bash
python case_c_lib.py     # the parameter base, prints what is still unmeasured
python front_frame.step.py
python back_shell.step.py
python mockups.step.py   # the bought hardware, for clearance checks only
python verify.py         # every check; exits non-zero on a violation
python render.py         # PNG views, no OpenGL needed
```

| File | What it is |
|---|---|
| `case_c_lib.py` | every dimension, each tagged with where it came from |
| `front_frame.step.py` | face plate, window with the bevel, seal groove, encoder hole |
| `back_shell.step.py` | the part that carries everything: bosses, posts, relief, cable entry |
| `mockups.step.py` | panels, controller, encoder — **not printed parts** |
| `verify.py` | fit, clearance, single-solid and watertight checks |
| `render.py` | a small z-buffer rasteriser, since pyglet isn't available here |

## Every dimension says where it came from

`case_c_lib.py` tags each value `ЧЕРТЁЖ` (read off the factory drawing),
`ТЗ` (a decision in the brief) or `ОБМЕР` (a guess awaiting measurement).
`verify.py` prints the `ОБМЕР` list on every run, and nothing on that list may
be frozen into a printable file. Six values are on it today; the one that
matters most is `CONN_STACK` — the HUB75 shell **with the ribbon plugged in**.

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
