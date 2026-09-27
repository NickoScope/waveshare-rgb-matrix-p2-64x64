# 38. Mail, WhatsApp and a teletype network between the panels

A study and a design, 2026-09-27, at the owner's request:

> «Давай к нашей лед панели waveshare добавим функции email, WhatsApp клиент и
> свою телетайп сеть между семейством панелей, которая может быть клиентом любых
> esp32 устройств по единому протоколу. Поищи на гитхабе, кто что-то подобное
> делал или нет, что можно взять за референс.»

**Nothing is built yet.** This is the first-hour document that `00-how-we-work.md`
asks for. Four strands ran in parallel: mail, WhatsApp, the teletype network with
its prior art, and the firmware's integration points. Sources are linked where
they are used. Stars and dates were read on 2026-09-27. A figure marked
*estimate* has not been measured.

## The verdict in five lines

1. **The panel opens no new TLS session for any of this.** Mail and WhatsApp are
   read by bridges at home (Home Assistant / the RPi5). Those bridges hand the
   panel finished JSON over the local MQTT bus it already has. That is the lesson
   of [32](32-net-broker.md), and of NickoScope32's ADD-76, where on-device
   Telegram cost ~42 KB of heap and was removed.
2. **All three features are one protocol, TTY/1.** A mail or a WhatsApp message
   is just a telegram from a node called `MAIL` or `WA`. A reply is a telegram
   back to that node. One module on the panel (`src/tty/`) and one inbox cover
   all three.
3. **Nobody has built this as a whole.** The pieces exist, and we take them from
   the best places (§6):
   - the frame and dedup: Meshtastic;
   - the signed broadcast and app-level ACK: EspNowBus;
   - store-and-forward: LXMF;
   - the "printed N characters" receipt and the ZCZC/NNNN look: i-Telex / piTelex;
   - the display hints: AWTRIX.
4. **Transports:**
   - inside a house: ESP-NOW broadcast on the router's channel. This is proven on
     our exact SDK in NickoScope32; see [26](26-mtr1-direct-link.md).
   - between houses: the Mosquitto brokers bridged over TLS, so the panels never
     do TLS themselves.
   - LoRa or Meshtastic, only as a later bridge.
5. **Mail can start today with zero firmware.** A Home Assistant automation
   publishes to the existing `nickoscope_matrix/notify` overlay. The draft is
   [configs/ha/mail_to_panel.yaml](../configs/ha/mail_to_panel.yaml).

## 1. What the firmware already gives us (integration map)

Read from `NickoScope/AnimatedPixelClock` main at `dc160af`.

| Piece | Where | What matters here |
|---|---|---|
| MQTT bus | `src/mqtt/mqtt_bus.{h,cpp}` | Prefix handlers, first match wins (`mqtt_bus.h:25-55`); `MQTT_BASE "nickoscope_matrix"`; incoming buffer **2048 B**, larger messages dropped silently (`mqtt_bus.cpp:34`); plain `WiFiClient`. **`MQTT_MAX_SUBS 10` with 9 used, and `MQTT_MAX_HANDLERS 10` with 8 used** (`:46-56`). An eleventh subscription is refused silently (the class of bug in [16](16-presence-radar.md) §"The ninth subscription") |
| Banner notify | `src/notify/`, `POST /api/notify` (`web.cpp:314,716-782`) | text ≤200 B, scrolls at 40 px/s, a built-in 8x8 **mail** icon, Cyrillic OK, **no hold**; dismissed by IR `dismiss` and `/api/notify/dismiss` |
| Card notify | `src/cards/`, `nickoscope_matrix/notify` | title ≤22 B, text ≤**64 B**, 2 lines, **no scroll, no queue** (a new one overwrites); `hold` + "PRESS"; the first knob press dismisses it (`main.cpp:1097-1102`) |
| Fonts | `src/fonts/sys_text.h`, `picopixel_fb.h` | ASCII, Latin-1, Cyrillic U+0400..045F. **Anything else, emoji included, draws as the MISSING box**, so bridges must strip emoji |
| Net broker | `src/net/net_broker.{h,cpp}` | GET only, one TLS client per request, destroyed after; callers are a fixed enum. Not an IMAP or SMTP path |
| Input | `control/control.h:40-44`, `ir/ir_actions.cpp` | `CTRL_CW/CCW/PRESS/LONG`; IR OK = the same switch; per-page click handlers |
| Pages | `main.cpp:94-132`, cards after `PAGE_COUNT` | a new `PAGE_TTY` behind its flag |
| Secrets | NVS per module; `provision_secrets.example.ini` → `pio run -e provision` | where a TTY family key goes |
| ESP-NOW, UDP multicast | none | ESP-NOW is new to this firmware |
| Internal heap | [32](32-net-broker.md) | ~21.5-23.3 KB free with the broker; largest block ~12-14 KB |

Two small inconsistencies turned up. They are worth fixing when this lands, not
before:
- IR `dismiss` and `/api/notify/dismiss` clear the banner but **not** the card
  overlay.
- The card overlay has no queue, so a burst of messages shows only the last one.

## 2. Mail

### Findings

- **On-device IMAP is possible and a bad trade.** The live library is
  [mobizt/ReadyMail](https://github.com/mobizt/ReadyMail) (v0.4.2, 2026-09). It
  is the successor of ESP-Mail-Client, which its README now marks DEPRECATED.
  - It has IDLE and XOAUTH2, but only with a ready-made token.
  - Its **licence is CC BY-NC 4.0**, which does not sit with our MIT fork.
  - Its README lists STARTTLS hanging on ESP32 core 3.x.
- **IDLE is the real cost.** It is a TLS session held for hours, and it would
  take over the net broker's one outbound session. mbedTLS alone is ~22-42 KB
  ([IDF table](https://github.com/espressif/esp-idf/blob/release/v5.5/docs/en/api-reference/protocols/mbedtls.rst)).
  `tlsUsePsram()` moves that into PSRAM, but the socket, lwIP buffers and the
  task stack stay internal.
- **iCloud (the owner's @me.com).**
  - IMAP: `imap.mail.me.com:993`; SMTP: `smtp.mail.me.com:587` STARTTLS.
  - An app-specific password is required; there is no POP
    ([Apple 102525](https://support.apple.com/en-us/102525)).
  - Whether iCloud offers IDLE is contested. It seems to advertise IDLE only
    after LOGIN ([Mozilla 1611624](https://bugzilla.mozilla.org/show_bug.cgi?id=1611624)).
    So Home Assistant may fall back to polling every 10 s. Either is fine for a
    wall panel. **Not verified**: port 993 was closed from the research sandbox.
- **Gmail** needs an app password or OAuth; basic sign-in went on 2025-03-14.
  **Outlook.com** is OAuth only, and Home Assistant's IMAP cannot do OAuth.
  **Yandex and Mail.ru** use app passwords.
- **Home Assistant's core `imap` integration**
  ([code](https://github.com/home-assistant/core/tree/dev/homeassistant/components/imap)):
  - an unread sensor;
  - the `imap_content` event with `sender`, `subject`, `date`, `uid`,
    `initial`, and `text` if enabled;
  - services `imap.seen`, `move`, `delete`, `fetch`.
  - **Catch:** it raises an event for the newest UID only, so a burst of mail
    gives one event. The sensor holds the true count.
- **Prior art.** No mature "mail on an LED matrix" project exists. Every working
  setup has a server read the mail and the display only show it. The AWTRIX
  `notify` + `indicator` UX is the one to copy.

### Design

```
iCloud IMAP ──► Home Assistant imap ──► automation ──► MQTT ──► panel
                 (app password,          strips HTML,           notify overlay now,
                  verify_ssl on)         emoji, trims           TTY inbox later
                                    ◄── imap.seen / imap.move ◄── panel command
                 HA smtp (587) ◄─────── canned reply ◄─────────── knob / IR
```

- **Stage 0 (now, no firmware).** `imap_content` with `initial: true` publishes
  to `nickoscope_matrix/notify`: sender and subject, trimmed to fit 64 B. A
  retained card `nickoscope_matrix/card/mail` shows the unread count. Draft:
  [configs/ha/mail_to_panel.yaml](../configs/ha/mail_to_panel.yaml).
- **Stage 1.** The same automation publishes a TTY/1 message from node `MAIL`
  (§4). The panel files it in the inbox. The knob offers `seen` / `archive` /
  a canned reply, which comes back as a TTY/1 message to `MAIL`; HA maps it to
  `imap.seen`, `imap.move` or `smtp`.
- **Fallback A (HA's IMAP misbehaves with iCloud).** A ~150-line Python IDLE
  daemon, or [goimapnotify](https://github.com/shackra/goimapnotify) plus
  `mosquitto_pub`. It re-asks CAPABILITY after LOGIN and publishes the same
  messages.
- **Fallback B (the panel must work without HA).** A poll every 3-5 min through
  the net broker:
  - `LOGIN`, `STATUS INBOX (UNSEEN UIDNEXT)`, `UID FETCH new (ENVELOPE)`,
    `LOGOUT`;
  - a short session, closed before the result is published;
  - no IDLE, no sending.
  - Our own ~300 lines, not ReadyMail (its licence). Only if the owner asks.
- **Privacy.** The panel hangs on a wall. By default, the preview shows sender
  and subject only, no body. A body preview is an owner's switch in HA, not a
  firmware default. Preview topics are **not retained**, so a subject does not
  live on the broker for ever.

## 3. WhatsApp

### Findings

- **There is no official way to read personal or family chats.**
  - The WhatsApp Business Cloud API reads only a separate business number.
    Family would have to write to "the Panel", and a group chat is not readable.
    It also needs a public HTTPS webhook.
  - From 2026-10-01, service messages are charged after 1,000 a month
    ([engagelab](https://www.engagelab.com/blog/whatsapp-pricing-2026-service-message-cost)).
- **Every route that receives personal or group messages is one of two kinds:**
  - **(A) an unofficial linked device** (whatsmeow, Baileys, whatsapp-web.js,
    and the services built on them: WAHA, GOWA, Evolution, Green-API, Whapi).
    This is against the ToS
    ([EEA terms](https://www.whatsapp.com/legal/terms-of-service-eea)), and
    there have been ban waves: [whatsmeow#810](https://github.com/tulir/whatsmeow/issues/810),
    [Baileys#1869](https://github.com/WhiskeySockets/Baileys/issues/1869).
  - **(B) the official app's notifications on an Android phone**, read by the
    HA Companion `last_notification` sensor with an allow-list for
    `com.whatsapp` ([docs](https://github.com/home-assistant/companion.home-assistant/blob/master/docs/core/sensors.md)).
- **CallMeBot only sends to yourself.** Nearly every "ESP32 WhatsApp" tutorial is
  that.
- **A real E2E WhatsApp client on an ESP32-S3 exists:**
  [oxidezap/whatsapp-rust-esp32](https://github.com/oxidezap/whatsapp-rust-esp32)
  (MIT, 2026-09). It proves feasibility and rules itself out for us:
  - ESP-IDF 5.5 + Rust, not Arduino;
  - a 4.2 MB app;
  - a 256 KB PSRAM executor stack;
  - prekeys cut to 50 because 812 X25519 keys "exhaust internal DRAM";
  - a permanent TLS websocket;
  - the same ban risk.
  - At most a separate coprocessor board, as an experiment.
- **No project shows incoming WhatsApp on an LED matrix.** AWTRIX and LaMetric
  do it only indirectly, through HA notifications.

### Design

- **Primary.** A bridge on the RPi5 in Docker, linked to a **second number** (a
  cheap French prepaid SIM) that is a member of the family group. Never the
  owner's personal number: a ban then costs only the spare SIM.
  - Bridge: [GOWA](https://github.com/aldinokemal/go-whatsapp-web-multidevice)
    (whatsmeow, ARM binary, webhook with a group filter) or
    [WAHA](https://github.com/devlikeapro/waha) with the GOWS engine (the
    `gows-arm` image; every former Plus feature is free since 2026.6.1).
  - A small adapter (Python or Node-RED) turns the webhook into TTY/1 messages
    from node `WA`. It publishes only allow-listed chats, strips emoji and trims
    text.
  - A reply from the panel is a TTY/1 message to `WA` with `ref` = the
    original's id. The adapter maps it to the chat, adds a 5-10 s delay and
    sends.
  - The MQTT topic shape follows
    [sidey79/whatsmeow-mqtt-bridge](https://github.com/sidey79/whatsmeow-mqtt-bridge):
    command envelope, retained status, LWT. That bridge ignores groups in v1.
  - A one-click HA alternative:
    [FaserF/ha-whatsapp](https://github.com/FaserF/ha-whatsapp) and its add-on
    (Baileys, the `whatsapp_message_received` event).
- **Fallback with no ban risk.** An old Android phone runs the **official**
  WhatsApp on the second number, with HA Companion reading `last_notification`.
  - Replies go through the notification's direct-reply action, via Tasker +
    AutoNotification.
  - Receive only, if Tasker is not wanted.
- **The honest alternative.** A Telegram bot in the family group: an official
  free API with no ToS problem. The owner already runs one through HA
  (NickoScope32-TG-HA). It costs the family moving chats.
- **Owner's decision needed:** second SIM + GOWA, Android notifications, or
  Telegram (§8).

## 4. The teletype network: TTY/1

### What exists (and what does not)

**Nobody has built a teletype network of ESP32 displays with one protocol over
several transports, with addressing and receipts.** The closest matches:

| Project | What it is | What it lacks |
|---|---|---|
| [jcdietrich/green-terminal](https://github.com/jcdietrich/green-terminal) | Waveshare ESP32-S3 LCD "typewriter-style green-CRT message terminal": types messages out, queue, alert, sticky | one device, no network |
| AWTRIX 3 `clients` ([api.md](https://github.com/Blueforcer/awtrix3/blob/main/docs/api.md)) | "Forward to other AWTRIX devices" | copies only, no addressing or receipts |
| Cornell ECE5725 "LED Matrix Messenger" ([page](https://courses.ece.cornell.edu/ece5990/ECE5725_Spring2020_Projects/May_19_Demo/LED%20Matrix%20Messages/W_dms486_ov37-1/index.html)) | two matrices in two houses over MQTT | Raspberry Pi, a student demo |
| [EvilChatMesh](https://github.com/7h30th3r0n3/Evil-M5Project/wiki/EvilChatMesh) | IRC-like chat over ESP-NOW on M5 Cardputer: CRC16 dedup, presence, relays | one device type, no security |
| [Marusko/ESP-NOW-LoRa-Messenger](https://github.com/Marusko/ESP-NOW-LoRa-Messenger) | ESP-NOW locally, LoRa backbone, end-to-end ACK | the nearest architecture, a 2026 hobby repo |
| [nepamesh/led-mqtt-meshtastic-8x32](https://github.com/nepamesh/led-mqtt-meshtastic-8x32) | ESP32 decodes Meshtastic from MQTT and scrolls it on an 8x32 matrix | a receiver only |
| [piTelex](https://github.com/fablab-wue/piTelex) / [MicroTelex](https://github.com/fablab-wue/MicroTelex) | the real i-Telex network: TLV packets, an Ack counting **printed characters**, the TNS directory | teleprinters, Baudot |

The stacks weighed and rejected as the base:
- **Meshtastic, MeshCore:** a whole firmware on LoRa. They are good for a bridge
  node, not for the panel.
- **Reticulum/LXMF:** the right ideas, but microReticulum has no LXMF yet, and it
  is heavy.
- **painlessMesh:** runs its own SSID mesh, which fights STA to the home router.
- **ESP-Mesh-Lite:** an IP mesh, far more than needed.
- **Tailscale and WireGuard on the panel:** microlink needs 85-116 KB of static
  SRAM.

### Principles

- **One envelope, any transport.** A transport only carries bytes.
- **Any ESP32 can be a client with no library beyond a ~300-line header.** That
  means a fixed binary header, TLV fields and HMAC-SHA256, which is in mbedTLS
  and in hardware on the S3. No CBOR, protobuf or new crypto library in phase 1.
- **The whole telegram fits one ESP-NOW v1 frame (250 B).** Every M5 on an old
  core can take part. v2's 1470 B waits until every device is on IDF ≥ 5.4.
- **A mirror in JSON on MQTT**, so HA, the bridges and Node-RED speak it without
  the binary codec. This is Meshtastic's `/e/` and `/json/` split.

### The binary frame (ESP-NOW, and the signed form everywhere)

```
off len field  meaning
 0   2  magic  'T' '1'          (NSP frames start 0xA5, so one ESP-NOW callback
                                 can tell the two apart by the first byte)
 2   1  type   MSG 1, ACK 2, WRU 3 ("who are you"), ANS 4 (answerback),
               SYNC 5, CANCEL 6
 3   1  flags  bit0 want-ACK, bit1-2 prio (info/warn/crit), bit3 to-is-channel,
               bit4 hold, bit5 via-MQTT, bit6 via-ESP-NOW
 4   1  hop    hops left, start 2. NOT signed, so a relay can decrement it
 5   4  from   node id (first 4 B of SHA-256 of the MAC in phase 1)
 9   4  to     node id | channel hash (flag bit3) | 0xFFFFFFFF = all
13   4  id     sender's counter; NVS stores it +1000 at boot. (from,id) is the
               dedup key
17   4  ts     unix time from NTP, 0 when unknown
21   4  ref    ACK / reply: the id being answered; 0 otherwise
25   1  st     ACK only: RCVD 1, SHOWN 2 (typed out on screen), READ 3 (pressed)
26   1  tlen   length of the TLV block
27   n  TLVs   type(1) len(1) value
               01 text (UTF-8)   02 callsign "NK-KUX"   03 sender name
               04 title          05 colour RGB565       06 fx ("tty", "plain")
               07 ttl seconds    08 canned replies ("Да|Нет|Позвоню")
               09 source ("mail", "wa", "tty")
27+n 16 tag    HMAC-SHA256(family key, bytes 0..26+n with hop zeroed),
               truncated to 16 B
```

- **Size.** Header 27 + tag 16 = 43 B, which leaves **207 B for TLVs**: about 90
  Cyrillic characters of text with a callsign and a title.
  - A longer text is split into parts linked by `ref`, the way NickoScope32's
    `ORACLE_STREAM_START/TEXT/END` does it.
  - For a wall panel, ~90 characters is a telegram, which is the point.
- **Dedup.** A ring of 64 × (from, id), 512 B *estimate* of internal RAM. A
  frame already seen is dropped before its TLVs are parsed.
- **Replay.** A per-sender sliding window of 64 ids, as in
  [EspNowBus SPEC.md](https://github.com/tanakamasayuki/EspNowBus/blob/deed6cc1dd1dcdd018e5f732a7751d21f7afd581/SPEC.md).
  When time is synced, frames with |ts − now| over 10 min are also refused.
- **Why HMAC and not ESP-NOW's own encryption.** CCMP covers unicast only,
  broadcast is never encrypted, and it is limited to 17 peers
  ([IDF](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/network/esp_now.html)).
  Also, unicast receive with STA connected is unconfirmed on arduino-esp32 2.x
  ([26](26-mtr1-direct-link.md) §4). So phase 1 is **signed broadcast**:
  anyone in radio range can read a telegram, nobody can forge one.
  - Phase 2 adds AES-CCM on the text (nonce = from‖id) if the family wants
    privacy on the air.
  - Phase 3 moves to per-device Ed25519 via
    [Monocypher](https://github.com/LoupVaillant/Monocypher), because mbedTLS
    has no Ed25519.

### The JSON mirror (MQTT)

```json
{"v":1,"t":"msg","fr":"9f3a01c2","cs":"NK-KUX","to":"*","id":4211,"ts":1790000000,
 "text":"Ужин в 8","title":"Кухня","name":"Мама","prio":"info","fx":"tty",
 "reply":["Иду","Позже"],"src":"tty","want_ack":true}
```

Topics. These are outside `nickoscope_matrix/`, because the network is not one
panel's:

| Topic | Retained | Carries |
|---|---|---|
| `tty/1/in/<node>` | no | messages to one node |
| `tty/1/ch/<channel>` | no | messages to a channel (`family`, `house-kux`) or all (`*`) |
| `tty/1/ack/<node>` | no | receipts back to the sender |
| `tty/1/dir/<node>` | **yes** | the node's answerback: callsign, screen cols/rows/colour, has-input, transports, key id |
| `tty/1/st/<node>` | **yes**, LWT | `online` / `offline`, as in Homie's `$state` |
| `tty/1/raw/...` | no | the signed binary frame, for bridges between houses |

- **Trust on the local broker.** JSON on the house broker is trusted through
  Mosquitto's user/ACL, the way every other panel topic is today. Only the raw
  signed form crosses a house boundary or goes on the air. The gateway converts
  and signs.
- **Two subscriptions on the panel.**
  - `tty/1/in/<me>` and `tty/1/ch/#` need two slots, and only one is free. So
    **`MQTT_MAX_SUBS` goes 10 → 12**, about 200 B of `.bss`, as the presence
    radar's did.
  - Handlers: one prefix `tty/1/`.

### Transports

- **Inside a house: ESP-NOW broadcast on the AP's channel.**
  - Copy NickoScope32 Main-S3's handling (`main.cpp:2676-2860`):
    - one broadcast peer, `ifidx = WIFI_IF_STA`;
    - `WiFi.setSleep(false)`;
    - a channel check every 2 s, with `esp_now_deinit` and init when the router
      moves;
    - de-init before and re-init after our `netRecover`, which calls
      `WiFi.disconnect(true)` (the ~15 s of dead radio recorded in NickoScope32).
  - The receive callback runs on the Wi-Fi task. It only copies the frame into a
    PSRAM ring and returns; parsing, dedup and HMAC run on the loop task.
  - Devices with no router (M5Dial, Atom Echo, watches) learn the channel from
    the hub's ANS beacon, or scan for it.
- **Gateway ESP-NOW ↔ MQTT.**
  - Where: the NickoScope32 Main-S3 hub (already an ESP-NOW hub with MQTT) and/or
    any panel.
  - It dedups by (from, id) and sets the via bits, so a frame never loops back.
- **Between houses: Mosquitto bridges.**
  - Each house's broker runs `topic tty/1/# both 1` over TLS 8883, either to the
    other house or to a neutral cloud broker (no port forwarding then).
  - The panels never do TLS.
  - **ntfy** is the fallback: `?poll=1&since=` gives catch-up for free; the body
    must be encrypted.
- **Later, optional: LoRa.** A Meshtastic node on the gateway carries the raw
  frame in `PRIVATE_APP = 256`. A frame of ≤250 B fits Meshtastic's ~237 B
  payload only with a trimmed text, so it is phase 4.

### Receipts: three levels, the telegraph's

1. The link: ESP-NOW MAC-ACK or MQTT PUBACK. This says nothing about the
   application; Espressif itself says to add your own ACK.
2. `ACK st=RCVD` from the addressee.
3. `ACK st=SHOWN` once the text has been typed out on screen (i-Telex's "printed
   N characters"), then `ACK st=READ` on a knob or OK press. The sender shows
   "✓ ДОСТАВЛЕНО" / "✓ ПРОЧИТАНО".

### Store and forward: the post office (ПОЧТАМТ)

- A small service on HA or the RPi5 (Python, ~200 lines *estimate*):
  - It keeps undelivered messages until ACK or `ttl`, and retries with backoff.
  - It answers `SYNC since=<id>` from a node that has just booted. This is LXMF's
    propagation node and ntfy's `since=`.
- Retained MQTT is used for the directory and status only, **never for mail**.
- The panel's own inbox: a ring of 32 messages in **PSRAM**, lost on reboot; the
  post office refills it with SYNC.

### On the panel: the TTY page

- `src/tty/` behind `-DTTY_ENABLED`, needing `MQTT_BUS_ENABLED`. The ESP-NOW
  transport goes behind `-DTTY_ESPNOW_ENABLED`, so the MQTT-only build carries no
  radio change.
- **A new message** raises the card overlay, with `hold` for `prio=crit`.
  - Its first lines are typed out character by character.
  - The header is NAVTEX/telex style:

    ```
    ZCZC NR0042 NK-GAR→NK-KUX 271530Z
    УЖИН В 8
    NNNN
    ```
- **The TTY page** is the inbox.
  - The knob scrolls, a press opens a message, and a long press offers the
    canned replies from the `reply` TLV.
  - The sender, `MAIL`, `WA` or another panel, is irrelevant to the page.
- **Optional MTK-2 mode:** capitals only, trimmed to the Baudot set from
  piTelex's tables, for the look.
- **Lua:** a later `tty.send(to, text)` / `tty.last()` pair, so games and effects
  can send telegrams. Not in phase 1.
- **Host tests:** `tools/tty/check_tty.py` covers:
  - frame encode and decode;
  - the TLV bounds;
  - HMAC vectors;
  - dedup and the replay window;
  - hop decrement not breaking the tag;
  - JSON ↔ frame round trip.
- **The shared library.** The codec and the HMAC are one header, `tty1.h`,
  Arduino-free, with the same host vectors. It is the "any ESP32 is a client"
  promise; it is also what NickoScope32's Main-S3, the M5Dial and the StickS3
  include.

## 5. Budget (estimates until measured on the panel)

| Item | Internal RAM | PSRAM | Flash |
|---|---|---|---|
| Two more MQTT subscriptions | ~200 B | - | - |
| Dedup ring + replay windows (16 senders) | ~1 KB | - | - |
| ESP-NOW (driver, one peer, callback) | a few KB *estimate*; ESP-NOW adds no static Wi-Fi buffers ([26](26-mtr1-direct-link.md) §4) | - | ~10 KB *estimate* |
| Inbox, 32 × 256 B | - | 8 KB | - |
| RX ring from the Wi-Fi task, 8 × 250 B | - | 2 KB | - |
| tty module + page + codec | - | - | ~15-20 KB *estimate* |
| **Mail, WhatsApp** | **0**: they arrive as MQTT JSON | - | - |

Measure the ESP-NOW line at bring-up against [32](32-net-broker.md)'s floor:
free internal heap, the minimum, and the largest block, before and after, on the
panel.

## 6. Reference shortlist: what to take from each

| Repo | Take |
|---|---|
| [tanakamasayuki/EspNowBus](https://github.com/tanakamasayuki/EspNowBus) (SPEC.md) | HMAC-signed broadcast, replay window, app ACK over MAC ACK, heartbeat |
| [meshtastic/firmware](https://github.com/meshtastic/firmware) + [protobufs](https://github.com/meshtastic/protobufs) | the compact header, (from, packetId) dedup, hop limit, the via-MQTT flag, `/e/` vs `/json/` topics, port numbers |
| [markqvist/LXMF](https://github.com/markqvist/LXMF) | extensible fields, propagation nodes for store and forward, identity-hash addressing (phase 3) |
| [fablab-wue/piTelex](https://github.com/fablab-wue/piTelex) | TLV framing, Ack by printed characters, the directory idea, Baudot tables for the MTK-2 look |
| [Blueforcer/awtrix3 api.md](https://github.com/Blueforcer/awtrix3/blob/main/docs/api.md) → [awtrix-ng](https://github.com/Blueforcer/awtrix-ng) | display hints, `hold`/`dismiss`, `indicator` for "unread", `clients` forwarding |
| [espressif/esp-now](https://github.com/espressif/esp-now), [aZholtikov/zh_network](https://github.com/aZholtikov/zh_network) | ESP-NOW relay with TTL, the "magic" dedup cache, retry backoff, coexistence with STA |
| [gmag11/EnigmaIOT](https://github.com/gmag11/EnigmaIOT) | ChaCha20-Poly1305 over ESP-NOW with counters and an MQTT gateway (phase 2) |
| [jcdietrich/green-terminal](https://github.com/jcdietrich/green-terminal) | the typing-out UX: queue, sticky, fade |
| [home-assistant/core imap](https://github.com/home-assistant/core/tree/dev/homeassistant/components/imap) | the mail event contract; the newest-UID-only catch |
| [aldinokemal/go-whatsapp-web-multidevice](https://github.com/aldinokemal/go-whatsapp-web-multidevice), [devlikeapro/waha](https://github.com/devlikeapro/waha) | the WhatsApp bridge |
| [sidey79/whatsmeow-mqtt-bridge](https://github.com/sidey79/whatsmeow-mqtt-bridge) | a WhatsApp ↔ MQTT topic and envelope shape, LWT |
| [oxidezap/whatsapp-rust-esp32](https://github.com/oxidezap/whatsapp-rust-esp32) | the numbers that show why WhatsApp does not belong inside the panel |

## 7. Order of work

| # | Step | Where | Gate |
|---|---|---|---|
| 0 | **Mail on the existing overlay**: HA IMAP (iCloud, app password) + the automation in `configs/ha/mail_to_panel.yaml` | HA only | the owner sees a new mail's sender and subject on the panel |
| 1 | `tty1.h` codec + `tools/tty/check_tty.py` vectors | fork `feat/tty` | host tests green; no firmware change yet |
| 2 | `src/tty/` over MQTT only: inbox, TTY page, typing effect, ACKs, canned replies; `MQTT_MAX_SUBS` 12 | fork `feat/tty` | flag matrix, gate audit, then the panel |
| 3 | Mail bridge moves to TTY/1 (node `MAIL`), with seen/archive/reply | HA | reply lands in the mailbox |
| 4 | WhatsApp bridge, after the owner's choice in §8 (node `WA`) | RPi5 / HA | family-group message on the panel; canned reply arrives in the group |
| 5 | Post office (SYNC, retries) | RPi5 / HA | panel reboot loses nothing |
| 6 | ESP-NOW transport (`TTY_ESPNOW_ENABLED`) + gateway on the NickoScope32 Main-S3 hub | fork + NikoScope32 | heap measured; panel ↔ M5Dial telegram with the router's channel moved once |
| 7 | Between houses: Mosquitto bridge | brokers | a telegram crosses houses; a panel offline for an hour catches up |
| 8 | Later: encryption (phase 2), Ed25519 (phase 3), Meshtastic bridge, Lua `tty.*` | - | on the owner's word |

Step 6 touches NickoScope32 as well. Before code there it goes through that
project's ADD process; the pointer is in NikoScope32's
`NickoScope32 BringUpToLife v1.b/docs/TTY1-teletype-network.md`.

## 8. Questions for the owner

1. **WhatsApp route:**
   - (a) a second SIM + GOWA/WAHA on the RPi5 (reads the family group, replies
     as "Панель", ban risk on the spare SIM only);
   - (b) an old Android phone with the official app + HA Companion (no ban risk,
     replies through Tasker);
   - (c) a Telegram bot instead.
2. **Mail:**
   - Only iCloud @me.com, or other boxes too?
   - Sender + subject only on the wall, or a body preview?
3. **The network's members.** Which panels and devices, in which houses? That
   decides whether step 7 is needed at all, and each device's callsign.
4. **A family key for phase 1** (signed, readable on air), or encryption from
   the start (phase 2 folded into step 6)?
5. **Stage 0 now?** It needs an app-specific password for iCloud entered into
   HA's IMAP integration, by the owner, not by an agent.
