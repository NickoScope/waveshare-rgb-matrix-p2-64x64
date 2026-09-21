# The panel's control map - the one file to read before touching it

**This file is the standing answer to "what can the panel do and how do I drive it".** It is
updated every time something is learned, added or broken. If you are about to work out how to
change a page, read a log or test a mode, the answer is here - do not rediscover it.

Panel: firmware **2.5.0**, `NickoScope-64x128.local`, **192.168.4.62** (measure by IP: the mDNS name costs 5.0 s of
name lookup per request on this Mac against 0.0008 s by IP). Branch `fix/portal-heap`, which is
`feat/fx3d` plus the portal-hang fix and the network log. Serial: `/dev/cu.usbmodem2101`, 115200 -
now optional, see the log over the network below.

## How to change what is on the screen

**`POST /api/panel {"showPage": N}`** - this is the way. 16 pages, listed below.
`GET /api/panel` returns everything: `now` (the page and style showing right now), `pages`,
`styles`, `carousel`.

```bash
curl -s -X POST -H 'Content-Type: application/json' -d '{"showPage":7}' http://192.168.4.62/api/panel
curl -s http://192.168.4.62/api/panel | python3 -c 'import sys,json;print(json.load(sys.stdin)["now"])'
```

`GET /api/panel` → `now`: `{page, key, name, notify, style, styleName, entered, hz}`.

| # | Page | key |
|---|---|---|
| 0 | CLOCK | clock |
| 1 | FOOTBALL CLOCK | (lua) |
| 2 | MINECRAFT | (lua) |
| 3 | ROOM RADAR | (lua) |
| 4 | SNAKE CLOCK | (lua) |
| 5 | SNOOKER CLOCK | (lua) |
| 6 | TETRIS CLOCK | (lua) |
| 7 | WORLD CLOCK | world |
| 8 | FLIGHTS | |
| 9 | TRAINS | |
| 10 | MARKETS | |
| 11 | TICKER | |
| 12 | PORTFOLIO | |
| 13 | HOLDINGS | |
| 14 | YACHTS | |
| 15 | MEDIA | |

**Clock styles: `POST /api/panel {"style": N}`** - the key is `style`, not `styleId`, and this
file said `styleId` until 2026-09-21. **`{"styleId":N}` answers `HTTP 200` and does nothing**,
exactly like `{"showPage":N}` before it. The firmware's own header is the authority:
`src/web/web_panel.cpp:10` reads `POST /api/panel {"show":{"page":i[,"card":"name"]}} | {"style":id}`.
There is no `POST /api/clock/style` - that route answers 404 to a POST. `styles[]` in the same
reply gives the ids and names (0 = MARIO ... 14 = WEATHER).

```bash
curl -s -X POST -H 'Content-Type: application/json' -d '{"style":14}' http://192.168.4.62/api/panel
```

**What the wrong key cost:** a whole night of believing the network broker was not being asked
for data (`served: 0`), when in truth the weather page had never once reached the screen, because
every attempt to select its clock style was a silent no-op that reported success.

**The carousel** walks pages and styles on its own: `carousel` = `{enabled, idleS, slotS,
allStyles, running, holdS, pageS, secs}`. Measured live: `idleS` 165, `slotS` 60, `allStyles`
true. So left alone the panel shows everything by itself, one slot a minute. `POST /api/panel`
with a `carousel` object changes it.

## Every HTTP route the firmware registers

Extracted from the source, both `server.on(...)` **and** the `route(...)` helper in
`src/web/web_panel.cpp` - a grep for `server.on` alone misses half of them, which has cost this
project two wasted test sweeps.

| Route | What it is for |
|---|---|
| `/` `/portal.css` `/portal.js` `/panel.css` `/panel.js` `/favicon.*` | the portal, gzip from PROGMEM |
| `/api/info` `/api/diagnostics` `/api/status` `/metrics` | **the diagnostics - start here** |
| `/api/panel` | pages, styles, carousel; `showPage`, `styleId` |
| `/api/knob` | the knob's *settings* (reverse, lockout, debounce, detent) - **not** knob actions |
| `/api/mode/clock` `/ambient` `/viz` `/auto` | force a mode, or give it back |
| `/api/display/on` `/off` `/brightness?value=0..255` | the screen |
| `/api/clock/style` | the clock style |
| `/api/fx3d` `/fx3d` | the 3D scenes and looks (docs/27) |
| `/api/lua` | the Lua effects |
| `/api/worldclock` `/api/flightboard` `/api/railboard` `/api/market` `/api/yachtradar` `/api/media` | each data page's own settings |
| `/api/anim/list` `/play` `/upload` `/delete` | the animation player |
| `/api/clips` `/api/clips/frame` `/api/clips/upload` | SD clips |
| `/api/notify` `/api/notify/dismiss` | the notification overlay |
| `/api/climate/pause` `/api/presence/mirror` `/api/ntptest` | the sensors, the clock's sync |
| `/api/ir/sim` `/learn` `/clear` `/cancel` | the IR slots |
| `/api/portal` `/save` `/api/export` `/api/import` `/api/rename` `/reset` | settings |
| `/update` | OTA - **wait for `ota.state` to read `valid` before any reboot** |
| `/api/reboot` | restart |

## What the diagnostics tell you

`GET /api/info` - the fields that matter when something is wrong:

| Field | Reads |
|---|---|
| `freeInternalHeap`, `largestHeapBlock`, `minFreeHeap` | internal RAM; the board has ~34 KB free at rest |
| `allocFails`, `allocFailBytes`, `allocFailTask` | **the first place to look for a hang** - task `wifi` means the radio went short |
| `loopMaxMs`, `loopSlowPart`, `loopSlowPartMs` | the longest `loop()` pass in the last 10 s, and which part |
| `linkRecoveries`, `lastLinkRecovery` | the Wi-Fi watchdog firing |
| `lastCrash` | the crash report from NVS - `thisBoot` says whether it is this run's |
| `resetReason` | 1 = power-on, 3 = software, 4 = panic, 5 = interrupt watchdog, 6 = task watchdog |
| `ota` | `partition`, `state` (`pending` until 60 s, then `valid`), `rolledBackFrom` |

## The log over the network (firmware 2.5.0)

The panel keeps its own log and hands it out over HTTP. **Off by default and
free while off** - no buffer, no hook. On, it uses 32 KB + 1 KB of **PSRAM**,
never internal RAM, so turning it on cannot change what it is there to observe.
The switch is kept in NVS and survives a reboot, which is the point: an
intermittent fault is caught across the restart it causes.

```bash
curl -s "http://192.168.4.62/api/log?on=1"                 # on
curl -s "http://192.168.4.62/api/log?since=0"              # read from the start
curl -s "http://192.168.4.62/api/log?clear=1"              # empty it, in place
curl -s "http://192.168.4.62/api/log?on=0"                 # off, buffer freed
```

Read with a cursor: `X-Log-From` is where the answer really starts (larger than
you asked means lines were dropped while you were away), `X-Log-Bytes` is the
body's length **in bytes** - never measure it as a string length - `X-Log-Seq`
is the panel's total, `X-Log-Dropped` what it threw away. A read is capped at
1 KB, so drain a burst in a loop rather than in one request.

In the portal: **Device status → Log over the network** - the switch, Follow,
Clear, and a view that reports a gap rather than hiding it.

**What it captures:** everything written through `dbgLogf`/`dbgLogWrite` - the
`[mem]`, `[loop]` and `[net]` lines - and the IDF's own `ESP_LOGx`.
**What it does not:** Arduino's `log_e`/`log_w`. In this build those expand to
`ets_printf` and never reach the hook, so a line like `WebServer.cpp:638
request handler not found` goes to the cable only. Capturing them needs the
whole firmware built with `-DUSE_ESP_IDF_LOG`, which rewrites every log line's
format - a change of its own.

## Serial

`/dev/cu.usbmodem2101` at 115200. The lines worth grepping: `[mem]` (heap minimum falling,
allocation failures with the task name), `[loop]` (any part over 200 ms), `[luafx]` (each Lua
effect's frame times), `[audio]`, `[fx3d]`, `[ir]`.

There is also a **serial console** in `src/ir/ir_console.h`: `ir status`, `ir help`, `ir cw [n]`,
`ir ccw [n]`, `ir ok [hold_ms]`, `ir cancel`. **It accepts the commands and does nothing** in this
build - see the broken list below.

## Known broken, as of 2026-09-20

| What | Symptom | Where |
|---|---|---|
| ~~Concurrent portal requests~~ | **fixed in 2.5.0** (`fix/portal-heap`): 8 KB of contiguous internal RAM is held for the radio's recovery and given up the moment it starts failing, and the expensive routes are refused while it is. 30 of 30 rounds of the test that used to wedge the panel; worst response 0.17-0.31 s against 25 s and death | `drafts/28-portal-hang-2026-09-20.md` |
| The audio visualizer | starting it costs 9.4 KB internal and the memory is **not** released when the mode is left | debt D1 |
| ~~`ir cw`/`ir ok` on serial~~ | **they work — corrected 2026-09-21.** `ir cw 1` turned the knob and changed the clock style; the whole station picker below was verified with them and nothing else. Only `/api/ir/sim` over HTTP is inert (IR `enabled:false`, `receiver:"not built"`); the serial console is not | `src/ir/ir_console.h` |
| `/api/notify?text=..&seconds=..` | HTTP error, serial says `request handler not found` - the parameters are not these | - |
| The animation player | `/api/anim/play?name=...` answers ok, `animationPlaying` stays false | needs eyes on the screen |
| ~~The weather~~ | **not broken - corrected 2026-09-21.** Measured after a power cycle on `fix/panel-tonight`: `weatherValid:true`, `weatherAgeSeconds:140`, a fresh fetch two minutes after boot. The earlier `weatherValid:false` entry was a state, recorded as a fault | - |
| Yacht radar | failed a 12,288 B internal allocation under memory pressure | - |
| Lua clock styles | `tetris_clock` 286 ms worst frame, `snake_clock` 180 ms, `snooker_clock` 325 ms to open - each one freezes the portal while it runs | - |
| MQTT | 528 ms worst pass, 1,001 ms every pass once the link is wedged | - |
| The radio under load | `allocFails` climbs steadily (task `wifi`, 1,626 B DMA buffers) whenever the panel is driven hard - 8 to 89 over two functional sweeps. Nothing fails visibly and the link never drops, but the shortage is real and its cause is the 131 KB HUB75 framebuffer that cannot move | docs/32 |

## The indoor sensor reads its own heat, and the offset that corrects it

The SHTC3 sits inside the enclosure beside the LED matrix and the ESP32, so it
reads the panel, not the room. Measured 2026-09-21: sensor **32.3 °C** against a
room at **24**, an offset of **-8.7 °C**, set in the portal under Display ->
Indoor sensor -> "Temperature offset, °C" (`climateTempOffset`, tenths, in NVS).

Humidity corrects itself and should be left alone: `climateRhFollowsT` is on by
default, so the same air recomputed at 23.6 °C reads **69.6 %RH** where the
sensor said 41.9 - the water in the air did not change, only the temperature it
is measured at.

**This is one point of calibration, not a model, and it will drift.** Self-heating
depends on screen brightness, on what is being drawn and on the room itself.
Calibrated at one minute, at one brightness: at night with the screen dimmed the
panel will read COLDER than the room, and in a hot room the offset will be too
small. Doing it properly means readings at several brightnesses and, if the
offset tracks brightness, computing it rather than storing a number.

Written down because it lives only in NVS: a wipe loses it and nothing else
records what it was or why.

Read it back: `GET /api/info` -> `climate` -> compare `sensorTempC` with `tempC`.

## The knob on the rail page, and the station list

**Click walks the stops, turn acts where you stopped** - the same shape the media
and market pages use. There is no long press anywhere in this firmware:
main.cpp folds `CTRL_LONG` into `CTRL_PRESS` deliberately, "held a little too
long, it is still a click". A second thing to control is another stop, never
another gesture.

| click | stop | what a turn does |
|---|---|---|
| 1 | LISTS | departures → arrivals → diagnostics |
| 2 | STATION | steps through the favourites, **changing the station at once** |
| 3 | out | walks pages |

The STATION stop does not exist while the list is empty - a stop where the knob
does nothing is worse than one fewer stop.

**The list is data in NVS, not code.** Up to eight, surviving reboots and
reflashes. There is no portal for it: the owner had the station controls removed
from the portal on 2026-09-20, and this replaces them.

```bash
curl -s -X POST -H 'Content-Type: application/json' \
  -d '{"favourites":["GLD","WAT","CLJ","WOK","SUR"]}' http://192.168.4.62/api/railboard
```

**The owner's five, set 2026-09-21:** `GLD` Guildford (home), `WAT` London
Waterloo, `CLJ` Clapham Junction, `WOK` Woking, `SUR` Surbiton. Written down
here because an NVS wipe loses them and nothing else records what they were.

Read them back with `GET /api/railboard` → `favourites`. **Do read them back**:
the first POST of this list answered `HTTP 200` and looked like it had stored
nothing, because the reporting field was in the wrong file. The store had worked.

**Testing it without hands:** the serial console drives the knob for real -
`ir ok` for the button, `ir cw 1` / `ir ccw 1` for detents. The whole picker was
verified that way.

## Driving it from a script instead of by hand

`tools/nsc/nsc.py` - one command, one JSON object on stdout, an exit code that
means something (0 done · 1 retryable · 2 bad call · 3 **a person must look** ·
4 pointless to retry). `nsc status`, `nsc budget`, `nsc page N`, `nsc style N`,
`nsc doctor --firmware <checkout>`. The shape is MicroPixel's, and why is
docs/33-one-cli-json.md.

Two things it does that reading this file cannot: **a command that changes
something reads the state back** (which is how the `{"styleId"}` no-op above
was finally caught), and an "ok" that only means "it was already in that state"
raises an `already_in_state` warning, because a verification that cannot fail
is not a verification.

`tools/nsc/functional.py` is this document as an executable sweep: all 16
pages set and confirmed, the clock styles, every board's data, the portal's six
assets, the four diagnostics routes, and the link-recovery and crash counters
compared before and after. **41 checks, all passing, 2026-09-21** on
`feat/net-broker`. Run it without a pipe - `python3 functional.py` - because a
pipeline hands you the exit code of the last command in it, not of the test.

## Mistakes this file exists to prevent

- **Grepping only `server.on` for the route list.** Half the API is registered through `route()`
  in `src/web/web_panel.cpp`. Because of that, `docs/drafts/28-portal-hang-2026-09-20.md` first
  claimed the knob-only pages could not be driven over HTTP. **That was wrong** - `POST
  /api/panel {"showPage":N}` drives every one of them, and all 16 were swept that way afterwards
  with no new allocation failures.
- **Driving the panel through `/api/ir/sim`.** It reports success and does nothing. Two sweeps
  were lost to it.
- **Measuring through the mDNS name.** Five seconds a request.
- **Rebooting after an OTA before `ota.state` reads `valid`.** The image rolls back and the test
  then measures the old firmware.
