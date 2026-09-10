# Handoff

Rolling record of where the work stands. Newest first.

---

## 2026-09-10

Twenty-three commits to the firmware, twenty-five here, plus sixteen on the
enclosure from the neighbouring session. Nothing has met hardware.

### The panel firmware went from nothing to three working pages

**Flight board**, fed over MQTT from Home Assistant. Live data broke three
things invented data never would have: character-by-character trimming turned
`EUROAIRPORT` into `EUROAIRPOR`; Picopixel's `U` is `V` with one extra row, so
`ZURICH` read `ZVRICH` across a quarter of the column; and AeroAPI's "city" is
the commune, `BLAGNAC` for Toulouse. All three fixed, the last by drawing the
IATA code unconditionally and the name as context.

**Yacht radar**, ported from NickoScope32. The first port drew fx34's
wireframe, which reads as noise on a raster panel. Rebuilt as a real chart:
land filled by scanline-filling the mainland ring, sea coloured by measured
GEBCO depth, land by measured EU-DEM elevation with a hillshade, baked at build
time into 8 KB of RGB565.

**Clock**, upstream's own, now driven by the knob.

**One encoder drives all three.** Rotate changes what the page is about, a
short press toggles its second axis, a long press leaves for the next page.

### Two corrections that cost a day between them

**The pin budget was counted, not read.** Free pins were derived from what the
firmware did not reference. The vendor schematic — downloaded on 2026-09-06,
read once, and **not kept** — says the expansion header is four pins, `IO45`,
`IO46`, `GND`, `3V3`, and that `IO10` is `RTC_INT` and `IO13` is `IMU_INT`. The
encoder designed that morning used exactly those two and could not have been
wired to a board at all. Drawings are now kept in `reference-drawings/` with a
fetch script and hashes.

**The audit ran after the pushes, not before.** One CRITICAL and three HIGH,
all of which would have shown on first power-on: a TLS handshake that can block
`loop()` for 120 s against a 15 s watchdog with `panic=true`; the same shape in
`PubSubClient::connect()`, and on every page rather than its own; and
`setTextSize` left at 3 by the animated clocks, which neither the style toast
nor the radar reset. All fixed.

### Lua, as preparatory work

The Watch's vendored Lua 5.4.8 came across as it stands — already the S3
adaptation, and deliberately without `io`, `os` or `package`. Phase 1 `nslua`
with it: stateless, PSRAM allocator, sandbox, two-million instruction budget.
**+91 KB flash, +80 bytes RAM**, measured with the self-test actually calling
it.

`tools/luasim` runs that same runtime on the host against a `px.*` raster API,
so effects can be written now: a Minecraft day/night cycle, a Tetris clock that
clears and rebuilds itself, a snake clock whose digits crawl away and back.
Previews committed beside the scripts, because a Lua effect has no other record
of how it reads.

### Open

- **Nothing is hardware-verified.** The panels have not arrived. Ten open
  questions and the gated sequence to settle them are in
  [12-bringup.md](docs/12-bringup.md).
- **The Lua bench is the gate that blocks everything built on the interpreter**
  — the heap and the HUB75 framebuffer both want PSRAM, whose bandwidth already
  caps the driver at ~13 MHz. Phase 6b.
- The two watchdog fixes have never run on hardware. Phase 6 exercises them.
- The pages are reachable only through the knob; no HTTP route, no button.
- Older commits in the fork carry `nickol@me.com` in public history. Local
  config is fixed and the last few were rewritten before pushing; the rest need
  a force-push and the owner's decision.
- NickoScope-Watch still listens on the legacy `.../state` topic; the keyed
  topic is published in parallel until it migrates.
- `mic_power_rail` GPIO46 — and note GPIO46 is now the encoder's B line, so
  this matters more than it did.
- **FYI, unconfirmed:** on R16V parts VDD_SPI is 1.8 V and GPIO47/48 run at
  1.8 V with it. Those two are this board's I2C bus. Read in the WROOM-1
  datasheet; confirm against WROOM-2 before designing anything onto it.
