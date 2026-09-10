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

### Also done, after this record was first written

**The encoder, and a correction it took the schematic to find.** A physical
control layer went in — one EC11, three pages, gestures identical everywhere:
rotate changes what the page is about, a short press toggles its second axis, a
long press leaves for the next page. The clock page walks all 15 styles from a
table generated out of the web UI's own option list, so the browser and the
knob cannot disagree.

Its first pin map was wrong, and wrong in an instructive way. GPIO10 and GPIO13
were chosen by counting which pins the firmware did not reference. The vendor
schematic — which had been read once in September and not kept — says IO10 is
RTC_INT and IO13 is IMU_INT, and that the expansion header U8 is four pins:
IO45, IO46, GND, 3V3. The encoder as designed could not have been wired at all.
Fixed, and the drawings are now in the repository with a fetch script and
hashes.

**The flight board got a transport.** It could draw but nothing fed it —
`flightboardIngest()` had no caller. `src/flightboard/fb_mqtt.cpp` subscribes to
the retained topic for the current selection and asks only when nothing arrives.
Three things decided whether it would work at all: PubSubClient's 256-byte
default buffer silently drops an oversized PUBLISH and a live board measures
1060 bytes; subscriptions do not survive a reconnect; and a retained payload
lands in milliseconds, so a request costs an AeroAPI fetch only when there is
genuinely nothing there. Verified against the live broker.

**A senior code audit ran, late.** It should have run before the pushes rather
than after. It returned CHANGES-REQUIRED with one CRITICAL and three HIGH, all
of which would have appeared on the first power-on: the AIS TLS handshake could
block `loop()` for up to 120 s against a 15 s watchdog with panic enabled;
PubSubClient's connect busy-waits without yielding, on every page; and two
pages never reset `setTextSize`, which the animated clocks leave at 3. All
fixed, along with eight MEDIUM findings.

**Two analysis documents.** [12](docs/12-bringup.md) is the gated bring-up
programme. [13](docs/13-code-practices.md) compares AnimatedPixelClock's
engineering against NickoScope32 V1b at code level — the conclusion is that
almost nothing transfers, and the one thing that does (a heap fragmentation
metric) has been sent to the phase-planning session.

### Open

- **Nothing is hardware-verified.** The panels have not arrived. The sequence is
  now written down: [docs/12](docs/12-bringup.md), eight gated phases.
- **Before wiring the encoder:** read the eFuse with `esptool.py summary`. The
  header pins are strapping pins, and GPIO45's VDD_SPI role should be void on
  this module because in-package flash and PSRAM fix that voltage — but that is
  UNVERIFIED, and if the eFuse is not burned a knob left in the wrong position
  at power-up stops the board booting.
- TLS session heap for the AIS websocket is not measured — runtime only.
- The yacht radar page is reachable only via the `httpForceYachtRadar` flag; no
  HTTP route or button yet.
- Older commits in the fork carry `nickol@me.com` in public history. Local
  config is fixed and the commits since have been clean; the rest need a
  force-push and the owner's decision.
- The panel schematic does not exist — searched and recorded in the
  [drawings README](reference-drawings/README.md), so nobody repeats it. The one
  thing it would have settled, the shift driver, is settled empirically in
  phase 2 instead.
- NickoScope-Watch still listens on the legacy `.../state` topic; the keyed
  `(apt, dir)` topic is published in parallel and the legacy publish can go once
  the watch migrates.
- `mic_power_rail` GPIO46 remains UNVERIFIED.
