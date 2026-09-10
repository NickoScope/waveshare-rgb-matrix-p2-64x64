# Upstream contribution roadmap: AnimatedPixelClock

Working list of changes worth proposing to
[Keralots/AnimatedPixelClock](https://github.com/Keralots/AnimatedPixelClock) (MIT), the
128x64 HUB75 clock firmware documented in [06-projects.md](06-projects.md).

Our fork: [NickoScope/AnimatedPixelClock](https://github.com/NickoScope/AnimatedPixelClock).

**House rule for everything below: open an issue before writing code.** The author is
active (three releases in four days as of 2026-09-09), so a short exchange costs nothing and
prevents building the wrong shape.

## The binding constraint: flash on the 4MB board

Measured on commit `74f964b`, arduino-esp32 2.0.17 via espressif32@6.12.0:

| Environment | Board | Flash used | Free |
|---|---|---|---|
| `matrix-s3` | S3-Zero / Super Mini, 4MB, `min_spiffs` | **82.0%** (1 612 729 of 1 966 080 B) | ~345 KB |
| `matrix-s3-wroom` | WROOM-1 N16R8, 16MB | 24.8% (1 627 549 of 6 553 600 B) | ~4.8 MB |
| `matrix-waveshare-rgb` | Waveshare ESP32-S3-RGB-Matrix | 24.6% (1 613 785 of 6 553 600 B) | ~4.8 MB |

The compact build is the one to respect. **Any feature that adds more than a token amount of
flash has to be optional at compile time and off by default on `matrix-s3`**, or the author
loses the 4MB target. Lead any proposal with this, not with the feature.

---

## 1. Make the HUB75 pin map configurable

**Status:** partially implemented on our branch `board/waveshare-esp32-s3-rgb-matrix`.
**Effort:** small. **PR readiness:** high, this is the obvious first one.

Today the pin map is a literal inside `makeMatrixConfig()` in `src/display/matrix_display.h`,
duplicated in `bringup/hello_matrix.cpp`. Because of that, the prebuilt images behind the web
flasher only work on the author's two wiring variants. Anyone with different wiring has to
build from source, which defeats the point of shipping a browser installer.

Turning the map into board profiles selected by a build flag costs almost nothing, removes
the duplication between firmware and bring-up sketch, and makes every future board a
`platformio.ini` entry rather than a source edit.

**Why the author should want it:** it grows the audience of the web flasher, which is clearly
something he invested in.

## 2. Waveshare ESP32-S3-RGB-Matrix board support

**Status:** implemented on our branch, builds clean, not yet run on hardware.
**Effort:** small once #1 lands. **PR readiness:** high, but hardware-verify first.

Follows directly from #1: one `platformio.ini` environment plus one pin set. Verified against
Waveshare's own BSP and example sources, see [02-controller.md](02-controller.md).

Worth mentioning in the PR body: this board carries an SN74HC245 buffer on the HUB75 lines,
so the 3.3V-drive caveat in the project's wiring guide does not apply to it. That is a
genuine difference from the hand-wired builds, not just a different pin list.

**Do not send this before the panels arrive.** A board-support PR that the submitter has
never run is not worth the author's review time.

## 3. MQTT with Home Assistant discovery

**Effort:** medium. **PR readiness:** discuss first, this is the one most likely to be
declined on scope grounds.

The firmware already exposes everything Home Assistant would want, over HTTP:
display on/off, brightness, mode, clock style, and a notification banner. What is missing is
the transport that makes Home Assistant create those controls **by itself**, rather than the
user hand-writing `rest_command` entries.

MQTT discovery is that transport. The device publishes retained config payloads under the
`homeassistant/` prefix at boot, and Home Assistant materialises a device with entities.

Natural mapping onto what already exists:

| HA entity | Backed by |
|---|---|
| `switch` or `light` | display on/off, brightness |
| `number` | brightness 0-100 |
| `select` | clock style, 15 options |
| `select` | mode: clock / ambient / visualizer |
| `text` or a button | notification banner, the existing `/api/notify` |
| `sensor` | IP, RSSI, uptime, current mode |

**The argument that makes this a good PR rather than feature creep:** it is a second
transport over the control layer that already exists, not new behaviour. The same functions
that serve the HTTP endpoints answer the MQTT topics. Precedent is strong in this niche:
AWTRIX 3 and PixelIt both do MQTT discovery and it is the main reason people pick them for
Home Assistant.

**Design constraints to state up front in the issue:**

- Optional at compile time, `-DMQTT_ENABLED`, **off by default on the 4MB `matrix-s3` env**
  where only ~345 KB of flash remains. PubSubClient is small, but discovery payloads are
  JSON strings and they add up.
- Last Will and Testament for availability, otherwise entities go stale instead of
  unavailable when the device drops off.
- Retained discovery configs, published once on connect, with a clean removal path.
- Reuse the existing `deviceName` for the topic prefix and the mDNS name, so one setting
  drives all three identities.
- Credentials belong in the existing web config portal, not in `user_config.h`.

## 4. Audio visualizer from an onboard microphone

**Effort:** medium to large. **PR readiness:** discuss first.

The 32-band visualizer currently depends on the desktop companion streaming PC audio over
UDP on port 4210. That is a hard dependency on a running computer.

Boards with a microphone could feed the same visualizer locally. The Waveshare
ESP32-S3-RGB-Matrix has two microphones plus an ES7210 with echo cancellation, and the
Adafruit MatrixPortal S3 has one as well, so this is not a single-board special case.

Structurally it is additive: a second source feeding the existing band data, selected at
runtime, with the UDP path untouched. Whether the author sees that as a welcome option or as
a fork's business is exactly what the issue is for.

## 6. Airport flight board page

**Effort:** medium, but far less than it looks. **PR readiness:** low — this is fork
territory, and deliberately so. It is the most valuable item here for us, and the least
likely to belong upstream.

### Why it is cheap: the whole pipeline already exists

This is not a new feature to design. It is a **second renderer for a contract that is
already deployed and debugged** in this household. Home Assistant already serves an
airport board over MQTT for a NickoScope32 device; the matrix becomes another subscriber.

**Request:** publish to `nickoscope_watch/flightboard/req`

```json
{"apt": "LFMN", "dir": "arr"}
```

`apt` is validated against a six-airport whitelist (LFMD, LFMN, LFPG, EGLL, EDDF, EHAM),
`dir` against `dep` / `arr`. Anything else is ignored.

**Response:** retained on `nickoscope_watch/flightboard/state`

```json
{"apt":"LFMN","dir":"arr","n":15,"upd":"08:18","now_idx":7,
 "f":[{"fn":"LH1064","tm":"18:07","st":"land","ct":"FRA"}, …]}
```

Four fields per flight: flight number, local time, status, city code. The HA side already
merges past and scheduled flights, de-duplicates on `fa_flight_id`, clips to a ±2 h window,
sorts by time, and returns 15 rows with `now_idx` pointing at the first flight still in the
future. Throttle is 90 s per (airport, direction) pair, and the automation's own notes put
the API cost at roughly one cent per fetch.

Closed status vocabulary, which is what makes colour coding safe:

| `st` | Meaning | Suggested colour |
|---|---|---|
| `sched` | scheduled | white |
| `board` | boarding | cyan |
| `dep` | departed | blue |
| `land` | landed | green |
| `delay` | delayed over 15 min | amber |
| `canc` | cancelled | red |

**The device does no API work, holds no credentials, and parses a few hundred bytes.**
Contrast that with the raw sensor attributes, which carry up to 50 flights with ~20 fields
each and are heavy enough that the integration's own docs tell you to exclude them from
the HA recorder.

### Layout, borrowed from the existing Lua scene

A split-flap board for this data already exists as `airport.lua` on the NickoScope32
vector display. Its layout decisions transfer directly and were made against real data:

- four columns: flight, city, time, status
- city truncated to 10 characters
- arrivals and departures alternate automatically on wall-clock seconds, on a **20 s
  period** — chosen because 60 is divisible by it, so the switch never jitters at the
  minute boundary
- when the list is longer than the visible band it scrolls continuously and wraps, about
  1.6 s per row, driven by milliseconds so the motion stays smooth

On 128 x 64 with a 4x6 font you get 25 characters per line and 8 rows at 8 px, or 6 rows at
10 px. `LH1064 FRANKFURT 18:07` is 22 characters, so a header plus six flight rows fits
with the status carried by **row colour instead of a text column**. That is both narrower
and more readable across a room than the `ST` column the vector version needs.

Highlight the row at `now_idx`: it is the whole point of the ±2 h window.

### What the matrix gains over the existing implementation

The Lua scene carries an honest limitation in its own header comment: the `beam` module
exposes only `scene`, `now` and `t`, so the flight list is a **snapshot frozen at upload
time**. Making it live requires a bridge process to re-render and re-upload the scene, and
that bridge is currently blocked by macOS withholding local-network access from launchd
agents.

**None of that applies here.** The ESP32-S3 subscribes to MQTT directly: data is live, no
bridge, no re-upload, no permission grant, no LittleFS wear from rewriting a scene every
time the board changes. Plus colour, which a vector CRT does not have.

So this page closes, on different hardware, a debt recorded as unsolvable in NickoScope32
without firmware changes on both of its controllers.

### Design decision: per-key response topics

`nickoscope_watch/flightboard/state` was a single retained topic serving every consumer, so
two devices wanting different airports overwrote each other. **Decided 2026-09-10: the panel
gets its own airport selector, and the response topic is keyed by the data rather than by
the client.**

```
nickoscope_watch/flightboard/state/<apt>/<dir>     e.g. .../state/LFMN/arr
```

Keying on the client was considered first and rejected. It fixes the *display* conflict but
not the *fetch* conflict: Home Assistant has one pair of AeroAPI sensors and one
`input_select.flight_board_airport` shared by everything, and the existing throttle only
short-circuits when `age < 90 s` **and** the currently selected airport matches the request.
Two clients on different airports never satisfy that, so each request flips the input_select
and pays for a fresh fetch. Per-client topics would have doubled the API spend while looking
like they solved the problem.

Keying on `(apt, dir)` instead gives four properties at once:

| Property | Result |
|---|---|
| Display conflict | gone, each airport has its own topic |
| Cache | the retained value *is* the cache, no extra store needed |
| Throttle | works again, the topic key matches the throttle key |
| Two devices, same airport | share one fetch instead of paying twice |

Backward compatibility is one extra publish action: keep writing the legacy `.../state` as
well until the watch is moved over.

**Device behaviour.** Subscribe to the topic for the selected airport and direction. On a
selector change, subscribe to the new topic — the retained value arrives immediately, so the
board is populated before any request goes out. Only publish a request when the retained
payload is missing or its `upd` field is stale. That keeps the panel almost entirely passive
and off the API budget.

### Open questions

1. ~~Passive subscriber or own selector~~ — **decided: own selector, per-key topics**
2. ~~Physical airport selector on the panel~~ — **decided: yes.** It lands in the 20 mm
   bottom strip of the enclosure; the enclosure spec has been notified
3. Split-flap character animation or plain redraw on change: the flip is the signature look,
   but it costs a per-glyph animation state machine
4. Behaviour when the retained payload is stale — the `upd` field carries the HA-side time,
   so the page can grey out or show an age indicator rather than lying

### Sequencing

Independent of items 1 to 4: it needs no upstream change and no MQTT work in the firmware
beyond a client, since the transport already exists. It can be built in the fork as soon as
the panels arrive and the display is proven.

---

## 5. Single 64x64 panel layouts

**Effort:** large. **PR readiness:** low, probably fork territory.

All fifteen clock styles are laid out for a 128-wide canvas. Setting `HUB75_CHAIN` to 1
produces a working 64x64 display with cropped artwork. Making the styles adapt is a redesign
of the project's visual identity, not a feature, and it is reasonable for the author to
decline it.

Only relevant to someone with a single panel. Not our case: four panels and two controllers
means two full 128x64 builds.

---

## Sequencing

1. Panels arrive, flash `matrix-waveshare-rgb-bringup`, confirm the pin map on hardware.
2. Open an issue proposing #1, referencing the branch as a worked example.
3. Land #1 and #2 together or back to back.
4. Only then raise #3 and #4, one issue each.

Item 6 sits outside that chain. It is fork work, gated only on hardware, and it is the
fastest thing here to get running because the protocol, the data and the layout all exist
already.

Sending a large feature before the small structural one has landed is the usual way these
contributions stall.
