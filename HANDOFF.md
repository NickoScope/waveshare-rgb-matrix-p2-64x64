# Handoff

Rolling record of where the work stands. Newest first.

---

## 2026-09-10

### Done

**Flight board reached live data.** The Home Assistant automation now sends a
cleaned city name (`cy`) alongside the IATA code, and the panel shows both.
Thirty real Nice flights broke three things that invented data never would
have, all fixed:

- character-by-character trimming produced `EUROAIRPOR`; fitting now drops
  whole words, then a dangling connector, and stops at the code
- Picopixel's `U` is `V` with one extra row — `ZURICH` read `ZVRICH` on a
  quarter of the destination column. `src/fonts/picopixel_fb.h` gives it a flat
  bottom; one bit changed, verified that exactly one glyph differs
- AeroAPI's "city" is the commune (`BLAGNAC` for Toulouse), which is why the
  code is now drawn unconditionally

Buying column width for the code was measured, not guessed: 23/30 rows could
show code and full name before, 27/30 after moving three constants and
shortening the two widest status words. Coverage is flat between 20 and 28 px
of status width, so nothing else was cut. Recorded in `docs/09`.

**Layout became a generated dependency.** The constants were hand-typed in
three places across two repos. `flightboard.cpp` is now the only hand-written
copy; `tools/fb_layout.py` extracts them, `fb_check.py` fails on drift and a
pre-commit hook runs it. Verified by breaking a constant and watching the
commit get blocked.

**Repository structure settled.** One working repo: the fork
`NickoScope/AnimatedPixelClock`, branch `board/waveshare-esp32-s3-rgb-matrix`.
The simulation moved there from here, which removed the cross-repo machinery
entirely. This repo is hardware documentation and the enclosure only.

**Yacht radar ported from NickoScope32.** Left 64x64 is a chart of the Bay of
Cannes, right 64x64 a table of vessels by range. AIS client from Main-S3
`iot/yacht_radar.cpp` (same silicon), visual design and coastline from H743
`fx34_yacht_radar.cpp`.

The first port drew fx34's wireframe, which reads as coarse on a raster panel.
Rebuilt as a real chart: land filled by scanline-filling the mainland ring
(the three "bridge" segments in the fx34 data exist to stitch it), sea coloured
by GEBCO 2020 depth, land by EU-DEM 25 m elevation with a north-west hillshade,
shoreline anti-aliased on top. All baked at build time into 8 KB of RGB565.
Terrain is committed so the map rebuilds offline.

Two resolution decisions worth keeping: the coastline is stored in DAC units,
not rounded to pixels, and vessels blend against the baked map rather than over
it — on a 64 px chart, sub-pixel position carried into brightness is the only
resolution left.

Cost measured with the module actually linked: flash +31.1 KB, static RAM
+1.1 KB.

### Open

- **Nothing is hardware-verified.** The panels have not arrived. First step when
  they do: `matrix-waveshare-rgb-bringup`, then settle GENERIC vs FM6126A.
- TLS session heap for the AIS websocket is not measured — runtime only.
- The yacht radar page is reachable only via the `httpForceYachtRadar` flag; no
  HTTP route or button yet.
- Older commits in the fork carry `nickol@me.com` in public history. Local
  config is fixed and the last three were rewritten before pushing; the rest
  need a force-push and the owner's decision.
- NickoScope-Watch still listens on the legacy `.../state` topic; the keyed
  `(apt, dir)` topic is published in parallel and the legacy publish can go once
  the watch migrates.
- `mic_power_rail` GPIO46 remains UNVERIFIED.
