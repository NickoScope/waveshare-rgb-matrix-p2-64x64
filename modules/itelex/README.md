# NickoScope-Telex: a teletype station for any ESP32

**i-Telex compatible.** The i-Telex protocol (telex over the internet) as a plug-and-play library:
drop it into any ESP32 Arduino project and the device becomes a teletype
station. It has a number, answers calls, prints what arrives letter by letter,
answers "КТО ТАМ?", and dials other stations.

Written for the family of LED panels (design:
[waveshare-rgb-matrix-p2-64x64 docs/38](https://github.com/NickoScope/waveshare-rgb-matrix-p2-64x64/blob/claude/waveshare-led-email-whatsapp-network-y01laq/docs/38-family-teletype-itelex.md)).
It knows nothing about the panel. **It is not in the panel's firmware yet**, by
the owner's word.

## Status

| | |
|---|---|
| Host tests | **PASS**, 97 checks, ASan + UBSan: `test/run_host_tests.sh` |
| **Interop with piTelex** (the i-Telex reference implementation) | **PASS**, 12/12, both directions, 3 runs in a row: `test/interop/run_pitelex_interop.py --pitelex <clone>` |
| ESP32-S3, arduino-esp32 2.0.17 | **compiles**, no warnings (`gnu++11`, `-Wall -Wextra`); not linked or flashed yet |
| Against a real teleprinter on the public network | **not tried** (needs a number, see below) |
| Centralex, TNS lookup | written from the spec and piTelex; **not tried** against the live servers |

### What "compatible" was checked against

The interop test runs piTelex's **own i-Telex code** (commit ece3d43,
`txDevITelexClient` / `txDevITelexSrv`) against our station over real TCP
sockets. It plays piTelex's printer through the same escape-sequence
interface its hardware drivers use.

1. **piTelex calls us:**
   - its text arrives;
   - our reply prints on its side;
   - its WRU gets our answerback;
   - its hang-up (End) is seen.
2. **We call piTelex:**
   - our text prints there;
   - our WRU is recognised (piTelex shows `#`);
   - its reply and answerback reach us;
   - our hang-up is seen.

piTelex is not vendored: point `--pitelex` at a clone.

## Using it

```ini
lib_deps = https://github.com/NickoScope/NickoScope-Telex.git
```

(a private repository needs git credentials on the build machine), or a local
clone with `symlink://../NickoScope-Telex`, or a copy in the project's `lib/`.
Then:

```cpp
#include <ITelex.h>

static const itx::PhonebookEntry kBook[] = {
  {10101, "192.168.1.57", 134, "", false, "KUX"},
  {10201, "192.168.2.40", 134, "", false, "GAR"},
};
itx::Station station;

void setup() {
  // ... Wi-Fi up ...
  itx::StationConfig cfg;
  cfg.session.answerback = "10101 KUX NIKOSCOPE";
  cfg.phonebook = kBook;
  cfg.phonebookLen = 2;
  itx::StationEvents ev;
  ev.onChar = [](void *, uint32_t cp) { /* show one character */ };
  station.begin(cfg, ev);
}
void loop() {
  station.loop();
  // station.dial("10201"); station.send("УЖИН В 8\r\n"); station.hangup();
}
```

The full, runnable example is [examples/SerialTeletype](examples/SerialTeletype/SerialTeletype.ino).

**Which code on the line.** The i-Telex network is ITA2: piTelex builds its
line codec with the ITA2 table. So is this station, by default. Russian text
to an ordinary station is transliterated (`ПРИВЕТ` → `PRIVET`).
- Two of **our** stations recognise each other by the Version packet: our id
  starts with `nk`, piTelex's with `pi`.
- They then switch the line to **MTK-2**, so Cyrillic passes as Cyrillic.
- Nothing is configured per call. A caller waits up to 3 s for the peer's
  Version before sending text, so it never guesses.

**The receipt.** By default a received character counts as printed when it
arrives. A display that types text out slowly should call
`station.printed(n)` as it shows characters. The sender's Acknowledge then
means "on the screen", the way it meant "on the paper".

**From a phone.** Any telnet or raw-TCP terminal app, to `<device IP>:134`.
- Across houses, the address comes through the house's Tailscale subnet
  router.
- The station sees plain ASCII instead of i-Telex packets, and takes the text
  as UTF-8, so Russian arrives unchanged.
- It answers in UTF-8.
- An ASCII caller may idle for 10 minutes; an i-Telex one for 30 s.

**An ASCII-only port** (`StationConfig::asciiListenPort`, off by default).
Auto-detection works on the first byte, like piTelex. A **Minitel** (with the
iodeo dongle's raw-TCP "Telnet" mode) starts with bytes that are also i-Telex
packet types: *Envoi* is DC3 0x13, an accent is SS2 0x19, an arrow is ESC 0x1B.
On the ASCII port there is no guessing. See [docs/MINITEL.md](docs/MINITEL.md).

## What is in it

| File | Arduino? | What |
|---|---|---|
| `src/itx_baudot.*` | no | ITA2 and MTK-2 (Russian register on code 0x00), bit-reversed as the i-Telex wire needs, shifts only on a register change, UTF-8 in/out, transliteration for plain ITA2 peers |
| `src/itx_packet.*` | no | station packets 0x00-0x09, Centralex 0x81-0x84, TNS Peer_query / Peer_reply_v1 / Client_update; direct-dial extensions; a streaming parser that tells packets from ASCII and skips telnet IAC |
| `src/itx_session.*` | no | one call over any transport (a write callback and `feed()`), described in the header |
| `src/ITelex.*` | yes | `itx::Station`: WiFiServer on :134, one call at a time, `dial()` by phonebook → TNS → `host:port`, the Centralex line |
| `test/host/test_itx.cpp` | no | the codec against piTelex vectors, the packets against the spec's examples, two sessions back to back (binary and ASCII, ITA2/MTK-2 by peer, flow control, WRU, hang-up, refusals, time-outs, the ASCII port) |
| `test/interop/` | no | `itx_tcp` (the session on a POSIX socket) and the piTelex interop driver |

### What the session does

- It tells a binary i-Telex call from a plain ASCII one (a telnet user) by the
  first bytes, as piTelex does.
- It decodes Baudot / MTK-2 to Unicode characters, and encodes UTF-8 text back.
- It answers WRU ("Wer da? / КТО ТАМ?") with the station's answerback.
- It keeps the i-Telex Acknowledge honest. The counter reports what the owner
  says it has *shown* (`printed()`), not merely what arrived.
- It throttles its own sending by the peer's Acknowledge, so a real 50-baud
  teleprinter at the other end is never flooded.
- It hangs up cleanly (End), notices a rejection, and times out a dead peer.

## Cost

| | |
|---|---|
| Flash | ~10.7 KB (`.text` of the four objects, `-Os`) |
| `sizeof(itx::Station)` | 1,716 B, the session (1,196 B) included; no heap allocation after `begin()` except the `WiFiServer` |
| Tasks, TLS | none: it runs from your `loop()`, over plain TCP |
| lwIP | one listening socket, plus one per call (two while a Centralex line is up); their buffers are not measured |

A global `Station` lands in internal `.bss`. Where internal RAM is tight, as on
the LED panel, allocate it in PSRAM instead, e.g. `ps_malloc` and placement
`new`.

`dial()` and the Centralex (re)connect block for a TCP connect, at most
`connectTimeoutMs` (3 s). Run the station on its own task if `loop()` must never
wait.

## The protocol, and where each fact comes from

- **Packets:** the i-Telex Communication Specification (telexforum.de, lexicon
  entry 74). Its worked examples are test vectors here:
  - Connect Remote `81 06 4D 97 53 00 21 B4`;
  - Client_update `01 08 16 AA 34 00 34 12 86 00`;
  - Peer_query `03 05 16 AA 34 00 01`.
- **Wire order of the Baudot code.** Bit-reversed against the usual ITA2
  tables: piTelex `txDevITelexCommon.py:257`, `BaudotMurrayCode(False, False,
  True)`, where the third argument is `flip_bits`.
- **Behaviour** (commit ece3d43 of [piTelex](https://github.com/fablab-wue/piTelex)):
  - the caller sends Version, then Direct Dial;
  - a called station answers Version with its own;
  - Acknowledge about once a second;
  - Baudot data of 1-50 codes a packet;
  - End on hang-up, Reject with a reason;
  - Centralex heartbeat every 15 s, the line dropped after 35 s of silence.
- **Cyrillic:** the MTK-2 tables are piTelex's `_LUT_BM2A_MKT2`.

piTelex is GPL-3. It was read as a reference and run as a test oracle (it
produced the Baudot vectors); none of its code is in this MIT library.

## Known limits

- **Ч.** MTK-2 as piTelex tabulates it has no Ч; it is sent as the figure 4.
  **Not verified** against a Soviet MTK-2 table. Ё is sent as Е, Ъ as Ь.
- **BELL.** MTK-2 gave BELL's code to Ю, so a bell is dropped in MTK-2; ITA2
  keeps it.
- **One call at a time.** A second caller gets Reject "occ", as on a real line.
- **Direct-dial extensions** are accepted and reported (`session().extension()`),
  not routed.
- **IPv4 only**, as i-Telex. No TLS: across the internet the tailnet (WireGuard)
  is what encrypts. A Centralex line to the public relay is plain text.
- **The public i-Telex network** gives numbers only through its
  administrators, and expects a real teleprinter behind them (see the design
  document, §3). The
  family network needs neither: TNS lookup and Centralex are off by default.
- **DNS.** Hosts are resolved by the core's DNS; `.local` (mDNS) names are not.
