# 26. The MTR-1 straight to the panel, or through Home Assistant

**HW deep-dive report, 2026-09-17.** The owner asked whether the Apollo MTR-1
should feed the LED panel directly - UART, ESP-NOW, I2C - instead of the
current chain through Home Assistant, AppDaemon and the MQTT broker, and then
asked the sharper question: how heavy is the current chain for Home Assistant,
and does it get in the way of anything.

Written to the `nickoscope-hw-deep-dive` protocol: sources before code, a pin
audit against the production tree, a conflict matrix, traps with their failure
mechanism, and a bench procedure for what only hardware can answer. Three
research strands ran in parallel (the sensor's side, the panel's radio on our
exact SDK, every alternative); the pin audit and the Home Assistant
measurements were done directly.

## Verdict

**Stay on Home Assistant for now, and exclude the MTR-1's fast target sensors
from the recorder.** The chain costs Home Assistant almost nothing; the one
real cost - recorder rows - does not come from the panel link at all, and the
exclusion removes it whichever way the panel is fed.

**A direct link is feasible and worth keeping as the upgrade path**, not today's
work. If it is ever built, it is one compact binary packet of our own, sent from
the radar's `on_data` event with raw values from a single frame, received over
**UDP or ESP-NOW broadcast with one decoder** - chosen on the bench. It buys
10 Hz, X and Y from the same frame, and independence from Home Assistant
restarts. It costs a firmware of our own on the MTR-1, two things only a bench
can settle, and it lands after debt D1.

**Wired links and I2C are out** on hard constraints: the panel has no free pin,
and I2C has no slave mode in ESPHome and no business on a cable across a room.

| Option | Verdict | The deciding reason |
|---|---|---|
| **Home Assistant, as now** | **keep** | measured cost to HA is negligible; ~1 Hz and a dependency on the HA host are the limits |
| UDP, own packet (`udp.write`) | upgrade path | no channel coupling; needs only the router |
| ESP-NOW broadcast, own packet (`espnow.send`) | upgrade path | proven on our SDK in NickoScope32; channel and roaming must be handled |
| ESP-NOW unicast | bench first | receive with STA connected is unconfirmed on arduino-esp32 2.x |
| ESPHome `packet_transport` | no | non-standard XXTEA, float+name format, GPL code we may not copy into an MIT fork |
| Direct MQTT from ESPHome | no | the broker lives on the HA host - not "without HA"; `retain` and `discovery` traps |
| UART tap of the radar TX | no | no free panel pin; radar only; ESPHome's config commands silence the line |
| C3's second UART | no | no free panel pin; needs Apollo's mezzanine header and a cable of unspecified length |
| I2C | no | no I2C slave in ESPHome; the panel's bus is internal, 1.8 V, shared with the codecs |
| Panel as an ESPHome API client | no | no MCU client library; Noise, protobuf, and still 1 Hz |

**Confidence:** HIGH for the Home Assistant costs (measured), HIGH for the
rejections (hard constraints), **MEDIUM for a radio link** - documentation,
source reading and one in-house precedent for broadcast, but unicast receive
and the panel's heap delta are unmeasured.

---

## 1. Identification

| | | Source |
|---|---|---|
| Sensor | Apollo Automation **MTR-1**, entity stem `apollo_mtr_1_53bc60`, IP 192.168.4.21 | HA registry |
| Module | Espressif **ESP32-C3-MINI-1** family: 4 MB in-package flash, 400 KB SRAM, no PSRAM. Exact variant (N4/H4, antenna) not verified | datasheet v1.3 in `ApolloAutomation/MTR-1/Datasheets` |
| Firmware | Apollo **26.3.2.1** (`main`), ESPHome **2026.3.3** (ESP-IDF 5.5.3.1), LD2450 firmware 2.04.23101915 | HA sensors; `esphome/components/esp32/__init__.py` at the tag |
| Entities in HA | 46 sensors + 4 binary sensors | HA registry |
| Sensor pins | radar UART TX21 / RX20 at 256 000, `rx_buffer_size: 1024`; I2C SDA1 / SCL0 (DPS310, LTR-390, SCD40); WS2812 on 3; buzzer 10; button 9 | `Core.yaml`, commit 43437f6 |
| Schematic | not published | repo, datasheet |
| Panel | Waveshare ESP32-S3-RGB-Matrix, ESP32-S3-WROOM-2-N32R16V; arduino-esp32 **2.0.17** on ESP-IDF **4.4.7** | `platformio.ini`; header diff against the v4.4.7 tag |

Apollo does not pin an ESPHome version (`min_version: 2025.8.0`, CI builds
`stable`). Three variants exist - `MTR-1_Factory.yaml` (improv, BLE, power save
`light`), `MTR-1.yaml` (no BLE, `power_save_mode: none`), `MTR-1_BLE.yaml`
(Bluetooth proxy, `light`). Which one is on the device is not verified.

## 2. What the current chain costs Home Assistant

Measured 2026-09-17 08:44-08:58 on the live system, read-only.

| | Measured | How |
|---|---|---|
| Host | HAOS 18.2, x86-64, 16 GB RAM, 468.7 GB disk, 30.8 GB used | system health |
| Mosquitto add-on, whole | **0.07 % CPU, 17.4 MiB** | Supervisor stats |
| AppDaemon add-on, whole (all its apps, `matrix_presence` being one) | **1.78 % CPU, 253.8 MiB** | Supervisor stats |
| Recorder | SQLite, 1.10 GB, oldest row 2026-09-07 | file size; `sqlite3 -readonly` |
| MTR-1 state rows, 10 min, one mostly still person | 1,155 rows = **1.9 rows/s**; target 1 angle, x, y, distance ~0.33/s each | recorder history |
| **MTR-1 state rows, last 24 h** | **156,299 = 39.5 % of all rows HA wrote** (395,342) | `sqlite3 -readonly`, grouped by `states_meta` |

**The finding that settles the question: the recorder cost does not come from
the panel link.** The rows are written because the MTR-1 is an ESPHome device in
Home Assistant with the recorder on. AppDaemon forwarding the targets to the
panel adds none of them. Feeding the panel directly would leave every row in
place; excluding the fast target sensors removes them whether or not the panel
stays on Home Assistant. At ~2 events a second nothing else in Home Assistant is
affected.

docs/23 §6 had projected 61,671 rows a day; today's direct count is 156,299. The
difference was not investigated - more occupancy and the direction and speed
sensors are the likely part of it.

### The recorder exclusion, MTR-1 only

| Remove | Rows / 24 h | Why it is safe |
|---|---|---|
| target 1 `x`, `y` | 20,253 + 20,146 | the panel and the radar card read them live; history was used only for our own investigations |
| target 1 `angle`, `distance` | 20,535 + 20,096 | derived from x and y; the card computes both itself |
| target 1 `direction`, `speed` | 16,058 + 8,677 | dashboard tiles, live |
| target 2, all six | 23,159 | the same for the second person |
| target 3, `resolution` | small now | grows with a third person |
| `moving_target_count`, `still_target_count` | 7,361 + 7,285 | the binary moving/still sensors stay on the history graph |
| `uptime` | 1,014 | a counter |
| **Total** | **~144,600 a day, 92 % of the MTR-1's rows** | |

| Keep | Why |
|---|---|
| binary presence, moving, still; `presence_target_count` | the "История присутствия" graphs on the Радар MTR-1 dashboard |
| `ltr390_light` | the light trend on the same dashboard |
| DPS310 pressure and temperature | long-term statistics (`state_class`), ~2,000 rows a day each |
| RSSI, chip temperature, CO2, zone counts | few rows, diagnostics |

Checked before recommending it:
- the `mtr1-radar-card` resource was decoded (12,143 bytes): **0** calls to
  history, recorder, `callWS`, `callApi` or `fetch`; its trail is a buffer in
  the browser, filled from live states in `set hass()`;
- no AppDaemon app calls history;
- the target sensors have no `state_class`, so no long-term statistics are lost -
  only the 10-day history.

**The price:** the 10-day history of coordinates goes, and it was what the
second-person investigation of 2026-09-16 ran on. Re-include for the length of
an investigation when one is needed. Old rows age out over 10 days; the file does
not shrink without a repack. **Not applied - it is a `configuration.yaml`
change, owner's word and a backup first.**

## 3. What a radio link needs on the sensor

- **Rebuild on ESPHome >= 2026.6.4, better 2026.8.x.** Two bugs in the 2026.3.3
  the device runs make it unusable for this:
  [#17265](https://github.com/esphome/esphome/issues/17265) - `send()` from a lambda
  without a callback throws `bad_function_call` and **reboots on every successful
  send** (fixed 2026.6.3);
  [#17267](https://github.com/esphome/esphome/issues/17267) /
  [PR #17271](https://github.com/esphome/esphome/pull/17271) - a received frame over
  250 bytes overflows the buffer and corrupts the pool, triggerable by any ESP-NOW v2
  device in range (fixed 2026.6.4). The channel poll on every loop pass is gone
  from 2026.8.0 ([PR #18027](https://github.com/esphome/esphome/pull/18027)).
- **`espnow`** arrived in 2025.8.0 ([PR #9582](https://github.com/esphome/esphome/pull/9582));
  **`udp`** in 2024.9.0 ([PR #6865](https://github.com/esphome/esphome/pull/6865)), with
  `udp.write` taking a byte list from a lambda
  ([docs](https://esphome.io/components/udp/)). Both run beside `wifi:` and `api:`,
  so **the MTR-1 stays in Home Assistant**. With Wi-Fi on, `espnow` cannot set a
  channel (`OnlyWithout(CONF_CHANNEL, CONF_WIFI)`) - it follows the AP.
- **10 Hz without touching Home Assistant:** `ld2450: on_data`, since 2026.2.0
  ([PR #13601](https://github.com/esphome/esphome/pull/13601)), fires once per radar
  frame; read `get_raw_state()` of the target sensors inside it. Raw values come
  before the per-sensor filters, so **X, Y and speed are from the same frame** and
  the phase skew between X and Y (docs/23) disappears for the panel. `.raw_state`
  is deprecated from 2026.4.0 and removed in 2026.10.0 - use the getter.
- **The filters must stay on the HA entities.** Every sensor carries
  `timeout: 1s` and `throttle_with_priority: 1000ms` (`ld2450/sensor.py`), and the
  component publishes only on change (`publish_state_if_not_dup`, `ld24xx.h`).
  Stripping them would multiply the recorder rows by about ten.
- **Obstacle: Apollo's target sensors have no `id`.** `!extend` needs one, and a
  second `sensor: platform: ld2450` block takes over the component's slot pointer -
  the HA entities would silently stop updating. Ways round: find them by name
  through `App.get_sensors()` at boot (breaks if Apollo renames), or keep our own
  copy of `Core.yaml` with ids added (loses package updates). Light, pressure and
  CO2 already have ids: `ltr390light`, `dps310pressure`, `co2`.
- **The packet:** ~55 bytes by estimate (three targets of x, y, speed, counts,
  lux, UV, pressure, temperature, CO2, a frame counter, a version, a CRC). Under
  ESP-NOW v1's 250 and far under UDP's 508.
- **Not `packet_transport`.** It is one format for both transports, which is
  attractive, but its XXTEA is non-standard (key index `& 7`), it carries only
  float-plus-name numeric and binary sensors (no text), it writes a rolling code
  to flash on every boot, a 252-byte alignment bug exists
  ([#13151](https://github.com/esphome/esphome/issues/13151)), and ESPHome's C++ is
  GPLv3 while our fork is MIT. Our own struct is simpler and ours.

**Self-update, resolved.** `main` Core.yaml (26.3.2.1, on the device) has no
`http_request` and no `update:`; Home Assistant shows no update entity for the
MTR-1. `beta` Core.yaml (26.8.27.1) has `http_request:` and
`id(update_http_request)` - PR #95 "Add managed firmware update system", merged
into `beta` 2026-06-17. **Dormant today; once it reaches `main`, an "Update" press
in Home Assistant would flash stock firmware and erase our link without an
error.**

## 4. What a radio link needs on the panel

- **API on our SDK** (header byte-identical to the v4.4.7 tag): receive callback
  `void (*)(const uint8_t *mac, const uint8_t *data, int len)`; `esp_now_recv_info_t`
  is 5.1+; **250 bytes maximum** (`ESP_NOW_MAX_DATA_LEN_V2` is 5.4+). No `ESPNOW`
  wrapper in arduino-esp32 2.0.17 - plain `esp_now.h`.
- **The callback runs in the Wi-Fi task, priority 23, core 0**
  (`CONFIG_ESP32_WIFI_TASK_PINNED_TO_CORE_0`). It must copy up to 250 bytes into a
  static mailbox under a spinlock and return - the way `src/presence/presence.cpp`
  already works. No `malloc` (anything up to 4 KB goes internal,
  `SPIRAM_MALLOC_ALWAYSINTERNAL=4096`), no `Serial` (HWCDC waits up to 100 ms on a
  mutex), no blocking queue send - the official v4.4.7 example blocks the Wi-Fi task
  for up to 512 ms. A stalled Wi-Fi task starves the same RX buffers whose
  exhaustion hung this panel (docs/22 §12.3).
- **Heap:** no published figure exists. Disassembly of `libespnow.a` from 2.0.17:
  `esp_now_init` creates one recursive mutex (~100 B internal); peers (192 B) and
  sends (36 B) go through `wifi_malloc`, which prefers PSRAM
  (`heap_caps_malloc_prefer`, matching `esp_adapter.c:60`). Receive buffers are
  probably PSRAM (inferred). **Expected delta ~0.1 KB plus our mailbox - to be
  measured.**
- **Effective Wi-Fi buffers** are not the sdkconfig's: `WiFiGeneric.cpp` defaults
  `_wifiUseStaticBuffers=false`, so the driver starts with static RX 4, dynamic RX
  32, dynamic TX 32, cache TX 4. ESP-NOW adds no static buffers.
- **Coexistence:** our code calls `WiFi.setSleep(false)` (`main.cpp:470`,
  `network.cpp:413`), which the v4.4.7 example README requires for ESP-NOW with a
  connected STA. A receiver needs no `add_peer` for broadcast or unencrypted
  unicast (esp-idf#10341, an Espressif engineer, 2024-03-26).
- **Unicast receive with STA connected is unconfirmed on 2.x:**
  [arduino-esp32#8912](https://github.com/espressif/arduino-esp32/issues/8912) was
  reproduced on 2.0.14; the proposed lib-builder fix
  ([#165](https://github.com/espressif/esp32-arduino-lib-builder/pull/165)) closed
  unmerged. **Broadcast receive with STA connected works on this exact stack** in
  NickoScope32 v33.55.0 (S3, 2.0.17 / IDF 4.4.7), beside an eero on channel 11.
- **Silicon:** the ESP32-S3 errata list eight items, none about Wi-Fi or RF.

## 5. PIN AUDIT (production tree, e3b5f65)

| Pin | Taken now (file:line) | A wired link would need | Confirmed where | Strapping / limits | Verdict |
|---|---|---|---|---|---|
| **IO45** | `src/control/control.cpp:34` knob A; `src/ir/ir.cpp:43` IR default | UART RX | GPIO matrix | strapping (VDD_SPI; ignored, fuse burnt - docs/11); **10 kΩ pull-down R59** | **CONFLICT** |
| **IO46** | `src/control/control.cpp:35` knob B | UART TX | GPIO matrix; output-capable on S3 (datasheet I/O/T) | strapping (ROM log, boot mode); **10 kΩ R60** | **CONFLICT** |
| **IO0** | `src/control/control.cpp:36` knob switch, BOOT pad | - | - | boot mode | not a candidate |
| **IO14** | unused by firmware; `src/clips/clip_sd.h:14-16`: TF SD_CS, "planned as the IR receiver's input" | one UART line | GPIO matrix | needs **R47 (0 Ω) removed** (docs/11:69) | **NOT FREE AS BUILT** |
| **IO47 / IO48** | `src/board/board_i2c.h:3-15`: SHTC3, ES7210, ES8311, RTC, IMU at 100 kHz | I2C | board | **1.8 V on the module**, level-shifted; not on the header | **CONFLICT** |
| none | - | ESP-NOW, UDP | radio | - | no pin |

**Gate: every wired candidate is CONFLICT or NOT FREE.**

Two inconsistencies in our own tree surfaced along the way: `ir.cpp` defaults
`IR_PIN` to 45 while `clip_sd.h` and docs/11 plan IO14 for the IR receiver.

## 6. System conflict matrix

| Area | The tree | Consequence |
|---|---|---|
| Wi-Fi mode | `WIFI_STA` (`network.cpp:84`) | ESP-NOW on the AP's channel only |
| Power save | off (`main.cpp:470`, `network.cpp:413`) | frames are not lost to modem sleep |
| **`netRecover`** | `network.cpp:408-414`: `WiFi.disconnect(true)` + `mode(OFF)` = `esp_wifi_stop` and `esp_wifi_deinit` (`WiFiGeneric.cpp:705-741`) | ESP-NOW must be de-initialised before and re-initialised after; NickoScope32 recorded ~15 s of dead radio without it |
| Cores | `loop()` core 1; LwIP and the Wi-Fi task core 0, beside the Lua effect task, audio capture and fetch tasks | the Wi-Fi task pre-empts all of them; the callback must be short |
| Internal heap, live 08:50 | free 33,796 B, minimum 10,076 B, largest block 13,812 B | measured against D1 and against the 28 KB floor `aero_direct.cpp:55` and `rtt_direct.cpp:59` use |
| Presence seam | `presence.cpp:57` parse → `Report r[]`; `:76` `s_model.onMessage` | a new transport only has to fill `Report[]`; the model, its host checks and the `room_radar` scene stay untouched |
| HUB75 DMA + Wi-Fi on S3 | the library's own history: ping to 5,000 ms (HUB75#570), a dying panel at divider 10 (HUB75#441) | the heavy DMA load is already here; it is a reason to bench, not a new risk |

## 7. Traps, with how they fail

1. **Stripping the ESPHome filters on the HA entities for 10 Hz** - ten times the recorder rows. Use `on_data` with raw values instead.
2. **Building on ESPHome 2026.3.3** - a reboot on every successful ESP-NOW send; pool corruption from any long frame in range.
3. **A second `sensor: platform: ld2450` block** - the HA entities silently freeze.
4. **`post_connect_roaming` (default true):** 5 minutes after connecting, with RSSI below −49 dBm, the MTR-1 scans every channel (up to three times) and ESP-NOW is deaf meanwhile. **The MTR-1 reads −51 dBm in HA today.** `post_connect_roaming: false` with a single AP.
5. **Apollo's managed update** reaching `main` - an "Update" press erases our firmware silently.
6. **The panel's `netRecover`** without ESP-NOW de-init/re-init - the radio stays dead.
7. **Anything slow in the receive callback** - the Wi-Fi task stalls, RX buffers are not returned, and 6 s without beacons drops the STA.
8. **Router changes channel** (ESP-NOW) - the sensor keeps sending on the old one; unicast `SEND_FAIL`, broadcast silently lost.
9. **`wait_for_sent: true` default** with the panel off - the 16-packet send queue fills and ESPHome logs allocation failures.
10. **UDP to a DHCP address** without a reservation - silence after a lease change.
11. **A BLE firmware variant on the MTR-1** - radio time-shared with BLE plus `light` power save: jitter.
12. **`.raw_state`** - the build breaks on ESPHome 2026.10.0.

## 8. Open unknowns, and the bench that settles them

Not verified: unicast receive with STA connected on 2.0.17 from a C3 sender; the
real heap delta of `esp_now_init` and where receive buffers land; the Wi-Fi task
stack (3,072 or 6,144 B); whether receive survives `WiFi.begin` without
re-init; client isolation on the Wi-Fi (UDP); which MTR-1 firmware variant is
flashed; the real `on_data` rate; delivery rate and latency of every option; the
exact C3 module variant.

Each scenario a separate boot; numbers from `[mem]`, `MEMTRACE` and `/api/info`:
internal free (60 s median), internal minimum, largest internal block,
`allocFailCount()`, STA disconnects, `[loop] … took` lines,
`uxTaskGetStackHighWaterMark(xTaskGetHandle("wifi"))`; on the sender, the
sequence number and the `send_cb` success rate.

| | Scenario |
|---|---|
| T0 | current firmware, idle 10 min - the baseline |
| T1 | `esp_now_init` + mailbox callback, idle 10 min; Δ = T0 − T1 |
| T2 | sender broadcasts at 1 Hz, 30 min; losses by sequence number |
| T3 | sender unicasts to the panel's STA MAC at 1 Hz, 30 min - **decides unicast** |
| T4 | flood at 50-100 Hz for 60 s |
| T5 | T4 while the heaviest portal page loads |
| T6 | router reboot or channel change: does receive recover, does the sender find the channel |
| T7 | forced `netRecover`: is `esp_now_init` needed again |

The same T0, T2, T4-T6 run for UDP.

**Pass:** idle internal free after T1 stays at or above **28 KB** (the floor the
direct fetch modules already use; with 33 KB today that allows Δ ≤ ~5 KB);
`allocFailCount` does not grow in T4-T5; zero STA disconnects; no more loop
parts over 200 ms than the same run without the link; the internal minimum no
lower than the no-link run minus Δ. **Fail:** any allocation failure, a
disconnect under flood, a hang, or idle free below 28 KB. Loss percentages are
reference figures until each flood scenario has five repeats.

If T3 fails, broadcast remains. If T4 or T5 fails, the panel stays on MQTT - the
path that works today.

## 9. Sources

- **Espressif:** esp_now v4.4.7 (esp32s3), wifi v4.4.7, speed v4.4.7, ESP-FAQ ESP-NOW,
  ESP32-S3 errata, ESP32-C3 and S3 datasheets, `soc_caps.h`; local
  `framework-arduinoespressif32` (esp-idf v4.4.7 38eeba213a) headers, sdkconfig,
  `libespnow.a` disassembly; issues esp-idf#10341, #18682, #18438;
  arduino-esp32#8912; esp32-arduino-lib-builder PR #165.
- **ESPHome:** esphome.io components espnow, udp, packet_transport, mqtt, api,
  packages; source `espnow_component.cpp`, `packet_transport.cpp`, `xxtea.cpp`,
  `ld2450/sensor.py`, `ld24xx.h`, `sensor/filter.cpp`, `wifi_component.cpp`,
  `logger/__init__.py`; PRs #6865, #8187, #9582, #11025, #12472, #13601, #17271,
  #17360, #18027; issues #12359, #12366, #13151, #13956, #14807, #15531, #17238,
  #17265, #17267; feature requests #2081, #2979.
- **Apollo:** `ApolloAutomation/MTR-1` `main` and `beta` `Core.yaml`, `MTR-1.yaml`,
  `MTR-1_Factory.yaml`, `MTR-1_BLE.yaml`, `build.yml`, PR #77, #95; datasheets;
  wiki (updating firmware, GPIO header).
- **Hi-Link:** LD2450 serial protocol V1.03 (copy), user guide.
- **NXP:** UM10204 Rev. 7.0, Table 10-11, §7.1-7.2.
- **Precedents:** NickoScope32 v33.55.0 (in-house; broadcast ESP-NOW with STA on the
  same SDK); WLED + QuickESPNow; VentoSync, presence_1, MY-ESPHOME (anecdotal, no
  10 Hz); HUB75-DMA #441, #570.
- **Measured here:** HA system health and Supervisor stats; recorder history;
  `sqlite3 -readonly` on the recorder; the decoded `mtr1-radar-card` resource; the
  production tree at e3b5f65.
- **This knowledge base:** [11](11-control-and-pins.md), [16](16-presence-radar.md),
  [22](22-audio-visualizer-onboard-mic.md), [23](23-mtr1-deep-research.md).
