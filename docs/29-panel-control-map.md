# The panel's control map - the one file to read before touching it

**This file is the standing answer to "what can the panel do and how do I drive it".** It is
updated every time something is learned, added or broken. If you are about to work out how to
change a page, read a log or test a mode, the answer is here - do not rediscover it.

Panel: firmware **2.5.0**, `NickoScope-64x128.local`, **192.168.4.62** (measure by IP: the mDNS name costs 5.0 s of
name lookup per request on this Mac against 0.0008 s by IP). Firmware 2.4.0, branch `feat/fx3d`
`26a1be4` at the time of writing. Serial: `/dev/cu.usbmodem2101`, 115200.

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

Clock styles: `POST /api/panel {"styleId": N}`, or `/api/clock/style`. `styles[]` in the same
reply gives the ids and names (0 = MARIO ... 14 = WEATHER).

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
| `/api/ir/sim`, and `ir cw`/`ir ok` on serial | answer success, change nothing (IR `enabled:false`, `receiver:"not built"`) | - |
| `/api/notify?text=..&seconds=..` | HTTP error, serial says `request handler not found` - the parameters are not these | - |
| The animation player | `/api/anim/play?name=...` answers ok, `animationPlaying` stays false | needs eyes on the screen |
| The weather | `weatherValid:false` since boot; retries every 60 s, each a TLS handshake from internal RAM | `feat/tls-buffers-psram` unmerged |
| Yacht radar | failed a 12,288 B internal allocation under memory pressure | - |
| Lua clock styles | `tetris_clock` 286 ms worst frame, `snake_clock` 180 ms, `snooker_clock` 325 ms to open - each one freezes the portal while it runs | - |
| MQTT | 528 ms worst pass, 1,001 ms every pass once the link is wedged | - |

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
