# Measurement protocol — what to check when the hardware arrives

Eight numbers are guesses in `case_c_lib.py`, and until they are facts nothing here may
be printed. This is the order to take them in, what to watch out for, and where each one
goes. Run `python verify.py` after each edit: it prints the remaining guesses on every run
and recomputes the minimum depth.

## Take these two first — they decide the final depth

**1. Thickness of the bare panel, with no mounting frame.** → `PANEL_T`

Take the frame off. Measure over the tallest thing on the back, not over bare board —
that is what the case has to clear. Measure at four points; if the GOB resin is uneven the
spread matters more than the average. Today's value, 15.0, is the *frame's* height, used
as a safe ceiling.

**2. Height of the controller board with connectors fitted.** → `CTRL_T`

Plug the ribbon and the power lead in first, then measure. Waveshare publishes 50 × 42 and
no thickness at all. This board sits behind the panel, so it adds to (1), and the two
together set how far below 30 mm the case can go.

> After these two: `verify.py` prints `минимум с контроллером внутри`. That is the number
> to compare against 30.

## Then the rest

**3. How far the mated HUB75 ribbon stands proud of the panel.** → `CONN_PROUD`, `VH4_PROUD`

Not the height of the shell — how much of the *mated* connector sticks out past the
panel's own outline. Currently assumed zero, on the argument that the frame closes over
everything. If it turns out positive and larger than the cavity, a relief reappears in the
back cover by itself.

**4. Outer size of the bare panel, board edge to board edge.** → `PANEL_BOARD`

Measure both panels, both axes. The seam design assumes they may differ from 128.0; what
it must not do is assume they are equal to each other. If they differ, say by how much.

**5. Are there any threaded mounting points on the bare panel?** → `USE_FRAME_M3`

The six-M3 grid on the drawing belongs to the frame. If the bare panel has nothing, the
current pressure-based holding stands as is. If it does have points, note the pattern and
we can add screws as a second line of defence.

**6. Do the magnetic screws stand proud, and by how much.**

**7. Gap between board edge and the first lit pixel.** → checks the 0.5 mm bezel overlap

Measure on all four sides of one panel. If it is larger than the overlap, the bezel will
show a dark border; if smaller, the bezel clips pixels.

**8. Mass of one panel.** → wall mount is sized for three times the assembly mass

## How to enter a value

Edit the number in `case_c_lib.py` and change its tag from `MEAS` to `DWG` or `SPEC` —
whichever it became. Then:

```bash
python verify.py          # what still remains, and what the minimum depth is now
python sheet.py           # parts and sections
python full_section.py    # the full vertical section
```

If a check fails, that is the point of it: the model has been told something it cannot
accommodate, and the failure names which clearance ran out.
