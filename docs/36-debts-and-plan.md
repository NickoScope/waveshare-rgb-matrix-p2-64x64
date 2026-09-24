# 36. Debts and plan

One list of what is owed and what comes next. Each item links to the document
that holds its detail; this file does not repeat that detail. Newest decisions
first. Started 2026-09-23 at the owner's request: "запиши в долги и план работы".

## Plan: next up, in the owner's order

| # | What | Status | Detail |
|---|---|---|---|
| P1 | **System corners on every screen.** Left: A/M, the carousel on (auto) or the pages changed by hand (manual). Right: a Wi-Fi icon coloured by signal level. While the remote is received, the right corner blinks a red dot instead of the icon. | **done** 2026-09-23 21:34, the owner: "работает". main b0684a4, in 2.5.8 (dev). The "entered" mark moved into the left corner as an amber arrow | AGENTS.md "The system corners"; `src/display/sys_corners.h` |
| P2 | **The panel in Home Assistant over MQTT discovery.** One device with its availability (LWT) and these entities: <ul><li>`light`: display on/off and brightness</li><li>`select`: page and clock style</li><li>`switch`: carousel</li><li>`number`: slot time</li><li>`button`: next and previous</li><li>`text`: notification</li><li>sensors: now showing, mode</li><li>diagnostics: version, uptime, RSSI, heap, DMA free, link recoveries, alloc fails, reset reason</li><li>`update`: `latest_version` published by the panel</li></ul> The firmware already knows every one of these values (`/api/status`, `/api/panel`, `/api/info`). The HA dashboard `/led-panel/panel` has sections waiting for them. | **later**, the owner's word 2026-09-23 21:19 ("так сделаем, но позже") | HANDOFF 2026-09-23 21:15; the dashboard agent's report |
| P3 | **Release 2.5.8.** Contents so far: the remote's arrows and brightness step once per press; the remote's brightness is kept across a reboot; brightness readings in `/api/info`. P1 is in it. | **released** 2026-09-23 21:49: https://github.com/NickoScope/AnimatedPixelClock/releases/tag/v2.5.8; the flasher serves it | [24](24-ir-remote.md) "Soldered and tried" |
| P4 | **A bare HLK-LD2450 module wired straight to the panel over UART.** This is the radar module alone, with its own UART and no ESP32; the MTR-1 stays on Home Assistant.<ul><li>Wiring: radar TX to **IO45** (the panel's RX); radar RX to **IO46** (the panel's TX, only if the panel will configure the radar); GND to U8; **5 V** from the panel's power input, because U8 has only 3V3.</li><li>Link: 256 000 baud, 3.3 V logic, 10 Hz.</li><li>Firmware: an LD2450 frame parser feeding the presence seam (`presence.cpp` `Report[]`). The room radar and the aquarium do not change.</li></ul> Freed by the owner's word that the encoder will not be fitted again (2026-09-23 21:50). | planned: HW deep-dive against the datasheet before any code | [26](26-mtr1-direct-link.md) §5 (the old "no free pin" verdict no longer holds); [11](11-control-and-pins.md) (IO45/IO46 straps, 10 kΩ pull-downs); [16](16-presence-radar.md) (LD2450: 5 V, 120 mA average, UART 256 000, 3.3 V) |
| P5 | **Release 2.5.9.** In it: the upload trial (the panel refuses a Lua file that would not run); the world clock's home city from the knob and the remote. | **released** 2026-09-23 22:38: https://github.com/NickoScope/AnimatedPixelClock/releases/tag/v2.5.9 | HANDOFF 2026-09-23 22:25 |
| P6 | **The agent's gallery and ours are two different things.** OpenClaw keeps its screens in its own `~/screens-gallery` (with SCOREBOARD.md) and believes "Nikolay copies the best to GitHub himself". It does not use `gallery_publish`, so the 21:00 sync finds nothing. Choose one: tell the agent to publish through `gallery_publish` (sent via AgentMQ 22:31), or teach `sync` to read `~/screens-gallery` | open, the owner to choose | HANDOFF 2026-09-23 |

## Decided, not to reopen without a reason

- **2026-09-23, the owner: native screens stay native.** The idea of moving
  the author's clock styles and the data boards to Lua was weighed and
  dropped.
  - They work, and there is room: the image is 2.2 MB of a 4.5 MB OTA slot.
  - Rewriting working code risks speed (px calls, docs/AGENTS.md costs),
    knob and remote controls, and looks, for little gain.
  - **New screens are Lua**, through the gallery and the upload trial.
  - An existing native screen moves only if there is a concrete reason to
    change that screen.

- **2026-09-24, the owner: releases only after architectural changes.**
  Gallery screens, docs and tools are committed and pushed, and that is all.
  A tag, a GitHub Release and the flasher come only for a change in how the
  firmware works, on his go.

## Debts: open, known, not forgotten

| # | Debt | Where it is written |
|---|---|---|
| D-A | The audio visualizer on the onboard mics hangs the panel. The mics stay off until the cause is found; the debts D1–D11 are listed there, starting with D1 | [22](22-audio-visualizer-onboard-mic.md) §12.3 |
| D-B | Lua sound (D11 there): first question, is there a speaker at all | [34](34-lua-sound.md) |
| D-C | Radio memory: the single-frame experiment is parked, double buffering stays | HANDOFF 2026-09-23 09:45; [03](03-firmware.md) |
| D-D | Yacht radar: 17.5 KB outside the lock; MQTT's blocking connect; OTA not taking the lock | HANDOFF "Open debts, unchanged" |
| D-E | Portal 503s under load, and the portal served from `loop()` freezing the display 0.2–0.3 s | [22](22-audio-visualizer-onboard-mic.md) D8 |
| D-F | Effects backlog: the index-addressed switch race is closed with `name`; left open are `keep[512]` on the stack and `rbStn` with the same `putString("")` return check | [35](35-effects-carousel-and-gallery.md) "Backlog" |
| D-G | The IR receiver on GPIO0 has two open items. (1) "A remote pressed during a reset lands in download mode" was not provoked yet. (2) The owner's wiring photos are still to come | [24](24-ir-remote.md) |
| D-H | The rail favourites were found empty on 2026-09-23. They are restored, but the cause is unknown (an NVS wipe? a full flash?). The list lives in docs/29 | [29](29-panel-control-map.md) |
| D-I | Font tables are duplicated across translation units; the Picopixel licence note; a no-PSRAM macro host test; the ambient file reopen; the S3-Zero boot of `psramInit` | HANDOFF 2026-09-23 (the system font) |
| D-J | **Closed 2026-09-23 in 2.6.0:** no effects compiled in, 36 upload slots, the seven former built-ins in the gallery and on the owner's panel. The drift check keeps the copies in tools/luasim/scripts and gallery/ in step | docs/drafts/release-v2.6.0.md |
| D-K | The agent's routine does not publish to its gallery. It is safe to add now (staging plus sync) | HANDOFF 2026-09-23 19:25 |
