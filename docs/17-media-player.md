# Media player and internet radio on the panel — design

**2026-09-14 · research and design only, nothing built.** Written by the
design helper from the flagship's files and this board's documentation; saved
here as it came, with the owner's correction already applied (the model is
the flagship's separate **S3 Audio** controller, not the main S3).

Owner's request: «изучи возможность сделать экран медиа плеер работающий с ХА
и интернет радио, у нас прекрасный пример реализации в NickoScope32 v1b, возьми
baseline прошивку esp32 s3 audio и посмотри как портировать и посадить тот
аудиомодуль еще нам здесь.»

Path aliases: `APC` = `/Users/apple/AnimatedPixelClock`; `KB` = this repo;
`NM` = `/Users/apple/Retro Nickol Moscow Dropbox/Nikolay Mir`; `AUD` =
`NM/Electronic-Engeneering-Schema-PPCB/work/repos/NikoScope32/baseline firmware/NickoScope32-v1B-Audio-S3-v1.0.5`;
`BRU` = `NM/Electronic-Engeneering-Schema-PPCB/work/repos/NikoScope32/NickoScope32 BringUpToLife v1.b/fw-audio-s3`;
`LIB` = `BRU/.pio/libdeps/audio-esp32s3/ESP32-audioI2S/src`.

## 0. Summary

1. **The flagship audio module** (U601) is an ESP32-S3 running **ESPHome
   2026.6.5 on ESP-IDF 5.5.4**: a Sendspin player for Music Assistant and an
   ESPHome `media_player` in Home Assistant with announcement ducking, feeding a
   PCM5101A, mirroring I2S to the H743 and controlled by MAIN over binary NSP on
   UART at 921600. Its internet-radio module (`ns32_radio`) is **specified, not
   built** as of 1.0.5.
2. **The ESPHome stack does not port 1:1** into this firmware (arduino-esp32
   2.0.17 = IDF 4.4.7; Sendspin and the ESPHome audio components need IDF 5.x,
   `AUD/ARCH-OPTIONS_2026-09-06.md:26-28, 79-80`). What ports: the design
   (roles, command/state contract, nothing heavy in the audio path, "last
   started wins") and the Arduino bring-up 1.2.3 pattern (ESP32-audioI2S
   3.0.12, a station core with a silence detector), proven on U601.
3. **Hardware fit is good on paper.** The onboard ES8311 codec and NS4150B amp
   use I2S on GPIO 43/38/21/12, amp enable GPIO11, I2C 47/48 — no overlap with
   HUB75, TF card, encoder or USB. The HUB75 library on the S3 drives
   **LCD_CAM, not I2S** (`gdma_lcd_parallel16.cpp:61-63, 81-83`), so I2S0 is
   free. Waveshare's `09_Music_Player` runs HUB75 + ESP32-audioI2S + ES8311 on
   this board (on arduino-esp32 3.3.7, not ours).
4. **Recommendation, in layers:** Phase 1 — the panel as **display and remote**
   for existing HA/MA players over the MQTT bus (no audio hardware, no GPL
   code). Phase 2 — **local internet radio** on the onboard speaker, exposed to
   HA as MQTT-discovery entities; needs the owner's GPL-3.0 decision (§1.4) and
   three bench numbers (§7). Optional Phase 4 — a native MA player by seating
   the **U601 ESPHome design on a separate ESP32-S3 audio board**, shown and
   driven by the panel through Phase 1.
5. **First step:** a one-evening spike (§7.1): panel running, ES8311 at 1 kHz,
   then one HTTP MP3 stream; measure MCLK, internal heap, the amp rail,
   brownout and panel stability.

## 1. What the flagship audio module does

### 1.1 Lineage

| Generation | Where | Stack | State |
|---|---|---|---|
| Loud-ESP32 classic (Sonocotta Rev F) | `NM/Oscilloscope/NickoSClock/Loud-firmware-src`, `…_Loud_squeezelite_nsp_uart_v0.1.4_…` | squeezelite-esp32 fork, IDF 4.3.5, GPL-3.0 | Paused 2026-08-14; built, never flashed |
| fw-audio-test | `NM/Electronic-Engeneering-Schema-PPCB/projects/NickoScope32-review/bringup/fw-audio-test` | Arduino 2.0.17, legacy `driver/i2s.h`, 48 kHz tone into PCM5101; NSP 0x53/0x55 to the H743 at 2.5 Mbaud | Receive confirmed on the H743, `crc=0`, 938 chunks/s |
| fw-audio-s3 1.2.3 | `BRU` | Arduino 2.0.17 + **ESP32-audioI2S tag 3.0.12**; radio, PCM5101 on I2S0, NSP + I2S1 to H743, text link to MAIN, web page | "Sound on both channels PASS" (`AUD/README.md:26-29`) |
| **AUDIO 1.0.5 (baseline)** | `AUD/esphome/audio-u601.yaml` | ESPHome 2026.6.5 / IDF 5.5.4, Sendspin, `speaker_source`, mixer, three own components | Baseline since 2026-09-08; paired with MAIN v33.64.0 and H743 v46.81.0 |

### 1.2 U601 hardware versus ours

ESP32-S3-WROOM-1 N16R8. I2S0 (BCK IO14, WS IO15, DATA IO16) to a **PCM5101A**
(pin-configured) → volume pots → two **LM4871** amps → two speakers; amp
shutdown from MAIN IO7. I2S mirror to the H743 on IO10/11/12; UART1 IO17/18 to
MAIN; UART0 IO43/44 to the H743. No mic, no SD. **Ours:** an **ES8311 codec that
needs I2C init and MCLK**, then one **NS4150B** mono amp gated by GPIO11; no H743.

### 1.3 Baseline 1.0.5 software (`AUD/esphome/audio-u601.yaml`)

| Block | Config | Lines |
|---|---|---|
| Framework | `esp-idf` 5.5.4; `CONFIG_SPIRAM_TRY_ALLOCATE_WIFI_LWIP`, `CONFIG_MBEDTLS_EXTERNAL_MEM_ALLOC` | 70-77 |
| Memory | PSRAM octal 80 MHz; 16 MB `qio`; littlefs 6 MiB | 57-69, 79-81 |
| DAC output | `i2s_audio` WS 15, BCLK 14; speaker DOUT 16, 48 kHz/16 bit/stereo, 200 ms buffer | 117-132 |
| Mixer | `mix_media` + `mix_announce` (200 ms each), two resamplers, stacks in PSRAM | 134-155 |
| H743 tap | `ns32_i2s_mirror` via `esp_rom_gpio_connect_out_signal` | 162-166 |
| Sources | `sendspin` hub and media source (48 kHz, decode in PSRAM); `audio_http` 200 KB; announcements 100 KB | 168-185 |
| Players | `speaker_source` FLAC pipelines, `volume_initial: 40%`, ducking −20 dB 0.3 s / 0.8 s; `sendspin` group | 187-226 |
| Link to MAIN | UART 921600, `ns32_nsp`: transport → group, volume → player | 243-262 |

RAM 54 168 B (16.5 %), flash 1 289 995 B (25.9 %). 1.0.0 soaked 9 h without a reboot.

### 1.4 Libraries and licences

| Component | Used in | Licence | Source |
|---|---|---|---|
| Sendspin, `sendspin-cpp` 0.7.0 | 1.0.5 | Apache-2.0; IDF ≥ 5.1 | `ARCH-OPTIONS:17-19, 79-81` |
| esp-audio-libs 3.2.1 | 1.0.5 | BSD-3 / Apache-2.0 | `ARCH-OPTIONS:68-69` |
| micro-mp3, micro-flac | 1.0.5 | Apache-2.0 | `ARCH-OPTIONS:70-72` |
| ESP32-audioI2S **tag 3.0.12** | bring-up 1.2.3 | **GPL-3.0** (`LIB/../LICENSE`) | `BRU/platformio.ini` |
| Its MP3/AAC decoders | 1.2.3 | "based on helix" (headers); Helix RPSL/RCSL per research C | `LIB/mp3_decoder`, `LIB/aac_decoder` |
| squeezelite-esp32 | Loud classic | GPL-3.0+ | research C |

micro-mp3: 13.1× realtime on the S3 in ~22.8 KB, dropping to 4.7× with 3–4
decoders in parallel — hence the flagship rule "no more than two active
decoders". No AAC decoder in ESPHome's audio layer or esp-audio-libs 3.2.1.
**This fork is MIT** (`APC/LICENSE`); linking GPL-3.0 audioI2S is the owner's
decision, which is why the audio half sits behind its own flag. No permissive
decoder verified for arduino-esp32 2.0.17. Not legal advice.

### 1.5 Tasks and buffers

- **1.0.5:** mixer, resamplers and Sendspin stacks in PSRAM; `ns32_nsp` parses
  in the main loop (≤ 512 B a pass); DAC 200 ms, mixer 200 ms, `audio_http`
  200 KB, announcements 100 KB.
- **1.2.3 (the pattern that ports):** audioI2S installs legacy I2S0 at 44.1 kHz,
  `dma_buf_count 16`, `dma_buf_len 512`, `I2S_MCLK_MULTIPLE_128`
  (`LIB/Audio.cpp:240-251`); decoder task **unpinned, priority 4, 3300 B**
  (`:6326`), wakes every 7 ms; input buffer ~655 KB PSRAM (`LIB/Audio.h:109-116`);
  PCM tap through weak `audio_process_i2s(...)`; **`connecttohost()` blocks the
  caller** for DNS+TCP (`BRU/src/hal_audio.cpp:80-83`), serialised by a mutex.

### 1.6 Stations

- **1.2.3:** three compiled-in stations (Riviera Radio HTTPS MP3 256, Yellow
  Riviera HTTPS MP3 128, SomaFM Groove Salad HTTP MP3 128); `RADIO n | next |
  <url> | 0`; **silence fallback** — no PCM for 15 s hops to the next station,
  at most every 20 s (`audio_core.h:26-34, 79`), added after an Infomaniak 302
  left the library "playing" with no PCM.
- **1.0.5:** no local catalogue; stations are whatever MA plays.
- **Recorded decisions (not built):** MAIN owns the catalogue from MA's library;
  "last started wins" with MQTT state; AAC from the start ("не колхоз, а хорошее
  радио") — `ns32_radio` with playlists, redirects, ICY, back-off, buffer, HTTPS
  with heap measurement, catalogue in LittleFS with a radio-browser.info search.
- **UI precedent, H743 fx32 Radiola v2.0:** the dial is a remote (pointer on
  FM, catch within ±0.6 MHz); click toggles TUNE/VOLUME; the screen shows what
  is **confirmed playing** (0xB9), not what was requested.

### 1.7 How HA and MA see and control it

- **MA:** Sendspin player (node port 8928, server 8927), worked without provider
  setup. MA's Sendspin provider declares no `PLAY_ANNOUNCEMENT` or `SEEK`.
- **HA entities** (idle today): `media_player.nickoscope32_audio_s3_player`,
  `…_group`, `media_player.nickoscope32_audio_s3`.
- **Announcements:** `tts.speak` on the ESPHome entity ducks −20 dB; MA's
  `play_announcement` pauses ~12 s without ducking.
- **NSP from MAIN:** frame `A5 01 TYPE LEN payload CRC16 5A`; accepts 0x73
  toggle … 0x7B volume set, PING/PONG; honest NACK for seek/source; sends 0xBE
  transport, 0xBC volume 0..30, 0xB8 station, 0xBD artist/album/title.
- **Not present:** no MQTT `media_player` platform in HA; no MQTT on U601.

### 1.8 Known bugs and fixes worth carrying over

| Finding | Relevance here |
|---|---|
| A tee in the audio path cut 48 000 → ~8000 frames/s (1.0.2 rollback, 1.0.3 GPIO-matrix mirror) | **Nothing heavy in the PCM path**; a spectrum tap copies non-blocking and drops |
| Partial-frame ring writes swapped L/R; a byte-ring reset from a second task tripped `configASSERT` | Same traps for a PCM ring feeding the spectrum |
| A periodic resend hung on a PING MAIN never sends | Don't hang periodic state on a peer's behaviour |
| Periodic 0xBD broke lyrics on the H743 | Retained MQTT state must not re-trigger "new track"; compare ids |
| ROM boot log prints on UART0 TX (**GPIO43**) at every reset | **GPIO43 is our ES8311 BCLK** (§2.3) |
| S3 has no APLL; BCLK from a fractional PLL divider | Judge THD by ear and meter |
| RTC clock source must stay internal RC | Default in 2.0.17 |

## 2. Hardware fit on the Waveshare board

### 2.1 Audio pins

| Signal | GPIO |
|---|---|
| I2C SDA / SCL | 47 / 48 |
| I2S BCLK | 43 |
| I2S MCLK | 12 |
| I2S WS | 38 |
| I2S DOUT → ES8311 | 21 |
| I2S DSIN ← ES7210 | 39 |
| Amp enable (NS4150B) | 11, active high |

From BSP `config.h` and [02](02-controller.md). Schematic text layer: U9
**ES8311**, **ES7210**, **NS4150B** with `PA_CTRL`; "ES8311 → NS4150B →
speaker" is the likely reading, **not traced**. ES8311 at 0x18 per ESPHome docs
(Waveshare's macro not read — confirm by I2C scan). Init from Waveshare
`09_Music_Player/es8311.cpp` (reset, clock coefficients assuming MCLK = 256·fs,
16 bit, volume reg 0x32).

### 2.2 HUB75 against I2S

`ESP32-HUB75-MatrixPanel-DMA` 3.0.14 selects `gdma_lcd_parallel16` on the S3:
`LCD_CAM` + GDMA, i8080 mode. **No I2S port is used by the panel.** Frame
buffers in internal SRAM. Vendor coexistence proof is on arduino-esp32 3.3.7
with a newer audioI2S API; it does not compile on 2.0.17 as is.

### 2.3 Pin conflicts

None between audio {11, 12, 21, 38, 39, 43} and HUB75, TF card (1/17/44),
encoder (45/46/0), USB (19/20). I2C 47/48 is shared with RTC/SHTC3/IMU (the
firmware does not call `Wire.begin` today). Notes:
- **GPIO43** carries the ROM boot log at reset onto the codec BCLK — listen for a click.
- **GPIO11** floating at boot — drive low first thing if the amp pops.
- **GPIO46** `mic_power_rail` is unverified and is the encoder's B line — leave the mics alone.
- **IO14** is reserved for the IR receiver ([11](11-control-and-pins.md)).

### 2.4 Power

5 V 10 A supply; the controller currently runs from its USB socket. The
NS4150B rail (5 V or 3.3 V) was **not read**: on 5 V at most ~1.56 W into 8 Ω
(peak ~0.63 A), on 3.3 V ~0.68 W. Risk of brownout on USB power with Wi-Fi TX
bursts — bench: amp rail voltage, 5 V sag at full volume, `esp_reset_reason()`.

### 2.5 Seating the audio module

| Option | What | Verdict |
|---|---|---|
| **A. Onboard ES8311 + NS4150B, this firmware** | 1.2.3 pattern + Waveshare ES8311 init | **Recommended for local radio** (Phase 2), subject to GPL decision and bench |
| **B. External ESP32-S3 node with the U601 ESPHome design** | Re-pin `audio-u601.yaml`, MQTT/HA instead of NSP; candidates: Loud-ESP32-S3 Rev G, Sonocotta configs in `audiodock-s3/firmware/esphome/` | **Optional Phase 4** — the only native MA/Sendspin player with ducking |
| C. External I2S DAC on free pins | only 45/46 on the header, both used | Rejected |
| D. Replace the panel firmware with ESPHome | loses every page | Rejected |

## 3. Software architecture here

### 3.1 Modules and flags

```
src/media/  media.h · media_model.cpp · media_ha.cpp (MQTT) · media_page.cpp
            radio_core.cpp/.h (host-testable, port of BRU audio_core)
            radio_hal_esp.cpp (audioI2S glue, radioCtl task, PCM tap)
            es8311.cpp/.h (vendored, Apache-2.0 repo) · radio_store.cpp · media_disc.cpp
src/web/web_media.cpp  /api/media
tools/media/           host test + preview renderer
```

- `MEDIAPLAYER_ENABLED` — display and remote; needs `MQTT_BUS_ENABLED` and `CONTROL_ENCODER_ENABLED`.
- `MEDIAPLAYER_RADIO_ENABLED` — local audio; needs the above plus `BOARD_WAVESHARE_RGB_MATRIX` and `BOARD_HAS_PSRAM`; adds audioI2S to this env only.
- Flag matrix rows: builds (media+knob+mqtt; full board with radio) and refusals (no mqtt; radio without media; radio without board).

### 3.2 Pipeline and cores

```
core 1: loopTask ── page ── WebServer ── mqttBusLoop ── mediaTick()   (commands via queue)
core 0: radioCtl (prio 2, ~6 KB) owns Audio: connecttohost/stop/loop
        PeriodicTask (lib, prio 4) ── decode ── I2S0 DMA ── ES8311 ── NS4150B
                   └─ audio_process_i2s ── non-blocking copy ── PSRAM ring (spectrum)
        Wi-Fi, luafx (1), rttfetch (1), weather (1)
HUB75:  LCD_CAM + GDMA, independent of loop()
```

Three required patches to audioI2S 3.0.12 (vendored under `lib/`):
1. **Pin PeriodicTask to core 0** (`LIB/Audio.cpp:6326`) — unpinned at prio 4 it can preempt `loop()`.
2. **Shrink I2S DMA** from 16×512 (32.8 KB internal) to ~6×256 (~6 KB); bench for underruns. Internal low-water with Lua is ~32 KB; the rail fetch gate is 28 KB.
3. **Never call `connecttohost()` from `loop()`** (15 s panic watchdog) — only from radioCtl.

### 3.3 Memory (proposal, to be measured)

I2S DMA ~6 KB internal · PeriodicTask 3.3 KB · radioCtl 6 KB · input buffer
~655 KB PSRAM (reducible) · decoder state unmeasured · HTTPS TLS via
`tlsUsePsram()` · spectrum ring 4 KB PSRAM. Heap gate before a stream start
(proposed: internal free ≥ 40 KB, largest block ≥ 16 KB; set from spike
numbers). **One TLS at a time** — prefer HTTP stations; no HTTPS stream while
the AIS websocket is up.

### 3.4 Decode cost, coexistence, watchdog

Helix MP3/AAC in 3.0.12 **not measured** here — bench Lua draw time and loop
fps with radio off / MP3 128 / MP3 320 / AAC 128. Acceptance: Lua draw average
+≤ 2 ms, panel refresh unchanged, no underruns in 30 min. Radio is independent
of the page. radioCtl is not on the task watchdog; its health is the 15 s
silence detector.

### 3.5 Knob and page

`PAGE_MEDIA` in `src/main.cpp`; hint "TURN: STATION"; 20 s carousel slot.
Inside: click cycles **TUNE** (rotate = previous/next station, slot 0 = OFF,
starts after the knob rests 1.2 s) → **VOLUME** (±2 %, deferred NVS write) →
leave. Source selection (local radio or an HA player) on the web page.

## 4. Home Assistant integration

The owner runs HA 2026.9.2, Music Assistant 2.10.3, Mosquitto 7.1.1, AppDaemon
0.19.2; no `mqtt_statestream`. Precedent: NickoScope-TFT ADD-04 chose option (a)
and built it (v0.47.0 player-mqtt, v0.48.0 player-radio).

| | (a) Display + remote via MQTT | (b) Panel as MA/DLNA renderer | (c) ESPHome-style API |
|---|---|---|---|
| How | HA automation/AppDaemon publishes compact state for a chosen player; panel publishes commands mapped to `media_player.*` / `music_assistant.play_media` | Sendspin blocked (IDF ≥ 5.1); squeezelite client GPL reference; DLNA no sync | Native API in Arduino: no library. **c-lite:** MQTT-discovery select/number/button/sensor for the local radio |
| Effort | fw ~3 d, HA ~1 d | weeks | full: weeks; c-lite ~1 d on top of Phase 2 |
| Latency | est. 100–500 ms, not measured | seconds | as (a) |

**Recommendation: (a) now, plus c-lite for the panel's own radio in Phase 2.**
A real MA group member → option B of §2.5, not a renderer inside this firmware.

Proposed contract under `nickoscope_matrix/<dev>/media/`: `state` (retained,
with epoch `ts`, player, state, title/artist/album, kind, vol, pos + `pos_at`,
dur), `players` (≤ 8), `favs` (≤ 16 MA radio favourites), `cmd`
(toggle/next/prev/vol/play_fav/select), `radio/state`. Publish only on real
changes; payloads ≤ 2048 B (the bus buffer). HA-side YAML goes through the
owner's HA best-practices review first.

## 5. Internet radio (Phase 2)

- **Stations:** `/media/stations.json` in LittleFS, ≤ 32 entries `{name, url, codec, kbit, flags}`, slot 0 OFF; TF card import/export; selection and volume in NVS `media`.
- **Web:** now playing, source, play/stop/volume, station editor with test play, browser-side radio-browser.info search (terms not verified), JSON-only `/api/media`.
- **Formats:** MP3 CBR first; the 3.0.12 tree has AAC/FLAC/Opus/Vorbis decoders; HE-AAC and HLS not verified; playlists handled.
- **Metadata:** ICY `StreamTitle`; Cyrillic on the panel font **not verified** — transliterate first.
- **Reconnect:** retry the same station 2/4/8/16/32 s then every 60 s; dead after 5 failures; hop only if flagged; 15 s silence detector catches stuck streams.
- **Volume:** audioI2S 0..21 plus a bench-calibrated ES8311 reg 0x32; amp off when stopped; mono downmix (L+R)/2 if needed.
- **HA (c-lite):** select station, number volume, button stop, sensors for station, title, state.

## 6. The 128×64 UI

Now playing (HA/MA): source tag + player + state + clock; artist, title
(scrolling), album; progress from `pos + (now − pos_at)`; volume bar and hint.
Now playing (local radio): station + LIVE dot; ICY title; 32-bar spectrum from
the PCM tap; volume, codec/bitrate, buffer %, Wi-Fi. Tuning: a dial with the
current station bright and neighbours dim, "starts in 1.2 s". Station list;
volume overlay band for 1.6 s. Optional later: 64×64 album art via AppDaemon
(raw RGB565 over LAN HTTP; the panel has no JPEG decoder) and an XY scope from
stereo PCM — which, per the owner's verdict on clips, must be plain L = X,
R = Y.

## 7. Plan

### 7.1 Phase 0 — one-evening spike (bench env, nothing merges)

| # | Step | Record |
|---|---|---|
| 1 | HUB75 pattern at the firmware's config | stable picture, refresh Hz |
| 2 | GPIO11 low; I2C scan 47/48 | ACK at 0x18, RTC/SHTC3 still answer |
| 3 | ES8311 init; 1 kHz sine at 48 kHz on 43/38/21 + MCLK 12 | clean; **MCLK frequency on GPIO12** (12.288 or 6.144 MHz) |
| 4 | Amp rail and 5 V sag at full volume, USB vs 5 V posts | voltages, no brownout |
| 5 | audioI2S 3.0.12 (patched): SomaFM Groove Salad HTTP MP3 128, 10 min | plays, ICY arrives, decoder heap line |
| 6 | Same with Lua-like load on core 0 and 20 fps drawing on core 1 | internal free/low-water/largest block, PSRAM, draw delta, no clicks |
| 7 | Reset with the amp powered | click from GPIO43? pop at boot? |
| 8 | 30 min temperature | noted |

Stop if the codec never ACKs, brownout on the 5 V posts, loop fps −20 %, or
internal low-water < 20 KB.

### 7.2 Phases

| Phase | Content | Effort | Gate |
|---|---|---|---|
| 1. Display + remote | model, HA MQTT, page, knob, web, HA automation/AppDaemon, previews, flag rows | fw 3 d + HA 1 d + bench 0.5 d | panel follows `media_player.nickoscope32_audio_s3`; knob volume and favourite; stale shown; heap flat |
| 0. Spike | §7.1 | 0.5 d | numbers into [02](02-controller.md) |
| 2. Local radio | GPL decision; patched audioI2S; radioCtl; ES8311; stations + web; reconnect; c-lite; 8 h soak | 6–8 d | no reboot, heap gate held, reconnects recover, rail still fetching, Lua delta in bounds |
| 3. Visuals | spectrum, scope, album art | 1.5 d + 2 d | no dropouts from the tap |
| 4. External node (optional) | U601 YAML on a spare ESP32-S3 audio board | 1–2 d + bench | visible in MA, ducking, panel reflects it |

Main risks: GPL-3.0 in an MIT fork (owner decides; flag-separated); internal
heap (DMA patch, gate, HTTP stations); unpinned decoder task (patch); MCLK
ratio (measure); brownout on USB power; boot pops; Cyrillic titles.

## 8. Not verified

ES8311 address macro; NS4150B rail and wiring; audioI2S 3.0.12's real MCLK
multiple (source comment ambiguous); mono slot and in-place PCM hook;
HUB75+audio together on 2.0.17; helix decode cost and heap; HE-AAC/HLS and a
connect timeout in 3.0.12; IDLE0 watchdog in 2.0.17; GPIO46 mic rail; I2C 1.8 V
on WROOM-2; `music_assistant.get_library` parameters; HA↔panel MQTT latency;
album-art pipeline; radio-browser terms; a permissive Arduino MP3/AAC decoder;
Loud-ESP32-S3 Rev G fitness; whether the firmware already publishes MQTT
discovery.

## 9. Sources

- **Target:** `APC/platformio.ini`; `APC/src/main.cpp`; `src/mqtt/mqtt_bus.*`; `src/network/tls_psram.cpp`; `src/railboard/rtt_direct.cpp`; `src/lua/lua_effects.cpp`; `src/viz/*`; `src/web/web*.cpp`; `tools/flag_matrix.py`; `LICENSE`; HUB75 lib `platform_detect.hpp:32-36`, `esp32s3/gdma_lcd_parallel16.cpp`.
- **KB:** `HANDOFF.md`; docs 02, 07, 11, 12, 13, 14; `reference-drawings/controller/ESP32-S3-RGB-Matrix-Schematics.pdf`.
- **Flagship audio node (`AUD`):** `NickoScope32_ADD-93_Audio_Node_U601_ESPHome_Sendspin_v1.0_2026-09-06.md`; `ARCH-OPTIONS_2026-09-06.md`; `CHANGELOG-v1B.md`; `README.md`; `esphome/audio-u601.yaml`; `esphome/components/ns32_nsp/*`, `ns32_i2s_mirror/*`; `research/2026-09-06_{A,B,C}_*.md`.
- **Bring-up:** `BRU` (`platformio.ini`, `src/audio_core.h`, `src/hal_audio.cpp`); audioI2S 3.0.12 in its `.pio/libdeps`; `…/projects/NickoScope32-review/bringup/fw-audio-test/`, `BRING-UP-PLAN.md`.
- **MAIN/H743 (the side that talks to it):** `NickoScope32_ESP32S3_v33.55.0_fx32_radiola_input_2026-08-27/src/main.cpp`, `src/nsp.h`, `src/loud_uart.cpp`; `NickoScope32-v1B-Main-S3-v33.64.0/src/nsp.h`; `NickoScope32_STM32H743_v46.65.0_radiola_live_tuning_2026-08-27/src/effects/fx32_radiola.cpp`, `src/nsp_handler_fx32.cpp`.
- **Related:** `Loud-firmware-src/…`; NickoScope-TFT ADD-01, ADD-04, `NickoScope_TFT_v0.48.0_player-radio_2026-06-23/`; `audiodock-s3/`; `3D Project/esphome-atom-voices3r-led/atom-voices3r-led.yaml`.
- **Vendor (fetched 2026-09-14):** `github.com/waveshareteam/ESP32-S3-RGB-Matrix` @ `4047e4e` (BSP `config.h`, `09_Music_Player.ino`, `es8311.cpp`); https://esphome.io/components/audio_dac/es8311/
- **Live, read-only over `ssh nickohome`:** HA version, add-ons, packages, `media_player` entities and Music Assistant actions; no secrets printed.
