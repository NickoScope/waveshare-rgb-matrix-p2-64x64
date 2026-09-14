# Handoff

Rolling record of where the work stands. Newest first.

## Open, across everything

- **The hardware arrived on 2026-09-14.** Phase 1 passed after a memory-type
  fix (octal flash); phase 2, one panel, is next. The open questions and the
  gated sequence are in [12-bringup.md](docs/12-bringup.md).
- **Phase 6b is the gate that blocks everything built on Lua** — the heap and
  the HUB75 framebuffer both want PSRAM, whose bandwidth already caps the
  driver at ~13 MHz, and nobody has measured what happens when they share.
- The two watchdog fixes have never run on hardware. Phase 6 exercises them.
- Cards, icons and the carousel are proven on the wire and drawn only on the
  host. Phase 6c.
- The world clock matches its Lua prototype pixel for pixel on the host and
  has never seen NTP time on the board. Phase 6d.
- **Presence: an Apollo MTR-1 is bought, the encoder stays.** Two stages in
  [16](docs/16-presence-radar.md); nothing built on the panel side.
- The pages are reachable only through the knob; no HTTP route, no button.
- NickoScope-Watch still listens on the legacy `.../state` topic; the keyed
  topic is published in parallel until it migrates.
- `mic_power_rail` GPIO46 — and GPIO46 is now the encoder's B line, so this
  matters more than it did.
- **FYI, unconfirmed:** on R16V parts VDD_SPI is 1.8 V and GPIO47/48 run at
  1.8 V with it. Those two are this board's I2C bus. Read in the WROOM-1
  datasheet; confirm against WROOM-2 before designing anything onto it.

---

## 2026-09-14, afternoon — the hardware is on the desk

- Controller and panels arrived. Supply 5 V 10 A; the controller runs from its
  USB socket.
- **Phase 1 passed after one fix.** Every image boot-looped at first: the env
  said `qio_opi`, and the WROOM-2's flash is octal. Now `opi_opi`; `provision`
  boots and prints over USB-CDC (question 3). `VDD_SPI_FORCE = True` read off
  the chip (question 4b).
- The bring-up image had stopped linking unnoticed (two `setup()`s). Fixed; the
  flag matrix now builds both bring-up images, 16/16.
- The board has two USB-C sockets, USB and POWER; not yet traced which feeds what.

**Next:** the two rail measurements, then phase 2 with one panel.

---

## 2026-09-14, after midnight

- Room radar drawn in the simulator (`room_radar.lua`): the LD2450's own fan,
  trails, entry bursts, rings round people sitting still, dims when empty.
- Radar hardware decided: **Apollo MTR-1** (LD2450 + ESP32-C3, ESPHome), bought.
  The knob keeps IO45/IO46. It also brings a light sensor, which can drive
  the panel's brightness, and CO2.
- GPIO45 settled from the WROOM-2 datasheet: VDD_SPI is fixed by eFuse on this
  module, so the strap is ignored. Found while being inconsistent about it;
  the owner caught that. `esptool.py summary` in the bring-up was not a real
  command — it is `espefuse.py summary`.

- Bring-up plan updated: questions 4b answered and 14–17 added, new phase 6e
  for the MTR-1 (the radar alone in HA first, then presence driving sleep and
  wake, then the live room radar), flash figure and flag matrix brought current.

**Next:** when the MTR-1 arrives, phase 6e from the top: the radar alone in
Home Assistant, then an HA automation to `nickoscope_matrix/presence` and
`src/presence/` on the panel. When the panels arrive, phase 0.

---

## 2026-09-13, late

The dotted world map clock went from a simulator script to a firmware page.

- `src/worldclock/` in the fork: the page after the clock on a long press, 20 s
  in the carousel, 10 fps. Cities: Cannes (home, breathes), Moscow, New York,
  London, Dubai, Almaty.
- One source: `tools/luasim/gen_world.py` writes the land mask and cities into
  the Lua script and the firmware header; `--check` compares them offline and
  the pre-commit hook runs it. Shown to fail on a one-digit change.
- Checked: C module on the host vs the Lua frame, 0 of 8 192 pixels differ.
  Flag matrix 14/14. +2 284 B flash, +4 096 B RAM against the same build
  without the flag.
- New bring-up phase 6d and question 13.
- Idea written down, not built: a 24 GHz presence radar so effects wake when
  someone walks in — [16](docs/16-presence-radar.md). The model the owner
  remembers as "2050" was not found; LD2450 or LD2410C, told apart by size.

**Next:** panels. Then measure the radar board, and try option A (through Home
Assistant) before soldering anything.

---

## 2026-09-12

Read the Ulanzi TC001/TC002 and the AWTRIX firmware that made the first one
worth owning, then built the five ideas worth taking. None of it runs on our
hardware — AWTRIX is nailed to a 32 × 8 WS2812 matrix — so this was an ideas
read. Notes in [15-ulanzi-awtrix.md](docs/15-ulanzi-awtrix.md).

### What went in

**Cards.** Home Assistant publishes to `nickoscope_matrix/card/<name>` and a
page appears; an empty payload removes it. Title, text, colour, a progress bar,
an icon, and `lifetime` so a page whose source died takes itself away rather
than lying about last Tuesday. Cards join the knob's page walk as they arrive.

**Notifications.** `nickoscope_matrix/notify` takes the whole screen, with
`hold` so a doorbell waits for a press.

**Icons.** 16 × 16 rather than AWTRIX's 8 × 8 — theirs is sized for a 32 × 8
display. 512 bytes of raw RGB565 in one retained message, written atomically
through a temp file and a rename.

**A carousel.** The pages advance after a minute of no knob activity; touching
the knob puts you back in charge. No new gesture, no setting.

**A shared MQTT bus.** `src/mqtt/mqtt_bus` owns the one connection. A second
client would have opened a second socket to the same broker, and the bus also
fixes a bug the flight board had alone: subscriptions do not survive a
reconnect, so the bus remembers the set and re-applies it. `fb_mqtt` went from
160 lines to 84.

All five cost **8.4 KB of flash and 2.1 KB of RAM**. Cards and icons were
round-tripped against the live broker; the drawing has been done only on the
host.

### The lesson of the day, and it is an uncomfortable one

**Every flag-combination check run on 2026-09-10 was worthless.** The command
used, `platformio run --project-option=...`, is not an option in this
PlatformIO: it exited with "Error: No such option", and the grep for `error:`
did not match that capital E, so it printed OK for builds that never happened.
The claim in `d44bb3b` that six combinations still compiled had never been
tested.

`tools/flag_matrix.py` now does it by writing a scratch env and checking the
return code, which cannot be fooled. It found three real breaks the moment it
ran, and it also asserts that three dependency guards *refuse* to build — a
guard that silently passes is worse than no guard. Twelve combinations.

Two smaller ones the same day: a size claimed in a commit message without being
computed (7.6 KB against a real 2 240 bytes, corrected), and a host renderer
that used top-of-line coordinates while the firmware used baselines, which drew
a rule straight through a title. The renderer caught the second before hardware
could.

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

### Closed late in the day

**The fork's public history no longer carries a personal address.** Five
commits still had `nickol@me.com`; rewriting them changed the SHA of all
twenty-three of ours, so the branch was force-pushed. Four things were checked
before and after: the tree hash is identical, so no content moved; the merge
base with `upstream/main` is still `74f964b`, so it is still a fork and a pull
request upstream is still possible; no document referenced any of the old SHAs;
and it still builds. A backup tag `backup/pre-email-rewrite` is kept locally.

