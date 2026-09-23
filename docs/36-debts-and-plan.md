# 36. Debts and plan

One list of what is owed and what comes next. Each item links to the document
that holds its detail; this file does not repeat that detail. Newest decisions
first. Started 2026-09-23 at the owner's request: "запиши в долги и план работы".

## Plan: next up, in the owner's order

| # | What | Status | Detail |
|---|---|---|---|
| P1 | **System corners on every screen.** Left: A/M, the carousel on (auto) or the pages changed by hand (manual). Right: a Wi-Fi icon coloured by signal level. While the remote is received, the right corner blinks a red dot instead of the icon. | in work 2026-09-23 | owner, 2026-09-23 21:19 |
| P2 | **The panel in Home Assistant over MQTT discovery.** One device with its availability (LWT) and these entities: <ul><li>`light`: display on/off and brightness</li><li>`select`: page and clock style</li><li>`switch`: carousel</li><li>`number`: slot time</li><li>`button`: next and previous</li><li>`text`: notification</li><li>sensors: now showing, mode</li><li>diagnostics: version, uptime, RSSI, heap, DMA free, link recoveries, alloc fails, reset reason</li><li>`update`: `latest_version` published by the panel</li></ul> The firmware already knows every one of these values (`/api/status`, `/api/panel`, `/api/info`). The HA dashboard `/led-panel/panel` has sections waiting for them. | **later**, the owner's word 2026-09-23 21:19 ("так сделаем, но позже") | HANDOFF 2026-09-23 21:15; the dashboard agent's report |
| P3 | **Release 2.5.8.** Contents so far: the remote's arrows and brightness step once per press; the remote's brightness is kept across a reboot; brightness readings in `/api/info`. P1 goes in too. | not released | [24](24-ir-remote.md) "Soldered and tried" |

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
| D-J | The built-in effects sit in both the firmware and the gallery. The drift check guards them. When they leave the firmware: 12 upload slots, 16 needed | HANDOFF 2026-09-23 19:55 |
| D-K | The agent's routine does not publish to its gallery. It is safe to add now (staging plus sync) | HANDOFF 2026-09-23 19:25 |
