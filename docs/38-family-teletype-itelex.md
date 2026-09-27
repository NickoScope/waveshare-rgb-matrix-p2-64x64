# 38. The family teletype: i-Telex over one tailnet

Decided with the owner on 2026-09-27, in three steps:

> «Идея, все панели сети/семьи посадить в одной сети через тайлскейл, и сделать
> мессенджер между ними. Отправлять с телефона на адрес панели.»
>
> «А через i-telex эмулировать телетайп?»
>
> «Делай так, но в прошивку пока не интегрируй, пиши отдельным модулем p&p.»

An earlier draft (mail, WhatsApp, a protocol of our own) was rejected the same
day. It is kept in
[drafts/38-mail-whatsapp-tty1-rejected-2026-09-27.md](drafts/38-mail-whatsapp-tty1-rejected-2026-09-27.md)
for its research.

**State:** the library is written. It is moving to its own repository,
**NickoScope-Telex**, on the owner's word of 2026-09-27; until that repository
exists, the copy is in [`modules/itelex/`](../modules/itelex/).
- It passes host tests (97/97).
- It is **compatible with i-Telex as piTelex implements it**: 12/12 interop
  checks in both directions against piTelex's own i-Telex code, over TCP, three
  runs in a row.
- It compiles for the ESP32-S3 against the panel's exact core.
- **It is not in the firmware, not flashed, and not tried with a real
  teleprinter.**

## The design in one picture

```
 house A (LAN 192.168.1.0/24)                 house B (LAN 192.168.2.0/24)
 ┌──────────────────────────────┐             ┌──────────────────────────────┐
 │ panel 10001 :134  i-Telex    │             │ panel 10003 :134  i-Telex    │
 │ panel 10002 :134  i-Telex    │             │                              │
 │ HA / RPi5: Tailscale         │◄── tailnet ─►│ HA / RPi5: Tailscale         │
 │   subnet router 192.168.1/24 │  WireGuard  │   subnet router 192.168.2/24 │
 └──────────────────────────────┘             └──────────────────────────────┘
          ▲                                               ▲
          └──────────── phone with the Tailscale app ─────┘
                   telnet app → 192.168.1.57:134 → types
```

- **The network is Tailscale, but not on the panels.** In each house, Home
  Assistant or an RPi5 runs Tailscale as a *subnet router*. It advertises the
  house LAN, so every phone and laptop of the family on the tailnet reaches
  every panel at its LAN address.
- **The messenger is i-Telex.** Each panel is a station with a number:
  - it answers calls on port 134;
  - it prints what arrives letter by letter;
  - it answers "КТО ТАМ?" (WRU) with its answerback;
  - its Acknowledge tells the sender how much is already on screen: the
    telegraph's receipt.
- **From a phone:** a telnet/TCP terminal app to `<panel>:134`, then type. The
  station tells an i-Telex caller from a plain ASCII one by the first bytes, as
  piTelex does. A plain ASCII call carries UTF-8 here, so Russian arrives as is.
- **Panel to panel:** by number, through a phonebook in the firmware
  configuration. Across houses see §5; it is the one part that needs a
  decision.

## 1. Why not Tailscale on the panel itself

Checked 2026-09-27 against the source of the only Tailscale client for ESP32,
[CamM2325/microlink](https://github.com/CamM2325/microlink) at `216da33`, and
against the panel's SDK. Espressif has nothing official: no repository, file or
issue about Tailscale in `espressif/*`. The only registry entry is a fork,
`fugo101/microlink` (ESP-IDF 6 only).

| | microlink needs | the panel has |
|---|---|---|
| ESP-IDF | ≥ 5.0; the component depends on `esp_driver_tsens` (≥ 5.3) | 4.4.7 (arduino-esp32 2.0.17, `platform = espressif32@6.12.0`) |
| ChaCha20-Poly1305 in mbedTLS | yes (`ml_noise.c`) | off in the 2.0.17 sdkconfig |
| Task stacks | 12 + 14 + 8 + 8 = 42 KB, internal (IDF 4.4 cannot put stacks in PSRAM) | 21-34 KB free internal, largest block 12-14 KB ([32](32-net-broker.md)) |
| TLS for DERP | a standing session, ~2 × 16.5 KB internal on this SDK | none to spare |

Also:
- a TCP crash under load, [#17](https://github.com/CamM2325/microlink/issues/17)
  (fix unmerged);
- DERP certificates not verified;
- the preferred DERP region hard-coded to Dallas;
- no Headscale in the code despite the README;
- 17 open PRs, no maintainer activity since 2026-03.

Worth reopening only if the firmware moves to arduino-esp32 3.x and frees
60-80 KB of internal RAM.

The subnet router costs the panel **nothing**. It is in Tailscale's free
Personal plan (up to 6 users), and devices behind it do not count as tailnet
devices ([kb/1019](https://tailscale.com/kb/1019/subnets)).

## 2. Why i-Telex

i-Telex is the amateur telex network over the internet, running since 2000
([i-telex.net](https://www.i-telex.net/)). Its protocol is documented: the
*i-Telex Communication Specification*, telexforum.de lexicon entry 74. Its
reference implementation in Python is
[piTelex](https://github.com/fablab-wue/piTelex) (GPL-3).

- **Light.** Plain TCP, packets `[type][len][data]`, no TLS. The module costs
  one socket and ~1.2 KB of session state.
- **A telegraph, not a chat.** It has:
  - numbers and a subscriber server (TNS, port 11811);
  - the answerback (WRU);
  - the Acknowledge counting printed characters;
  - Baudot at the wire, 5 bits a character.

  The owner asked for exactly this look.
- **NAT solved already, if ever needed.** *Centralex* (`tlnserv2.teleprinter.net:49491`)
  holds an outbound line from the station and puts incoming calls through it.
  No public IPv4 and no port forwarding
  ([piTelex wiki](https://github.com/fablab-wue/piTelex/wiki/SW_DevITelexCentralex)).
- **Any ESP32 can join.** The protocol core has no Arduino in it. The
  NickoScope32 Main-S3, an M5 device or a new board takes the same library.

## 3. The public i-Telex network: not yet, and not without asking

- Numbers are given out by the i-Telex administrators.
- The author of WinTlx writes: *"Participation in the i-Telex network requires
  at least one real teleprinter. Participation only with WinTlx is not
  possible."* ([WinTlx README](https://github.com/detlefgerhardt/WinTlx))
- An LED panel alone is therefore unlikely to get a number. Ask on
  telexforum.de before any public use. Centralex also needs a number registered
  as "dynamic IP", with its PIN.
- **The family network does not need any of that.** It uses its own phonebook
  and the tailnet. The module's TNS lookup and Centralex are switched off by
  default. They are there so that the day a number is granted, joining the
  public network is configuration, not code.

## 4. The module: `modules/itelex/`

A PlatformIO/Arduino library, MIT, written from the specification. The owner
asked for it as its own repository, "NickoScope-Telex", and for i-Telex
compatibility («мы должны быть совместимы с iTelex»). piTelex was
read as a reference and used as a **test oracle** (its encoder produced the
Baudot vectors); none of its GPL code is copied. Details, API and limits are in
[modules/itelex/README.md](../modules/itelex/README.md).

| File | What | Arduino? |
|---|---|---|
| `itx_baudot.*` | ITA2 and MTK-2 (Russian) with the bit-reversed wire order; UTF-8 in and out; transliteration for plain ITA2 peers | no |
| `itx_packet.*` | every station, Centralex and TNS packet; a streaming parser that tells packets from ASCII and skips telnet negotiation | no |
| `itx_session.*` | one call: detect binary/ASCII, decode, answer WRU, Acknowledge by what was *shown*, flow control by the peer's Acknowledge, End/Reject/timeouts | no |
| `ITelex.*` | `itx::Station`: listen on :134, one call at a time ("occ" to a second caller), dial by phonebook/TNS/host:port, the Centralex line | yes |
| `examples/SerialTeletype` | the smallest station: the serial monitor is the teleprinter | yes |
| `test/run_host_tests.sh` | 97 checks under ASan/UBSan, incl. two sessions wired back to back | no |
| `test/interop/` | a live i-Telex call against **piTelex's own code** in both directions: text, WRU and answerback, hang-up | no |

**Which code is on the line.**
- The i-Telex network is **ITA2**: piTelex builds its line codec with the ITA2
  table.
- MTK-2 would turn Russian into Latin garbage at a piTelex station. So the
  station speaks ITA2 by default and transliterates Russian.
- Two of our stations recognise each other by the software id in the Version
  packet (ours starts with `nk`) and switch the line to **MTK-2**, where
  Cyrillic passes.
- A caller waits up to 3 s for the peer's Version before it sends text.
- Tested both ways in `testCodingByPeer`.

**An ASCII-only port** (optional): see [modules/itelex/docs/MINITEL.md](../modules/itelex/docs/MINITEL.md).

**Verified:**
- host tests PASS (97/97);
- interop with piTelex PASS (12/12, both directions, 3 runs).
- The module and the example **compile** for the ESP32-S3 with no warnings:
  - xtensa-esp32s3-elf-gcc 8.4.0 (esp-2021r2-patch5);
  - the headers of arduino-esp32 2.0.17 / IDF 4.4.7;
  - the core's own `platform.txt` flags (`-std=gnu++11`), plus `-Wall -Wextra`.
- `pio run` could not be used in the session that wrote this, because the
  PlatformIO registry was blocked by its network policy. So the example has been
  compiled, **not linked**.
- Code: ~10.7 KB of flash (`.text` of the four objects). `sizeof(itx::Session)`
  is 1,196 B; `sizeof(itx::Station)` is 1,716 B, the session included. lwIP's
  socket buffers come on top and are not measured.

**Not verified:**
- a call with a real teleprinter on the public network;
- Centralex and the TNS against the live servers;
- anything on the panel.

## 5. Across houses: the one open decision

A phone reaches every panel through the subnet routers. A **panel** calling a
panel in the other house is harder: its gateway is the home router, which knows
nothing of the other LAN. Three ways, from Tailscale's docs and the HA add-on's
(`hassio-addons/addon-tailscale` DOCS.md):

1. **Renumber so the LANs differ** (192.168.1.x and 192.168.2.x). Add a static
   route on each home router: "the other LAN via the local HA/RPi". Enable
   `accept_routes` and SNAT on the subnet routers. The panels then dial LAN
   addresses directly. Cleanest; needs router access in each house.
2. **A relay on the house's HA/RPi.** One TCP forward per remote panel, e.g.
   `socat TCP-LISTEN:13403,fork TCP:192.168.2.40:134`. The phonebook entry for
   10003 points at the local relay. Works even with identical LANs; one line per
   remote panel.
3. **Identical LANs and no relay:** only the phone path works, via Tailscale's
   4via6 addresses (`fd7a:115c:a1e0:b1a:0:<site>:<ipv4>`). i-Telex is IPv4-only,
   so panel-to-panel is out.

**Recommendation: 1 where the router allows static routes, 2 otherwise.** Both
need no change to the module: only the phonebook differs.

## 6. Numbering plan (proposal)

- Five digits, as i-Telex requires. `1HHNN`: HH is the house, NN the device.
  So 10101 is the kitchen panel in house 01, and 10201 the first panel in
  house 02.
- The phonebook lives in each device's configuration for now. A family
  directory, i.e. a small TNS on the RPi5 speaking the same Peer_query, is the
  next step once there are more than a handful of numbers. A C# server exists:
  [detlefgerhardt/ItelexSubscriberServer](https://github.com/detlefgerhardt/ItelexSubscriberServer).

## 7. What comes next, in order

| # | Step | Where | Gate |
|---|---|---|---|
| 1 | The module: codec, packets, session, station, example, host tests | KB `modules/itelex/` | **done**: host tests PASS, compiles for the S3; link + flash on the bench |
| 2 | Interop with piTelex over TCP (host build of the session) | `test/interop/` | **done**: 12/12 PASS |
| 2b | The same on hardware: the example on a spare ESP32-S3 vs piTelex on a laptop | bench | text both ways; End seen |
| 3 | Tailscale subnet router in house 1 (the HA add-on, `advertise_routes`); a phone's telnet app to the S3 | HA | a telegram typed on the phone prints on the S3 |
| 4 | The panel: `src/itelex/` behind `-DITELEX_ENABLED`, a TELEX page (ZCZC header, letter-by-letter typing, receipt), the knob for canned replies, the flag-matrix row, the RAM delta measured | fork `feat/itelex` | only on the owner's word: «в прошивку пока не интегрируй» |
| 5 | Across houses per §5; the family directory on the RPi5 | routers / RPi5 | panel ↔ panel between houses |
| 6 | The public network: ask the i-Telex admins; Centralex with the granted number and PIN | telexforum | a call from a real teleprinter |

## 7b. Minitel

Asked the same day. The iodeo dongle's firmware has a raw-TCP mode, so a
Minitel can reach a panel's address today.
- Its keys start with bytes that look like i-Telex packets, so the station got
  an optional ASCII-only port.
- A "3615 TELEX" service on the RPi5 (MiniPavi) is the full experience.
- Details and sources: [modules/itelex/docs/MINITEL.md](../modules/itelex/docs/MINITEL.md).

## 8. Questions for the owner

1. §5: can the home routers take a static route, and may one house's LAN be
   renumbered?
2. §6: is the `1HHNN` numbering right, and what are the answerbacks, e.g.
   `10101 KUX NIKOSCOPE`?
3. Should a telegram on the panel look like a telegram, with the `ZCZC … NNNN`
   header and CAPITALS only? Or should it keep lower case when it arrives by
   plain ASCII from a phone?
4. Should we ask the i-Telex administrators now, or keep it family-only?
