# Flight board simulation — generated, not hand-written

`flightboard-sim.html` renders the 128x64 flight board pixel for pixel in a
browser, on live Home Assistant data, so the layout can be judged before the
panels arrive.

**The layout constants in this page are generated.** They come from the
firmware, which lives in a different repository:

```
  NickoScope/AnimatedPixelClock,  branch board/waveshare-esp32-s3-rgb-matrix
  src/flightboard/flightboard.cpp                     <-- source of truth
            |
            |  tools/fb_sim_build.py
            v
  sim/flightboard-sim.html      the  BEGIN GENERATED LAYOUT  block
  sim/flightboard-layout.json   the same thing, standalone
```

Both carry a `digest` of the layout. If it stops matching the firmware,
`tools/fb_check.py` in the firmware repo says so and names what is stale.

## Do not hand-edit

- the `BEGIN GENERATED LAYOUT ... END GENERATED LAYOUT` block in the HTML
- `flightboard-layout.json`

Change `flightboard.cpp` in the firmware repo instead, then:

```bash
cd ../AnimatedPixelClock && python3 tools/fb_sim_build.py
```

Everything else in the page — the prose, the styling, the controls — belongs to
this repo and is edited here normally.

## Why two repositories

The firmware is a fork of `Keralots/AnimatedPixelClock` and has to stay one, or
the changes can never be offered back upstream as a pull request. This repo is
our own knowledge base. They are deliberately separate; the generator and the
digest are what keep them honest.
