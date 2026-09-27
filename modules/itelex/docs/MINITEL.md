# Minitel on the family teletype network

Asked by the owner on 2026-09-27: «а может Minitel сети и протоколы
использовать? Относительно минител, уже есть решение:
https://www.tindie.com/products/iodeo/minitel-esp32-dongle/».

A study with sources. Only one piece is built: the ASCII-only port, see §4.

## 1. What the iodeo dongle is

- **The hardware.** An ESP32-WROOM-32E board that plugs into the Minitel's
  DIN-5 socket and is powered from it. It has USB-C, a buck converter and
  auto-reset
  ([hardware README](https://github.com/iodeo/Minitel-ESP32/blob/39c49b8462b46dfb7da84c08aecdd48e5c52a224/hardware/README.md)).
- **Buying it.** Tindie shows it **sold out since 27 Oct 2025**, at $62.50. EU
  orders go through a form on iodeo.fr, and buyers in the comments report no
  answer.
- **The firmware** is `Minitel1B_Telnet_Pro`, by Louis H. and F. Sblendorio of
  Retrocampus, GPL-3. It connects by:
  - **Telnet**, which is **raw TCP to any host:port**, bytes passed through
    ([`loopTelnet`](https://github.com/iodeo/Minitel-ESP32/blob/39c49b8462b46dfb7da84c08aecdd48e5c52a224/arduino/Minitel1B_Telnet_Pro/Minitel1B_Telnet_Pro.ino#L313-L338));
  - WebSocket (ws/wss);
  - SSH;
  - serial.
- **Setting it up.**
  - Configured on the Minitel's own screen, with 20 presets stored in SPIFFS.
    MiniPavi `ws://go.minipavi.fr:8182`, 3615co.de and Retrocampus are among
    them.
  - 4800 baud, falling back to 1200 on a Minitel 1.
  - Builds on the esp32 core **2.0.x**, the same core as our panels.

**So a Minitel can already open a raw TCP line to a panel's address**,
through the house LAN or the Tailscale subnet router, like a phone's telnet app.

## 2. What a Minitel speaks

- **Code:** Télétel / Videotex (CEPT-2 command set, per the PTT's 1986 notice).
  **The standard number NF Z 77-030 is not verified.**
- **Screen:** 40 × 24 plus the status row 0. The Minitel 1B also has an
  80-column "mode mixte".
- **Line:** 7 data bits, even parity (7E1).
- **Control codes** ([Minitel1B_Hard.h](https://github.com/iodeo/Minitel1B_Hard/blob/203a5a233ad35b785b93e91aed211195ba1438d7/Minitel1B_Hard.h#L125-L177)):
  - FF 0x0C clears the screen;
  - US 0x1F positions the cursor;
  - SO/SI switch the mosaic set;
  - SS2 0x19 starts an accent (G2);
  - the function keys are **DC3 0x13 + a letter**: Envoi 0x41,
    Correction 0x47, Suite 0x48, and so on.
- **No Cyrillic.** Its character sets are Latin with French diacritics.
  Redefinable characters (DRCS) exist on the **Minitel 2** only. A Cyrillic
  font could in principle be loaded there; nobody was found doing it.
  **Not verified.**

## 3. Three ways to bring a Minitel in

| | How | Effort | Verdict |
|---|---|---|---|
| **A. Dongle → the panel's port** | the dongle's raw-TCP mode to `<panel>:<ascii port>`; the station talks plain text | small; the connection part is built (§4) | **the first step**: works with Latin text today |
| **B. "3615 TELEX" service on the RPi5** | a MiniPavi gateway ([ludosevilla/minipavi](https://github.com/ludosevilla/minipavi), GPL-3, runs on a Pi) plus a service (PHP or any HTTP+JSON). The service is an i-Telex client into the family network: inbox, dial a number, the phonebook, receipts shown in row 0 (`createPushServiceMsgCmd` in [MiniPaviCli](https://github.com/ludosevilla/minipaviCli)) | 1-2 weeks | **the real Minitel experience**, with menus and pages; also opens the web Minitel emulator to family members without a terminal |
| C. The panel shows Videotex pages | a 40 × 24 page is 320 × 250 px; the panel is 128 × 64 | high | **no**: only a ticker of row 0 or a mosaic picture would fit |

### What option A still needs beyond §4 (not built)

- **Videotex output.** The station answers in UTF-8, which a Minitel shows as
  rubbish for anything outside ASCII. It needs:
  - accents sent as SS2 sequences;
  - Cyrillic transliterated;
  - lines wrapped at 40 columns.

  A small output filter on the ASCII port would do it.
- **Minitel keys as text:**
  - Envoi → CR LF;
  - Correction → backspace;
  - SS2 accents → Unicode;
  - Connexion/Fin → hang up.
- **The panel's own number.** The Minitel dials an address, not a number. A
  number directory is option B's job.

## 4. Built: an ASCII-only port

- **The problem.** Detection by the first byte is how piTelex tells an i-Telex
  call from an ASCII one (`txDevITelexCommon.py` L29-31): bytes 0x00-0x09 and
  0x10-0x1F mean i-Telex. A Minitel whose user first presses Envoi (0x13) or an
  accented letter (0x19 ...) would therefore be taken for an i-Telex station.
- **The fix.** `StationConfig::asciiListenPort` opens a second port where every
  call is ASCII from the first byte. The i-Telex port 134 stays exactly as
  compatible as before.
- **Tested:** `testAsciiPort` in `test/host/test_itx.cpp`.

## 5. What the owner would need

- A **Minitel 2** rather than a 1B: 9600 baud and DRCS. Prices not checked.
- The **dongle**, if iodeo takes an order again. Otherwise build one from its
  published schematic (CC-BY-SA 4.0): an ESP32, a DIN-5, an NPN transistor, a
  buck converter.
- **Do not wire an ESP32 straight to the Minitel's TX line** as the Arduino
  examples do: their pull-up goes to +5 V.

## 6. Licences

These are all GPL, and the NickoScope-Telex library stays MIT by keeping them
out of it:
- the dongle firmware and Minitel1B_Hard: GPL-3;
- MiniPavi: GPL-3;
- MiniPaviCli: GPL-2+.

A "3615 TELEX" service is a separate program that talks to the stations over
TCP, so it can be GPL on its own without affecting the library.
