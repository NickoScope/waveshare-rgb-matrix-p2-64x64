# Handoff

Rolling record of where the work stands. Newest first.

## 2026-09-16, evening: the infrared remote, and what the audit found in it

**Done.**
- **`src/ir/` is in the firmware, flashed, and driven from the panel's serial
  console.** Ported from NickoScope32's ADD-79 and reshaped to our conventions.
  It produces what the knob produces - detents and a button level - and hands
  them to the encoder's own state machine, so the gestures keep one
  implementation. The seam is inside the encoder's 1 kHz task, not `loop()`, so
  the event queue keeps its single producer. Learned codes in their own NVS
  namespace, a portal card, `/api/ir/*`, and a serial console.
- **Tested on hardware the only way that proves anything:** the encoder's own
  counters moved - cw 0→4, ccw 0→2, click 0→1, long 0→1 - and the display
  walked its pages while they did.
- **164 host checks, 53 of 53 flag-matrix rows**, both on the final code.
- **The audit found two blockers I had written myself**, and both would have
  fired on a panel with no remote in the room: past 24.85 days of uptime the
  knob's own button would have read as permanently pressed, and one
  unauthenticated GET could pin it down for weeks. Both came from a rule I had
  stated in the header as a law - always compare `millis()` with a signed
  difference - and the tests were written under the same law, so they agreed
  with the bugs. Fixed by removing the class: the button is a start plus a span,
  the span is zeroed when it runs out, ages are unsigned. Four host cases now
  run at 25.5 days.
- **The same commit had silently deleted 85 of the 198 lines of
  `platformio.ini`** - the comments recording why the flash mode is `opi_opi`
  and why `SPIRAM_DMA_BUFFER` is refused. Restored and verified line by line.
- **Told the upstream author**, on the owner's "публикуй": issue #3 comment
  5703737437. He has no physical control in his firmware at all, so the letter
  leads with that, gives the measured cost (10,832 B flash, 280 B static RAM)
  and the pull-up any of his users will need. Two of our comments now stand
  unanswered; the watch list says to check which one a reply answers.
- **Read the datasheet of the part on our own board** (doc 24 has it): rev B1
  fits a TSOP2138 on 3V3 with the datasheet's own application circuit, landing
  on **IO4** while the NickoScope32 firmware's `PIN_IR` is 14.
- **The audio module is approved in scope AND written** (doc 25). The scope, put
  to the owner in plain terms and accepted: a Music Assistant player over
  Snapcast with PCM, announcements in stop-and-resume form, the visualizer fed
  from what the panel itself plays, a talking speaker at about 0.68 W; ducking,
  microphones and wake word out, with the numbers for each.
  **The code exists too**, on `feature/ma-player` (`57e23fb`): `snap_proto.h`
  with every layout taken from Snapcast's own `doc/binary_protocol.md`,
  `maplayer_model.h` with the rules and the heap gate, `maplayer.cpp` with the
  socket, the state machine, NVS and `/api/info`, a README, **136 host checks
  passing**, and three rows in the flag matrix (the client builds; the audio
  half and the audio flag alone are both refused). Building it caught a real
  defect the host test had missed: the test ran under C++17, where a class with
  member initialisers is still an aggregate, while the firmware compiles as
  gnu++11 where it is not - so the test now builds under both standards.
  **What is deliberately not there: the sound.** `MAPLAYER_AUDIO_ENABLED`
  refuses to compile until debt D1 is paid, because a stream would be a third
  consumer of the internal heap that already hangs the panel. Nothing has run on
  hardware, and no audit has looked at it.

**Open, in the order they should be taken.**

0. **First thing to check tomorrow, five minutes:** the panel reports
   `ir.enabled: false` in `/api/info` after the flash, and the default is on
   (`settings.irEnabled = true`, NVS key `irEn`). Nothing is broken today
   because no receiver is built, but with one fitted it would simply not start.
   Find out whether a portal save wrote it off (the card's checkbox posts
   nothing when unticked, and the page may not have ticked it from the form
   values), or whether the setting never loaded. Watch `minFreeHeap` while
   you are there: it sat at 7,480 B after this evening's test, against 15,060 B
   earlier - the portal polling and the Lua scenes during the run are the
   likely reason, and that is debt D1's territory.
1. **Debt D1** of [22](docs/22-audio-visualizer-onboard-mic.md) §12.3 - the
   portal's ~20 KB internal-heap spike. It blocks both the visualizer and any
   audio, because a stream would be a third consumer of that memory.
2. **The receiver has never run.** The header is genuinely free, and the whole header was
   **metered by the owner on 2026-09-17: pull-up pads open, 10 kΩ from each pin to
   GND**: the pull-up positions at IO45/IO46 are empty and nothing on
   the board claims those GPIOs. The fitted 10 kΩ pull-downs and the strapping roles
   decide only how a device is wired ([11](docs/11-control-and-pins.md),
   [24](docs/24-ir-remote.md)). Solder a 38 kHz part, measure the 2.2 kΩ
   pull-up rather than trusting the arithmetic, and learn codes from the owner's
   remote. Remember IO45 is a strapping pin.
3. **Two decisions for the owner:** whether the next board revision swaps
   TSOP2138 for a long-burst part (TSOP2238) now that the datasheet says NEC is
   a long-burst format, and whether `PIN_IR` moves from 14 to 4.
4. **The second person on the radar** - parked as a debt until after the next
   tests.
5. **The audio module wants an audit** before anything of it is merged: it is
   written and host-tested on `feature/ma-player`, but no auditor has read it
   and no part of it has run on the panel. Its own first step is the same D1.

## Open, across everything

- **Debt in the fork: the crash report reads a core dump it has not checked (found 2026-09-17, porting upstream PR 4).** `src/health/boot_health.cpp` from `8ec3045` calls `esp_core_dump_get_summary()` straight away, and in ESP-IDF v4.4.7 that function parses the ELF without a checksum (`core_dump_elf.c` 709-776), so a half-written dump is parsed as if it were whole. Two smaller ones in the same file: `causeName()` stops at `StoreProhibited`, so an interrupt watchdog, stored as 64 + `PANIC_RSN_INTWDT_CPU*`, reads "other"; and `getBytesLength("crash")` without `isKey()` logs an error on a board that never crashed. Fix all three the way `feat/crash-report` (`7022c15`) does: `esp_core_dump_image_check()` first, the pseudo-cause names, `isKey()`.
- **Debt in the fork: the weather scheduler compares a signed difference against a deadline (found 2026-09-17).** `weatherLoop()` from `6e91d54` returns while `(long)(now - nextFetchMs) < 0`. With weather disabled or off screen for more than 24.85 days, a stale `nextFetchMs` reads as a future deadline and holds the next fetch back until another 24.85 days pass or a settings change kicks it - the same class of bug the IR audit found on 2026-09-16. Fix it the way upstream PR 3 does: a wait window of elapsed time (`waitFromMs`, `waitMs`), compared unsigned. The model in `docs/drafts/upstream-pr-03-weather-sched-model.py` can be pointed at the fork's version.
- **The audio module's scope is approved (2026-09-16 21:42).** The owner accepted what the board can actually do: a Music Assistant player over Snapcast with PCM, announcements in stop-and-resume form, the visualizer fed from what the panel itself plays, and a talking speaker at about 0.68 W. Ducking, microphones, echo cancellation and wake word are out - the numbers are in [25](docs/25-ma-media-player.md). **Order of work: debt D1 of [22](docs/22-audio-visualizer-onboard-mic.md) §12.3 first** - the portal's ~20 KB internal-heap spike - because a stream would be a third consumer of the memory that already hangs the panel.
- **The Music Assistant player: researched, and the part the owner asked for does not fit (2026-09-16).** The owner asked for the board's whole audio module — streaming from MA, **announcements with the music ducked**, both microphones with echo cancellation, and the visualizer folded in. Answer, with the numbers, in [25](docs/25-ma-media-player.md): playback fits, the rest does not. **Ducking is not available on any route we can implement** — MA does true ducking only for AirPlay, where the *server* mixes the clip into the music; Snapcast switches streams, slimproto stops and resumes, and MA's own request for ducking on queue-flow players was closed as a duplicate. **Voice does not fit either**: Espressif's figure for two microphones plus a reference is 79.1 KB of internal SRAM against the 32,952 B measured free here — Home Assistant's own voice device pairs its ESP32-S3 with a separate XMOS chip for exactly this reason. **The binding constraint is the board, not the chip:** ES8311 and ES7210 share one BCLK and one WS, and an I2S port carries one sample rate for both directions, so a second I2S controller does not help. Read off the schematic in this repo: the echo reference path does exist (ES8311 OUTP/OUTN through 0 Ω links into the ADC's third channel), the amplifier is an NS4150B on **3V3** — so ~0.68 W into the 8 Ω driver, and the brief's "5 W" is the speaker's rating, not the board's — PA_CTRL is held low by 10 kΩ, and MIC4 is not routed. What was built: `src/maplayer/` behind `-DMAPLAYER_ENABLED` on branch `feature/ma-player` (`57e23fb`, pushed) — the Snapcast client's clean core, **host-tested at both c++11 and c++17, 136 checks**, with no audio at all: `MAPLAYER_AUDIO_ENABLED` refuses to build. **Next step is not this module**: debt D1 of [22](docs/22-audio-visualizer-onboard-mic.md) §12.3, the portal's ~20 KB internal-heap spike, has to land first, because a stream is a third consumer of the same memory that already hangs the panel. Two unrelated defects were found in passing and parked as tasks: `ir.h` is included in `web.cpp` under the presence radar's flag rather than its own, and `IRremoteESP8266` is pinned twice in `platformio.ini`.
- **Debt: was anyone actually there? (2026-09-16 20:51, owner's call to park it).** The owner reported the second person had stopped appearing. Investigated: the two display rules added that evening cost 1.5 % of the time the second slot was filled (21 s out of 1374 s, replayed through the real model), and the panel drew two people for five minutes straight on the new firmware at 20:11-20:16. In the window he complained about, the feed carried one target for five minutes (20:19:04-20:24:04). Open question, to answer after the next tests: were two people physically in the room then? If yes, the sensor lost a still person and the fix is on the MTR-1 side ([23](docs/23-mtr1-deep-research.md) §3b); if no, the panel was right.
- **The infrared remote is in the firmware, and no receiver is soldered (2026-09-16).** `src/ir/` behind `-DIR_ENABLED`, ported from NickoScope32 ADD-79 and reshaped to our conventions: the rules are host-tested, the receiver is a second flag, and the seam is the encoder's own sampling task. It produces detents and a button level, so the knob's state machine keeps being the only one. Two things wait for hardware: the receiver has never run, and the 2.2 kOhm pull-up it needs on IO45 is arithmetic, not a measurement ([24](docs/24-ir-remote.md)).
- **The onboard-mic audio visualizer hangs the whole panel (2026-09-15 evening).** Capture's 10.4 KB plus a ~20 KB portal spike exhaust internal heap, Wi-Fi fails its buffers, MQTT retries freeze `loop()`. The owner keeps it off until the cause is found; the debts, in order, are in [22](docs/22-audio-visualizer-onboard-mic.md) §12.3.
- **The hardware arrived on 2026-09-14.** Phases 1 and 2 passed (phase 1 after
  an octal-flash fix); phase 3 too — 128×64 as one canvas. Phase 4, our own
  firmware, passed as well. Phase 5 (encoder) or 6 (network) next. The open questions and the
  gated sequence are in [12-bringup.md](docs/12-bringup.md).
- **Phase 6b is measured, and the HUB75 buffers stay in internal SRAM.** Lua in
  PSRAM beside them costs the render under a millisecond. Moving the buffers
  to PSRAM freed 130 KB of internal heap, but it striped the picture and broke
  TLS certificate checks, so it was reverted
  ([03](docs/03-firmware.md#tried-on-this-board-2026-09-14-rejected)).
- **Internal heap is the scarce resource on this board.** ~41 KB free after
  boot, up from ~37 KB when the Lua stack went from 16 to 12 KB (`123ce83`).
  A TLS fetch needs its 12 KB stack plus ~4 KB. Still possible: run the SD
  reader task only while a clip plays (6 KB).
- The two watchdog fixes have never run on hardware. Phase 6 exercises them.
- The carousel has run on the panel; the owner later switched it off in the
  web UI. Cards and icons are still proven only on the wire and on the host.
  Phase 6c.
- The world clock runs on the panel with NTP time, the home city and city
  search. The owner: "мировое время работает великолепно" (2026-09-14).
- **Presence: the Apollo MTR-1 is installed (2026-09-16)** in the living room and in Home Assistant, with a dashboard "Радар MTR-1" (`/presence-radar`) and a live radar card. Radar Bluetooth is still on and zones are off. Nothing is built on the panel side yet; the two stages are in [16](docs/16-presence-radar.md).
- **Idea, owner's request 2026-09-14: any Home Assistant dashboard on the
  panel.** Pick a dashboard (or a view of one) in HA and show it on the device
  in a special 128×64 format, two 64×64 panels. Nothing designed yet. The open
  questions: what "a dashboard" means at 128×64 (a rendered card image, or a
  small layout language fed with entity states), where it is rendered (HA side
  into a bitmap pushed over MQTT, like icons, or on the panel from states), and
  how the choice is made (a select entity in HA, the knob, the web UI).
- Pages are shown by the knob, the portal, or `POST /api/panel {"show":{"page":i}}`.
- NickoScope-Watch still listens on the legacy `.../state` topic; the keyed
  topic is published in parallel until it migrates.
- `mic_power_rail` GPIO46 — and GPIO46 is now the encoder's B line, so this
  matters more than it did.
- **FYI, unconfirmed:** on R16V parts VDD_SPI is 1.8 V and GPIO47/48 run at
  1.8 V with it. Those two are this board's I2C bus. Read in the WROOM-1
  datasheet; confirm against WROOM-2 before designing anything onto it.

---

## 2026-09-16, evening — the presence radar runs end to end

**On the panel:** `feature/market-climate-audio` `377508d`, flashed over USB at the owner's request. It adds the presence radar and the D3 fix to yesterday's build.

- **The radar works end to end.** The Apollo MTR-1 in the living room → an AppDaemon publisher on Home Assistant → MQTT → `src/presence/` → the `room_radar` Lua scene. `/api/info` reads `source live, targets 1, messages 3, summaries 3, parseFailures 0, people 1, lux 27, online true`.
- **The owner confirmed +X** by walking in: the dot appeared on the side he entered from, so `mirrorX` stays off and matches the Home Assistant card.
- **D3 is proven on hardware:** `[loop] mqtt took 308 ms`, against 3,001 ms before. Free internal heap 36.1 KB, minimum 31.5 KB, no failed allocations.
- **Yesterday's radar rewrite holds:** the scene opens in 0.79 s, was about 2 s.

**What today cost, and what it taught.**
- **The audit of the merged tree found three MAJOR defects** (`b8a6c61`): a ninth MQTT subscription refused in silence, a false "no second task to lock against" in a header while the Lua task reads the model 19 times a frame from core 0, and a parse that accepted any int32 from the broker. All three were real.
- **The hardware found a fourth that no host test had** (`377508d`): the retained summary was counted as a parse failure, because the parser required a targets array. It hid behind the targets payload, which carries the same counters. The host tests grew from 85 checks to 101.
- **A permissions wrong turn.** A write test as the plain SSH user failed and this session concluded `/addon_configs` was read-only. It is not: yesterday's install had used `sudo`. The owner caught it ("вчера мог а сегодня не можешь?"). **Write to Home Assistant over SSH with `sudo`.**

**Also done today.**
- **The SSH add-on's `init_commands` blob is gone**, on the owner's word. It was a leftover from debugging the `nickobot` app on 11-12 September that POSTed file contents into `sensor.nsc_diag` at every add-on start, and had been running dry since. Previous options saved at `~/panel-backups/2026-09-16-ha/`.
- **The music player was diagnosed and the panel cleared.** `S3 Audio NickoScope32v1b` is an ESPHome node played through Music Assistant. Music Assistant's log shows `Slow send_bytes` to that player's MAC in bursts (15 Sep 16:44-19:14, 16 Sep 09:08-09:09 and 17:51), up to 9.6 s, with the player's RSSI at −67 to −83 dBm; the panel was playing cleanly through the worst of the panel's own MQTT storms. Radio has now played 35 minutes with no stall at all, while the last stall was on Spotify. Two suspects remain, the network path to the player and the Spotify provider, and the radio run is the evidence separating them.
- **One real coordinate reached the public KB history** in a test written by the neighbouring session; the owner decided to leave it. Tests use invented numbers from here on.

**Open, in order:**
- the audio visualizer debts D1, D2, D4-D10 from [22](docs/22-audio-visualizer-onboard-mic.md) §12.3, untouched today;
- the delta audit's minors in [16](docs/16-presence-radar.md);
- the player: finish the radio run, then decide between the network path and the Spotify provider.

---

## 2026-09-15, late evening — the audio visualizer breaks the panel

- **On the panel:** `feature/market-climate-audio` `f896605`, flashed over USB. It carries the market, the 32 MB layout, the SHTC3, the onboard mics, styles 7–14, Code EQ as style 2, the heap diagnostics (`[mem]` lines, `allocFails`), a 4 KB capture stack, the settings-save fix and the fast `room_radar`.
- **The owner's summary, 23:20:** until the audio visualizer is started everything works and every screen is fine; after it starts, something breaks.
- **What the serial log shows.** The log is in `~/panel-backups/2026-09-15-monitor/` (private).
  1. **Memory.** Capture holds 10.4 KB of internal heap while it runs, and a portal page load spikes another ~20 KB. Together they took free internal heap down to 896 B (23:04:54) and 504 B (23:08:58).
     - Wi-Fi then failed its RX buffer allocations (`1626 B, caps 0x80c, task wifi`) and the network stack died.
     - MQTT retried every 5 s, and each attempt held `loop()` for 3 s: that is the frozen display. DNS, TLS and ping failed too.
     - The firmware's link recovery restarted Wi-Fi about 3 min later (23:12:10).
  2. **`room_radar` stopped** ("over the time budget (500 ms)", three frames in a row) in today's builds. A/B on the panel:

     | Build | Draw avg / max | Drops after open |
     |---|---|---|
     | 18:05 build | 384 / 408 ms | 0 |
     | Today's tree without `AUDIO_MIC`/`VIZ_WOW` | 381 / 407 ms | 2 |
     | Full build | — | 3, the effect stops |

     The rewrite `3b57c93` has 4.7x fewer instructions per frame and is byte-identical at 6,822 timestamps. It is merged and flashed, but no 30 s frame report on the panel yet.
  3. **Portal saves froze the display for 1.1 s.** This was upstream code erasing 40 absent NVS keys. Fixed in `f79fe99`: 51 ms.
  4. **DSP cost:** 12–15 ms per 20 ms frame on core 0, which it shares with Lua and Wi-Fi.
- **Mitigation without a flash:** portal, Audio visualizer, Source, "PC companion only". `micFeedsViz()` returns false for `AUDIO_SRC_PC`, so capture never starts; the visualizer still runs from the PC stream.
- **Proposed, not started** (the owner has not said go yet):
  - (a) name the portal request that takes ~20 KB (URI in the `[mem]` line) and move its small allocations to PSRAM;
  - (b) no capture start without internal headroom;
  - (c) MQTT: a 1 s connect timeout (`WiFiClient::setTimeout`) and retries backing off from 5 to 60 s;
  - (d) DSP cost.
- **Also today:**
  - a comment on Keralots #3 (22:22), watch item 7;
  - PR #4 merged at 20:35;
  - Code EQ picked by the owner (variant 3).
- **Local only:**
  - `.pio/bisect.ini` (envs `bisect-noaudio`, `bisect-nowow`) in the integration worktree;
  - worktree `/Users/apple/AnimatedPixelClock-radar`;
  - backups in `~/panel-backups/2026-09-15-before-climate-audio/` (the 18:05 app0 image, otadata, boot logs).
- **Monitor:** a serial-only logger from the session scratchpad is running and holds `/dev/cu.usbmodem2101`.
- **The owner's decision, 23:22:** "аудио визуалайзер вешает всю систему, с ним нужно работать … я пока не буду запускать аудио. завтра начнешь искать причину." The audio visualizer stays off. Every result of today's checks and the ordered debts are in [22](docs/22-audio-visualizer-onboard-mic.md) §12.2-12.3.
- **Next step, 2026-09-16:** start on D1: put the URI into the `[mem]` line, then measure each portal request with the mics idle and running.

---

## 2026-09-15, evening — the sensor and the microphones are on the panel

- **On the panel:** `feature/market-climate-audio` `c71bdb5` (market, 32 MB layout, SHTC3, onboard mics, styles 7–14). Flashed over USB at 21:34 at the owner's request, after byte-comparing the partition table with the build. The previous app0 and otadata are backed up in `~/panel-backups/2026-09-15-before-climate-audio/` (private).
- **Before flashing:**
  - build: RAM 102,016 B, flash 2,239,977 B; flag matrix 46/46;
  - climate 147/0; weather screen 11 frames identical; market, portal and media checks passed;
  - audio DSP: C++ matches Python; styles 7–14 pixel-identical in double.
  - The final audit found one MAJOR: the mics held about 11 KB of internal RAM forever. Fixed in `e7ad859`: capture now runs only while the visualizer shows the mics, stops 25 s after, and GPIO11 is driven low. The delta audit approved it, and the committed code matched the audited diff by patch-id.
- **On hardware:**
  - clean boot; the market record was read from LittleFS;
  - climate "ok", id 0x0887, 31 °C (docs/21 §12.7);
  - the mics start and stop, cost 10.4 KB while running and lose nothing per cycle; DSP takes 12–15 ms per 20 ms frame (docs/22 §12.1).
- **For the owner to test:**
  - a reference thermometer for 30–60 min (docs/21 §12.6);
  - design B live and stale via `/api/climate/pause`;
  - styles 7–14 with music, a clap for latency, LED supply noise, gain (docs/22 §12);
  - the market pages.
- **Open:**
  - minFreeHeap 11.3 KB after the visualizer ran; watch it next to the TLS pages;
  - DSP cost; `audioInternalBytes` under-reports;
  - the backlogs in `src/audio/README.md` and `src/climate/README.md`.
  - After the owner's test: merge into `board/waveshare-esp32-s3-rgb-matrix`, then delete the local `wip/market-*` branches, which carry fund history.

---

## 2026-09-15, after midnight — plan for the day

**Where it stands at the end of the session.**
- **On the panel:** the board branch at `8c5f8cf`, flashed over OTA and
  confirmed by the panel itself. It carries the gzip portal, boot health, the
  12 KB Lua stack, the yacht radar's own task, and fetches only while a page
  is on screen. The football clock is showing.
- **Pushed:** the board branch, every helper's `wip/` branch and this
  repository. `wip/web-ui` had never been pushed and went up at the end.
- **Sent to Keralots:** issue #3 and two comments under his r/esp32 post.
  The scheduled task `keralots-watch` checks for answers every two hours,
  08:00–22:00 ([watch list](docs/watch-list.md)).
- **The eight helper worktrees are removed.** All of them were merged and
  pushed; the branches remain, locally and on GitHub.

**Plan, in order.**

1. **Answers.** When Keralots replies on #3, summarise it for the owner and
   redo the PR order in [09](docs/09-upstream-contributions.md). No PR before
   he answers or the owner decides.
2. **PR 1, Waveshare board support.** Only after step 1.
   - Branch from `upstream/main` with only the environment, the pins and
     `opi_opi`.
   - Build every upstream environment, and measure flash on `matrix-s3`.
   - Draft the PR text in the owner's voice in `docs/drafts/`. It goes out on
     his "отправляй".
3. **Not yet checked on the panel.**
   - Media player:
     - TUNE and VOLUME from the knob;
     - `play_fav` through `music_assistant.play_media`, never run yet;
     - volume on the Yandex stations.
   - Portal: save a setting and reload, export and import, the OTA page's
     reload.
   - `/api/info` `lastCrash`, after a day of use.
4. **IR receiver.** RMT receive on GPIO14, once the owner has removed R47
   and fitted it ([11](docs/11-control-and-pins.md)).
5. **Memory.** Run the SD reader task only while a clip plays: 6 KB of
   internal heap.
6. **Flight lists survive a reboot** (the owner said yes, 2026-09-15).
   - Keep the last AeroAPI lists and their fetch time in flash.
   - At boot, show them straight away. The next call waits for the
     15-minute floor, counted in wall-clock time.
   - Today every reboot bought the lists again; 24 calls went that way.
   - Test after the day cap resets at 00:00 UTC: reboot twice and count the
     calls.
7. **The market dashboard** ([18](docs/18-stock-dashboard.md)): design v3
   after two council reviews; the owner moved the maths to Home Assistant.
   Previews approved 10:13. Three helpers since ~10:20:
   - the AppDaemon app, plug-and-play modules, on `wip/market-board` in
     `AnimatedPixelClock-market` (paced: Yahoo returned 429 to the Mac after
     ~40 requests in 90 min);
   - the panel page and the portal's Market page on `wip/market-panel` in
     `AnimatedPixelClock-market-panel`, with a table-driven settings registry;
   - a research report on professional dashboards and a settings inventory,
     to become `docs/19-market-dashboard-research.md` (the owner, 10:15: as
     many settings as sensibly possible; GitHub, Reddit, finance sources).
   **19:35 two features in build, both from feature/market-dashboard 776fc04.**
   - `feat/onboard-climate`: SHTC3 on I2C 47/48. The owner picked design B; it is being drawn now.
   - `feat/audiofx-onboard-mic`: ES7210 with two mics; the capture pipeline is done. The owner picked all 8 new effects and keeps the old 6; they are being built.
   - Plan: one integration branch with both merged, `web_assets.h` regenerated after the merge, the audit gate (BLOCKER/MAJOR only), then one OTA.
   - Hardware tests after that: the SHTC3 ID and a self-heating calibration against a reference thermometer, then mic noise and latency.
   - At the squash, leave out `tools/audiofx/out` (23 MB of GIF/MP4 previews) or move it out of git.
   **18:54: 32MB done.** On the owner's "да", the panel was repartitioned over USB.
   - Result: LittleFS 23.9 MB, 20 MB free; the animations carried over; the market record is written.
   - Watch minFreeHeap (12.5 KB at boot).
   - PR #4 is open upstream.
   - Agents still running: the climate sensor and audio FX.
   **18:10 32MB flash, the owner's request.** Following upstream: large_littlefs_32MB.csv, LittleFS 3.4MB to 23.9MB, NVS unchanged.
   - Done: committed and built on `feature/market-dashboard`; the table was verified.
   - To do: needs USB. Back up, copy the files, flash the app and table, flash the new LittleFS image.
   - The script is being written in `tools/flash/`, tested offline.
   - Waiting for the owner to connect USB and give his go.
   **17:10 session summary (market dashboard).**
   Done:
   - council design and the owner's decisions; previews v1 and v2 approved;
   - panel page and portal; HA app with plug-and-play modules;
   - audits, fixes, and squash into `feature/market-dashboard` (b40c3d6, pushed);
   - OTA to the panel (build 17:00:11); app on HA; "Портфель" view in HA.
   Fixed on the real system:
   - AppDaemon's `config_path` Path in `self.args`;
   - the panel reboot loop on a full LittleFS (free-space guard).
   Left:
   - step 7, the owner's look at the panel pages;
   - the owner's decision on freeing ~125 KB of LittleFS for the offline record;
   - log noise `live: shrunk`;
   - delete the local wip branches and worktrees (they hold the funds in history) after step 7;
   - merge `feature/market-dashboard` into the board branch after step 7.
   Next step: the owner's hardware check, then merge and cleanup.
   **17:05: steps 1–6 done, working end to end.**
   - Guarded firmware flashed.
   - App re-enabled.
   - The panel accepts the data and has not rebooted.
   - Step 7 (the owner's look at the pages) and the HA "Портфель" view are left.
   - Delete the local wip branches and worktrees after step 7.
   **17:00: incident.** From 16:31 to 16:53 the panel rebooted every ~16 s. LittleFS was full (12 KB free); the
   market record write hit littlefs's divide-by-zero in its NOSPC log.
   - The app is stopped: pre-install `apps.yaml` restored; the package, store and `local.json` remain on HA.
   - Retained topics were cleared.
   - A free-space guard is in firmware; it is being built for OTA.
   - Then re-add the apps.yaml entry from `apps.yaml.market-disabled-20260915`, without its `disable` line.
   **13:55: finish line in 7 steps.**
   1. Panel: done.
   2. App: done. First real fetch OK; fees missing (401).
   3. Squashed `feature/market-dashboard` e737aab: pushed.
   4. Final audit: running.
   5. OTA: the panel at 192.168.4.43 has been offline since morning.
   6. HA install: needs the owner's yes and a backup.
   7. Hardware test.

   Delete the local wip branches after step 7.
   **Privacy (11:58).** Both repos are public; the owner's allocation had
   been pushed. His decision:
   - fork branches: scrub. `origin/wip/market-board` and
     `origin/wip/market-panel` were deleted at 11:59; the local copies are
     intact. Push squashed clean branches only after `git grep` finds none
     of his weights.
   - KB: allocation moved to gitignored `private/`; history kept.

   11:30: the panel side is done (`wip/market-panel`, remote deleted since); the audit
   gate is running on it; the research is in doc 19; the owner has six
   page decisions to make (doc 18). The HA app is still building.
   Then: merge, OTA, the HA app install (the add-on's `python_packages`),
   the "Портфель" view in HA, measure. Installed for HA's own dashboards on his word:
   `ha-easy-stock` with the four indices and the dashboard "Биржа".
8. **PC control: the companion app's stats and spectrum stream.** Still in
   the firmware on UDP 4210, but never tried on this panel.
   - First from the Mac: send synthetic packets, `FFT1` plus 32 bands for the
     spectrum and v2.2 JSON for the stats, and check both screens at 128×64.
   - Then with the owner's Windows or Linux PC and the real app. There is
     no macOS build.
8. **Power for the final installation** ([12](docs/12-bringup.md) Phase 0,
   [04](docs/04-best-practices.md)).
   - Which supply the owner has (volts, amps). Needed: 5 V, at least 8 A.
   - Each panel on its own lead from the supply.
   - The controller from the same supply, through the M3 posts or the POWER
     socket.
   - 1000–2000 µF across each panel's input.
   - Check that the USB socket does not back-feed.
   - Measure the current on a white field at brightness 128 and 255, and the
     5 V at the panels' VH4 under load.
9. **Waiting on the owner's decision:**
   - GPL-3.0 for media player phase 2 (local radio);
   - a password on `/update`.

---

## 2026-09-14, late evening — third checkpoint

- **The slowdowns the owner saw came from internal heap running out.** The
  snooker clock stuttered, pages switched late, and the rail board sat in
  LOW MEM.
  - `MEM_TRACE` checkpoints in `setup()` found where the memory goes: the
    HUB75 buffers ~148 KB, the Wi-Fi connect 46.5 KB, the Lua task stack
    16 KB.
  - The fixes, each run on the panel:
    - Fetches take turns, below the effects (`425c571`).
    - The weather task lives only for a fetch (`6e91d54`): ~30 KB free a
      minute after boot became ~38 KB.
    - At boot, internal heap now bottoms out at 30 KB. It was 10.6 KB while
      the boards fetched in the background.
- **Boards and weather fetch only while their page is on screen.** Owner's
  brief. The rail board used to poll every 5 min off screen, and tracked
  flights on their own cadence. Weather was fetched whenever the rotation
  contained its clock, even if it wasn't showing. Checked after boot: 0 rail
  polls, 0 AeroAPI calls, no weather fetch.
  - Then each page was shown in turn through `/api/panel`:
    - Trains fetched at once: 93 services.
    - Flights made 2 calls.
  - Off screen, 1 min 45 s went by with the rail poll due and none sent. A
    poll can still start in the 3 s after the page leaves.
  - **The ~1 s loop stalls, found with a part profiler** (`fc67bda`: `/api/info`
    `loopSlowPart`, serial `[loop] <part> took N ms`):
    - **Not the settings write.** A style change now writes one key in 0–3 ms
      (`f341bae`), and four style changes stayed under 15 ms.
    - **Entering the yacht radar: 636 ms.** The AIS TLS handshake ran in
      `loop()`. It is now on a task that lives with the page (`bfe7375`), and
      three entries measured 16–38 ms.
    - **Loading a portal page** blocks `loop()` for as long as the transfer
      takes, at ~70–100 KB/s:
      - `/` (128 KB): 1765 ms. It is a template with ~70 `%V_*%` tokens, so
        it cannot simply be gzipped.
      - `/panel.js` (100 KB): 987 ms.
      - `/portal.js` (44 KB): 537 ms.
      - The static files are cached for a year, but `?v=` changes with every
        firmware, so the first portal open after a flash reloads them all.
      - The portal's polls are 22–60 ms each.
      - **The owner chose both:** (1) gzip the static files; (2) move the
        settings page to a JSON fetch so `/` can be gzipped too.
- **PSRAM for the HUB75 buffers: tried and rejected.** Stripes on every page,
  and TLS `-9984` on both pinned hosts ([03](docs/03-firmware.md)).
- **Football clock merged** (`3aa6d4e`). 20 fps, 18 ms a frame. One frame
  dropped once, about 70 s after boot; the suspects are in
  [14](docs/14-lua.md).
- **Media player phase 1 merged** (`6ad1133`).
  - On the panel: page 11, subscribed under `nickoscope_matrix/d20ec8/media/`.
  - The AppDaemon app is installed and running, on the broker login
    `flight_board` already uses (`nicko_mqtt_user`/`nicko_mqtt_pass`); nothing
    new was entered. Backup: `apps.yaml.bak-media-20260914`. The panel reports
    the bridge online, 5 players, a now-playing state and 16 radio favourites.
- **AeroAPI ran into its day cap** (24 board calls, $0.12). Every reflash
  refetched everything. Keeping the lists across reboots was offered to the
  owner and has no answer yet.
- **"IP (for Python)" on the boot screen:** upstream's label for the PC
  Companion App, which sends to UDP 4210. Explained to the owner; not
  changed.
- **OTA works, and now rolls back** (`8ec3045`, [03](docs/03-firmware.md)).
  - `/update` took a 2.29 MB image in 23–28 s.
  - An image is confirmed only after a minute up, with Wi-Fi and 200 frames.
    A test image that aborts before that was rolled back on the panel, from
    `app1` to `app0`.
  - `/update` still has no password; the owner chose the other two fixes.
- **Crash reports now show in `/api/info` → `lastCrash`**, read out at boot and
  erased from flash.
  - Left over from earlier in the day: `loopTask`, `StoreProhibited` at
    address 0, `pc 0x40377c0a`, image `52f21f1c046d1d7b`. That is the shape
    of an `abort()` or a failed assert: the rollback test's deliberate abort
    reads the same, `pc` in `panic_abort`. So it was likely an abort in
    `loop()`. The cause is unknown, because no ELF with that SHA survives.
  - ELFs of flashed images are kept in `~/AnimatedPixelClock-elf/` from now
    on.
  - One unexplained reboot at ~23:27 left no report, so it was not a panic:
    power, an external reset, or the owner.
- **The portal is gzipped, and `/` is static** (merged `8c5f8cf`, flashed over OTA,
  confirmed).
  - First open, cache empty: 301 KB before, 80 KB after.
  - `/` loads in 0.14 s instead of 1.8 s.
  - All 105 settings the old template filled match.
  - Numbers are in [03](docs/03-firmware.md).
- **Flag matrix: 35/35 as intended** on `bfe7375`, on `8ec3045` (boot health) and on `8c5f8cf` (gzip portal).
- **Next:**
  - IR receiver, once the owner has fitted it.
  - **Sent 2026-09-15:**
    - the first issue to Keralots,
      [#3](https://github.com/Keralots/AnimatedPixelClock/issues/3);
    - two comments on his r/esp32 post, from the owner's Reddit account:
      a top-level comment, and a reply in the S3 boards thread
      ([drafts](docs/drafts/reddit-comments-01.md)).
    - a Show and tell post about the Waveshare board in the HUB75 library,
      [#962](https://github.com/mrcodetastic/ESP32-HUB75-MatrixPanel-DMA/discussions/962).
  - Watch the issue and the comments for the author's answer before any PR
    work. The PR order is in the issue.

## 2026-09-14, evening — second checkpoint

- **Web UI merge pushed** (`62a0e6a`, flag matrix 22/22).
- **Yacht radar fixed and extended; the owner: "отлично радар яхт работает".**
  - **Why it was always empty:** aisstream.io sends binary websocket frames,
    and the port handled text only. The flagship fixed the same bug in
    v33.0.3. Fix in `ab4314c`.
  - **More boats:** added the Class B messages, with names from
    aisstream/ais-message-models. The flagship subscribes to Class A only.
    The table then filled to its 16-vessel cap in two minutes; with Class A
    alone it had reached 11.
  - **On screen:** a 6 s sweeping beam that flashes the dot and its list row,
    lengths in the list, and the list looping when it overflows (`281d46f`).
  - **Then:** the list is sorted by length by default, and static data is
    kept for vessels not yet plotted, so lengths no longer wait six minutes.
  - **Carousel off:** at the owner's request, from the web. The AIS stream only
    runs while the page is up, and 15 s was never enough for a boat to report.
- **Snooker clock merged** (`66bee4b`). A self-playing frame under WPBSA rules
  with a HUD clock; on the panel 20 fps, draw average 10 ms.
- **Rail board settings in the web** (merged `5515371`, flag matrix 24/24):
  - swap interval, rows, brightness, stale threshold;
  - row, heading and highlight colours;
  - seconds on the clock;
  - a green "due soon" window of 0–15 min, default 3.
  - Kept in NVS `rbcfg`; web settings win over HA's config topic until reset.
  - On the panel: every bad value is refused with a 400 naming the field,
    and green rows are flagged live (2 departures, 3 arrivals).
- **Portal "Effects & clips" page** (`aae1a78`): stored clips with Play and
  Stop. Tried in a browser against the panel.
- **Second Fenderson clip:** "Blocks" 2:15–2:29. The animation store now holds
  planets and blocks, with ~620 KB left, so a third full-length clip needs
  one deleted.
- **Phone clip maker and TF card gallery merged** (`fd3e2f0`, flag matrix
  26/26):
  - "Make a clip" on the Effects & clips page takes any audio or video file,
    renders XY in the browser, and uploads to the card, or to flash when there
    is no card.
  - The gallery on the card has thumbnails, Play and Delete, and a cap of
    12 000 frames (8 min, 49 MB).
  - Playback streams from the card with a 25-frame read-ahead ring in PSRAM.
  - **Checked on the panel, 21:34–21:43:** the card mounts at boot, with
    31 GB free. The whole Planets track (4875 frames, 20.0 MB) took 114 s to
    upload, about 175 KB/s. The card itself writes 1.2 MB/s, so the portal's
    upload handling is the bottleneck: a todo. Playback over 2 min read 2.5 ms
    per frame on average and 6.4 ms at worst, with 0 underruns, the ring full,
    and 3.3 KB of the 6 KB reader stack free.
  - **Gotcha:** a clip shows only on the CLOCK page. The web Play button puts
    that page up first; a bare `POST /api/clips {"play":…}` does not.
- **Media player phase 1 in progress** (helper,
  `/Users/apple/AnimatedPixelClock-media`, `wip/media-remote`): a now-playing
  page and remote for HA/MA players over MQTT, with an AppDaemon app on the HA
  side. The design is in [17](docs/17-media-player.md).
- **IR receiver pin found:** IO14 with R47 removed, or IO10. Details in
  [11](docs/11-control-and-pins.md). Nothing is soldered yet.
  - Scope grew at the owner's request: a clip gallery on the TF card with
    streaming playback, read ahead in PSRAM; a size cap from the format and
    the card. Rendering is XY only; the extra modes were dropped after the
    owner saw a vectorscope clip.
  - Not doing: downloading from YouTube or Spotify (their terms, and DRM).
  - In-page microphone or tab capture needs HTTPS, and the portal is plain
    HTTP; recording to a file is the path.
- **Oscilloscope clips: the XY algorithm is the one** (owner, 21:18). Left
  channel is X and right is Y, from the original album tracks, as for
  Planets, Blocks and now Circles (4:49–4:55, on the panel).
  - A stereo vectorscope clip from a remix was rejected as garbage and deleted.
  - The remixes are mostly ordinary music and draw only a blob.
  - The clip maker is told: XY only.
- **TF card works:** the owner's 32 GB card mounts in 1-bit MMC at 20 MHz and
  reads a 4 KB frame in 2.6 ms on average, 6.4 ms at worst. Numbers are in
  [02](docs/02-controller.md).
- **Flight board going direct, in progress** (helper,
  `/Users/apple/AnimatedPixelClock-flights`, `wip/flight-direct`):
  - AeroAPI straight from the panel, with cost guard rails;
  - up to 6 custom airports added by search;
  - tracked flights pinned as the top row.
- **World clock rework merged** (`2fed039`, flag matrix 24/24). The owner
  stopped the helper at 20:12 and chose to verify what was already committed.
  - The big time is home's time and home's name pulses for 10 s after a change.
  - Cities can be searched in the portal: the browser asks Open-Meteo's
    geocoder, and up to 6 custom cities are kept in NVS (`wcC0`–`wcC5`).
  - An unchosen home follows the weather location, then a once-per-boot IP
    lookup, then the panel's zone. Zones come from an embedded tzdata table.
  - Checked on the panel over the API:
    - Almaty 23:16 (+5), Cannes 20:16 (+2), and TOKYO added as home 03:16 (+9);
    - a bad zone, a 40-character name, latitude 123 and an unknown id are each
      refused with a clear 400;
    - the owner's home was restored and TOKYO removed afterwards.
  - Owner at 20:20: "мировое время работает великолепно".
- **Rail board fetches RTT directly from the panel** (merged `2fd1973`).
  - The owner provisioned the refresh token himself with
    `provision_secrets.py rtt-from-ha`, then the provision and normal flashes.
  - On the panel at 19:59: source `direct`, token `refresh-exchanged`,
    HTTP 200, 0 fails, 43 KB responses every 30 s.
  - **The board was still empty.** RTT's live times carry no zone
    (`2026-09-14T18:31:00`), although the spec describes UTC or an offset, so
    every service was refused. Found with new skip counters and a raw sample
    in `/api/railboard`. Zone-less times are now London time. At 20:07:
    8 departures and 8 arrivals from the direct fetch.
  - **A web-forced mode trapped the knob:** a clip started by
    `/api/anim/play` could not be left. Any page change now releases it.
  - Quota reported by RTT: 9000 a day, 750 an hour, 30 a minute. The panel
    uses about 2880 a day.
  - The HA fetch automation stays off. Its AppDaemon replacement (option A in
    `src/railboard/README.md`) is not installed; if it is, the two together
    use ~7200 of the 9000.
  - RTT's API terms ask that tokens stay server-side. The owner was told and
    chose direct.
- **Oscilloscope music on the panel, a first look.** A 14 s clip of Jerobeam
  Fenderson's "Planets" (1:00–1:14) plays as a custom animation on the CLOCK
  page.
  - Rendered from the owner's own WAV with the beam's dwell as brightness,
    phosphor afterglow and bloom, in 16 greens.
  - The renderer is still in the session scratchpad. Neither the audio nor the
    clip is in any repo.
- **Encoder confirmed by hand:** owner at 18:50, "энкодер — хорошо", on the
  1 kHz sampler with the 2 ms pair filter. Phase 5 rotation is closed; the
  knob's switch is still unsoldered.
- **Knob "phantom" steps were measured, and they were not noise.**
  - A first capture with nobody meant to be at the knob logged 18 clockwise
    steps in 15 s.
  - A 2 ms stability filter on the A/B pair went in (`af42154`). It filters
    the pair, not each pin: a per-pin filter passes a 1 ms-a-state quadrature
    sequence. The host test covers spikes, fake clicks and coupled pulses.
  - CTRL_DEBUG builds now log every raw A/B change with its time.
  - The second capture (10 min) had 6 clockwise steps 25–32 s after boot and
    nothing after. They were clean quadrature: 34–50 ms between the A and B
    edges, rests of 1–1.5 s at both 00 and 11. A rest at 00 needs both contacts
    really closed through the 10k pull-downs, so this was the shaft turning,
    not coupling. The only glitch in 10 min was one 1 ms bounce, filtered.
  - **Answered by the owner at 18:48:** he was turning the knob and switching
    modes from the web himself. There were no phantoms. The raw log is a
    clean picture of a real hand on this knob: 34–50 ms between the A and B
    edges at a relaxed pace. The advice to tie the module's "+" to GND stays:
    it removes the ~1.1 V divider on an open line while the other contact is
    closed, a margin problem in its own right.
- **Flight board: arrivals and departures take turns every 10 s** (`133ff50`).
  - Both halves come in on one wildcard subscription.
  - A half fetched more than 30 min ago is asked for again, once. Retained
    departures stamped 09:34 were being shown at 18:30.
  - The web page has "Both, every 10 s", plus arrivals only and departures
    only.
  - Inside the page, the knob now steps airports only.
  - Verified on the panel: 10 s swaps, 400 on a bad value, stale departures
    refetched.
- **Lua looks merged** (`f332d7b`): black ground, big digits, a livelier
  Minecraft. On the panel Minecraft draws in 18 ms, down from 33.6. Numbers
  are in [14](docs/14-lua.md).
- **Rail board merged** (`ba390dd`), laid out from the owner's photo of a UK
  station screen.
  - One list at a time, 10 s each; any station by CRS code from the web.
  - `tools/railboard/ha_package_railboard.yaml` replaces the Guildford one.
  - On the panel it subscribes and publishes the GLD selection. There is no
    data yet: the package and the RTT token are not in HA. The owner has the
    commands.
- **Flag matrix:** the 22/22 recorded for `133ff50` is **unverified**. Two
  trees ran the matrix at once and shared `/tmp/pio_flag_matrix.ini`. The
  script now keeps its scratch file under each tree's `.pio`. The rerun on
  `ba390dd` passed 22/22, and everything up to `ba390dd` is pushed.
- **Code-audit gate on the whole day (`20eb9c1..ba390dd`): CHANGES-REQUIRED**
  — no blocker, 2 major, 7 minor, 5 nit.
  - No secrets were found (gitleaks) and the build is clean.
  - Both majors are fixed: paid AeroAPI requests are capped in the firmware,
    and portal POSTs must be JSON.
  - The cheap minors are fixed too.
  - **Left open, for the owner:**
    - An EC11 held once for 250 ms at 00 switches the knob to half-detent
      until reboot.
    - The Lua task's 16 KB stack against `LUAI_MAXCCALLS 200` is unmeasured:
      run a nested-pcall script on the panel.
    - One shared retained `railboard/select` topic serves every device.
    - A flight board payload has no date, so a day-old board fetched in the
      same half hour looks fresh. The fix is an epoch `ts` from HA.
  - The auditor's own note: this was a code review, not a hardware QA pass.
- **Aqara FP2 found in Home Assistant.** It was already paired over HomeKit
  since June; the Pi's USB only powers it.
  - Over HomeKit, HA gets one presence for the whole room plus light level.
  - The FP2 does count people, as the owner pointed out, but that goes out
    only through Aqara's cloud API. The route needs a bridge on :8080 and
    his decision.
  - No coordinates leave the stock firmware.
  - New automation `automation.matrix_fp2_presence_to_mqtt` publishes it
    retained to `nickoscope_matrix/presence/fp2`, checked on the broker.
  - Nothing on the panel consumes it yet.
  - Details and sources are in [16](docs/16-presence-radar.md).
- **Raspberry Pi (nickol), read-only look:** healthy — 52.7 °C, not
  throttled, NVMe 7 % used.
  - Swap is 1.4 of 2 GiB, mostly openclaw.
  - 17 stale ssh sessions are open.
  - eth0 has no cable, so it runs on Wi-Fi.
  - The `nickol` alias did not resolve from the Mac.

---

## 2026-09-14, evening — owner away, working alone (checkpoint)

The owner left the bench with instructions to keep debugging, bring in the
Guildford board and the Lua effects, extend the web UI, and finish with the
code-audit gate. Written mid-way so nothing is lost if he is back first.

Done and pushed to the fork unless marked:
- **Encoder, second fix.** The flagship decoder "did not always fire". It is
  now sampled by a 1 kHz esp_timer instead of once per loop(), learns
  half-detent knobs (a 00 rest), and its lock-out is 10 ms, not 80.
  `tools/control/encoder_host_test.cpp` runs the real control.cpp against
  simulated knobs: 11/11. **Not yet turned by hand on the panel** — nobody was
  there to turn it.
- **Flight board** top-right now shows the time; it showed HA's last-fetch time,
  which looked like a stopped clock.
- **Guildford rail board merged** (`bb55814`, local until the flag matrix passes):
  a page named TRAINS; a click enters it and rotation toggles board and
  diagnostics. Needs the owner's RTT token in Home Assistant — steps below.
- Running in the background: the flag matrix on the merge, a 10-minute soak on
  the board, and two helpers in their own worktrees — the web UI
  (`/Users/apple/AnimatedPixelClock-web`, `wip/web-ui`) and Lua effects on the
  panel (`/Users/apple/AnimatedPixelClock-lua`, `wip/lua-effects`). Nothing of
  theirs is merged yet.

**Rail board, what only the owner can do** (from `tools/railboard/ha_package_guildford.yaml`):
1. `<config>/secrets.yaml`: `rtt_bearer: "Bearer <long-life access token>"`.
2. `configuration.yaml`, once: `homeassistant: packages: !include_dir_named packages`.
3. Copy the package to `<config>/packages/railboard_guildford.yaml` and restart HA.
4. Never set `homeassistant.components.rest_command` to debug logging: at debug
   it logs request headers, which carry the token.
Not run anywhere yet: the package has never been loaded into Home Assistant.

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
- Rails by the owner's meter: about 5 V on the posts, about 3.3 V on the header.
- **Panel column drivers are `FM6124HJ`.** Library 3.0.14 initialises FM6124 and
  FM6126A through the same function, so question 1 is settled from the chip
  marking; test A confirms it on screen.

- **Phase 2 passed:** colour order, rightmost column with `clkphase = false`, all
  64 rows. GENERIC draws the same picture; the firmware keeps FM6126A.

- **Phase 3 passed:** one continuous 128×64 canvas, chain order right, white
  steady, no visible gap at the seam (by eye, panels loose).

- **Phase 4 passed:** the real firmware, ten minutes without a reboot, Lua
  self-test passing, both panels in use. The carousel walked all four pages on
  its own: clock, world clock, flight board (no data yet), yacht radar (no key).

- **For now, without a knob:** every page and all 14 clock styles, 15 s each
  (`CAROUSEL_ALL_STYLES`, flag matrix 18/18). Lua effects are still not on the
  panel — the runtime is not connected to the display; phase 6b first.

- **Phase 5, rotation passed.** The common goes to 3V3 on this board (10 k
  pull-downs R59/R60); the first knob had a dead DT contact; the decoder is the
  flagship's. The knob's own switch is still to be soldered (BOOT works meanwhile).
- **Phase 6 in part:** broker credentials and the AIS key provisioned from the
  owner's own run of `tools/provision_secrets.py`; the board connects to
  Mosquitto and the flight board shows data.

**Next:** the flight board airport choice in the web UI; merge the Guildford rail
board branch; solder the knob's switch.

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

