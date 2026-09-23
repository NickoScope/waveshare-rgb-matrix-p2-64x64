# Handoff

Rolling record of where the work stands. Newest first.

## 2026-09-23 (09:45): the radio's memory — single-frame experiment parked as a debt, panel back on 2.5.5

**The owner's call (09:37):** back to double buffering, keep the single frame
as a debt and think again later. The panel was USB-flashed with main = tag
v2.5.5 (48d3665, no source changes since); it runs 2.5.5 and the carousel is
back on. After a USB flash the OTA state reads "undefined", which is normal:
there is no pending image for boot_health to confirm.

**What the experiment was** (branch `feat/frame-in-psram`, pushed, last commit
c73a424; version 2.5.6 there, never released): one HUB75 DMA frame instead of
two, pages draw into a PSRAM frame, and display() copies the changed rows into
the DMA frame timed to the scan. A GDMA probe reads the descriptor the DMA is
on and counts, on the panel itself, the frames that showed a pass half old and
half new. `/api/frame?sync=0|1|2` switches the timing (off / follow / ahead);
`?detail=1` shows the last 8 mixed frames. `tools/frame_sync_bench.py <ip>`
runs every mode on the same pages with the carousel held off.

**Measured on hardware:**
- Radio pool (DMA-capable internal heap): about 86 KB free and a minimum of
  72–78 KB, against 15–19 KB free and a minimum of 380 B–1.5 KB on 2.5.5.
  Stress and normal self-tests passed (ping 8/8, no allocation failures).
- Tearing, 30–40 s per mode on Tetris, Minecraft and Snake at 20 flips/s:
  sync off ~63 % of changed frames mixed (the negative control works); follow
  and ahead both 1–2 % mixed; double buffering 0 by construction.
- Waiting for the scan costs 1.8–2.3 ms per frame on average in follow mode
  (7–8 ms worst) and 4.3 ms in ahead mode (9.1 ms worst). The copy takes
  about 3 ms. The flip rate did not drop.
- Cause of every remaining mixed frame, from the probe's notes: row 0 written
  while the scan was on row 31, about to come round to row 0. Holding the
  scheduler during the copy did not help (13 of 1152 mixed).
- The last idea is built on the branch but **not measured**: a guard that
  starts the copy from the next pass when the scan is on the last three rows
  (at most about 1 ms more wait).

**Debt, for when this is picked up again:**
1. Flash the branch, run `frame_sync_bench.py` for several minutes on several
   pages. Adopt only if follow mode shows 0 mixed frames. Anything above 0 is
   visible tearing that 2.5.5 does not have.
2. If it is not 0: look for other ways to free the radio's pool that keep
   double buffering, e.g. fewer colour bits for the second buffer. Colour depth
   is off limits by the owner's rule, so that needs his word first.
3. Until then the pool stays the known risk: debt 1 in the list below (fast
   page switches after boot starve the radio). The 2.5.3 heap back-off and
   network watchdog are what keep it on the network.

## 2026-09-23 (08:44): first live over-the-air update through the SDK — UPDATED

The owner asked for a live run with all the communication through him.
v2.5.5 (48d3665) published on the flasher and as a GitHub Release (his
"отправляй"). `tools/agent/update.py --install` ran with his answers relayed
word for word through a pipe: "yes" (his first answer was "да" - not relayed,
he was asked again), "update", the panel's name. Image checked (SHA-256
da7dd6ad..., ESP32-S3), sent, panel back in 10 s on 2.5.5, OTA state pending,
confirmed by boot_health at 76 s: **UPDATED, app1, valid.** Read-only self-test
after: ping 3/3, portal 12/12, no allocation failures; dmaMin 1,508 B since boot.

Also today on main: Cyrillic (2.5.4), IR receiver on GPIO0 with ten learnable
buttons, DHCP name, brightness rounding, health.py, update.py - each through
the gate audit. Ideas and the owner's two remarks on the update flow:
docs/ideas.md. Still first on the list of real work: the radio's DMA pool.

## 2026-09-23 (08:10): the self-test, the panel's name in DHCP, brightness rounding — on main (0c3d573), not flashed

- `python3 tools/agent/health.py` (and MCP `panel_selftest`): ~30 s health run,
  verdict + findings, raw logs in health-logs/<time>/. Use it before and after
  any change instead of probing by hand. --list/--panel/--all, --read-only,
  --stress, --serial. Restores everything it changed on any exit.
- Firmware 2.5.4 now also carries: DHCP hostname = panel name (eero showed
  esp32s3-XXXXXX), brightness percent rounding (95/101 values drifted 1%).
- Both gate audits APPROVED (Cyrillic; this change after one CHANGES-REQUIRED).

Debts the self-test found (firmware, all about the radio's DMA-capable pool):
1. Pages switched fast soon after boot (1.5 s, flights/trains start TLS) took
   the pool to 1,396 B; radio buffers failed; off the network 3 min until the
   watchdog. At the 2 s pace the radio still failed its 1,626 B buffer twice.
2. The portal's CSS and JS answer 503 even after Retry-After while those
   fetches run: a browser opening the portal then gets an unstyled page (the
   browser does not retry a stylesheet). Consider never refusing the two
   assets, or inlining them.
3. Opening the USB console resets the board on this Mac even with DTR/RTS low.
4. saveSettings() persists the runtime brightness set over the API (the code
   says it does not) — backlog.

## 2026-09-23 (07:55): Cyrillic built — v2.5.4 on main (060926d, 79e5dd9), NOT flashed

Done, per the plan below: PicopixelCyr (tools/fonts/mkcyr.py -> picopixel_fb.h),
strict decoder src/fonts/utf8_next.h (200,035 inputs = Python), shared
src/fonts/pxfb_text.h; px.text/px.width and the world clock's name path use it;
luasim the same; fx_parity identical on every script + cyrillic_test.lua + the
world clock page; missing glyph = solid block (the hollow box read as 0).
Flash +2,340 B, RAM 0. SDK effect_api and AGENTS.md updated. All three envs build.

Gate audit (senior-code-audit, after the fact): APPROVED, 0 critical/high.
ASCII identical on 600k strings, decoder 381k exhaustive cases under ASan,
no out-of-bounds for any code point, RAM 116,936 B before and after. Two lows
fixed (737caa0). Open lows: const tables in a header are copied per file
(Cyrillic twice, ~870 B each; Latin already 11 times, ~9.4 KB, older debt);
З equals the digit 3 pixel for pixel (decide on the wall); mkcyr needs one
build for Picopixel.h; lua_effects.cpp drawMessage still print()s the effect
name and Lua error text (Cyrillic would vanish there).
Quick panel test 07:15 on v2.5.3: API brightness/display/notify/pages all 200,
portal 15 sections + 3x Save & apply "Saved", 29/29 pings, radio 0 failures
(the one failure was the yacht page's 12 KB stack, known). Uploaded Lua slots
on this panel are empty: the aquarium lives on the old panel only.

Waiting for: the owner's word to flash, then the wall check of И Й Л Д У Ж Щ Ё
(test card: upload tools/luasim/scripts/cyrillic_test.lua after flashing), and
the release (release.py + GitHub Release, notes drafted first).

Debts found on the way (not in this change):
- World clock city names are ASCII in NVS (WcCity.name[21], worldClockCheck
  A-Z only; "Москва" fits to ""). Cyrillic names need a new NVS format.
- Media titles and notifications use the built-in 5x7 font (no Cyrillic); the
  media page transliterates (ICAO 9303). A 5x7 Cyrillic set would be its own job.
- Flight board, rail board, yacht radar, market print ASCII data via print();
  switching them is per page, when their data can carry Cyrillic.

## 2026-09-23 (00:52): the plan — Cyrillic as a system font

The owner's decision: build Cyrillic by the ledmatrix agent's plan
(docs/drafts/cyrillic-from-openclaw/cyrillic-font-design.md, generator mkcyr.py),
plus the additions from the review (review-2026-09-23.md):

1. Second range U+0400-045F (PicopixelCyr) beside PicopixelFB; case folded
   like the Latin one.
2. One shared UTF-8 decoder and one draw/width helper (`pxfbNextCp`,
   `pxfbGlyph`, `pxfbDrawText`, `pxfbTextWidth`) used by Lua px.text/px.width
   and by every C++ page that prints user strings (worldclock, flightboard,
   media, cards, railboard...). Latin output must stay byte-for-byte.
3. **Added:** a visible missing-glyph box instead of a silent space; strict
   decoding (reject C0/C1 overlong leads and broken continuations); undrawn
   slots of U+0400-045F point at the missing glyph.
4. luasim.c and gen_font.py changed in the same commit, or fx_parity lies;
   mkbdf.py skips codes >= 0x80.
5. Checks: fx_parity 0 px on a Cyrillic test effect and on the whole gallery
   (Latin regression); px.width folds case; on the wall, by eye, И Й Л Д У Ж Щ.
6. Flash only on the owner's word.

Order: generator and header -> Lua path + luasim -> fx_parity -> C++ pages.

## 2026-09-23 (00:40): yacht radar is dark, and the fix that lit it was rolled back

State: the panel runs v2.5.3 as published (e40be2f/9e9ee88), no yacht change.

- The yacht page shows "no memory for the AIS stream task": the task wants a
  12,288 B stack in one internal block, and the largest block is 7-11 KB now
  (`allocation failed: 12288 B, caps 0x804, before yacht radar`). It gives up
  until the page is left and re-entered.
- Tried (git stash "yacht-retry-8k" in ~/AnimatedPixelClock-netbroker): an 8 KB
  stack (three connected readings left 9,232-9,268 B of 12 KB free, a ~3 KB
  peak; this run left 5,168 of 8,192) and a retry every 5 s while the page is up.
  The task then started, 7 vessels arrived, **and the TLS session to aisstream
  took the DMA-capable pool to 1,012 B largest / 756 B minimum: the radio failed
  its 1,626 B buffers, the portal answered 503 throughout, and the panel left
  the network.** Rolled back by USB within minutes.
- tlsUsePsram() is in main.cpp, yet the drain happened with the session open:
  find out what of the websocket/TLS path still lands in internal DMA memory
  before the yacht radar may run again. The stack fix alone is not safe.
- **DEBT (owner, 2026-09-23 00:43): the yacht radar used to run freely here.**
  It was a working page after its own task landed (bfe7375, 2026-09-14) and
  through the week after; now it cannot even start. So this is a regression:
  something since then took the internal and DMA-capable memory it lived on.
  Candidates in time order, none proven: Lua effects over the air (82e32f8,
  2026-09-21, a 12 KB task stack plus its heap), the net broker, the market
  and media stores, and v2.5.3's portal queue and DMA guard (the guard now
  refuses the portal while the TLS session is open, where before it served it).
  Start by bisecting on the panel: the last build where the page shows vessels
  with the portal open, then the first where it does not.
- Cyrillic: the ledmatrix agent on nickol.local wrote the design and generator
  on 2026-09-22; copied to docs/drafts/cyrillic-from-openclaw/.

## 2026-09-23 (00:25): release like upstream, flasher and README cleaned of upstream leftovers

Done:
- GitHub Release v2.5.3 published on the fork (tag at 9e9ee88), the way
  upstream does it; every flasher version gets one from now on.
  `gh` in the firmware repo defaults to upstream Keralots: always
  `-R NickoScope/AnimatedPixelClock`.
- Flasher: companion and release-notes links point at our releases/latest;
  the wiring-guide link (jumper-wire boards) and "flashed from a phone" removed.
- Issues enabled on the fork, so "report a bug" works.
- README rewritten for the fork (0fc4b59): a 3x3 grid of host renders
  (img/screens.png), Waveshare-only hardware, a table of pages, Lua, the knob,
  Home Assistant, the SDK, our flasher and releases, credit to upstream.

Left:
- **Owner takes live photos of the screen on 2026-09-23.** Put them in the KB
  first (photos/<date>/, EXIF stripped), then the README beside the renders.
  Useful: the whole panel on the wall, the aquarium, the world clock, the flight
  board, a clock style. No people in frame, and markets only on the indices page.
- Sponsor button removed (FUNDING.yml with `ko_fi: keralots` deleted, 3dc00f5,
  owner's call). The repo description and homepage are ours now
  ("128x64 RGB LED wall panel on the Waveshare ESP32-S3-RGB-Matrix: ...",
  homepage = our flasher).
- From before: flasher points 2 and 3 (name at setup, AP "<name>-Setup"),
  4 (secrets in the portal), sound D11, rotating the MQTT password and AeroAPI
  key after NickoSha left.

## 2026-09-22 (23:55): opening the portal no longer drops the panel off the network

Firmware commit e40be2f (v2.5.3, flashed over USB to NickoScopeMatrix-64x128-01;
published on the flasher page 2026-09-22 as release commit 9e9ee88, image
sha256 6c7a11c0… verified byte-for-byte from GitHub Pages). `release.py` needs
Python 3.10+ (`python3.12 release.py`), the system 3.9 fails at SHA256SUMS.

**Cause, measured over the cable.** The Wi-Fi task allocates its 1,626 B receive
buffers from the *DMA-capable* internal pool (caps 0x80c = INTERNAL|DMA|8BIT).
One portal visit issued 48 requests, many at once; each one waiting in the
synchronous web server holds such buffers. The DMA pool's largest block fell
11,252 -> 5,108 -> 3,572 -> 1,396 B and the radio failed. The portal guard read
the *general* internal pool, which still showed 7,668 B, so it let everything
through.

**Why the watchdog did not revive it.** A probe that cannot even be sent was
deliberately "not counted against the gateway", and the only other path was a
15-minute blind timer. Now two unsendable rounds in a row restart Wi-Fi: seen
recovering in about 3 minutes, no reboot.

**Fixes.** portal.js queues every same-origin request, one on the wire at a time
(duplicates shared, 503 retried after Retry-After); the guard also reads the DMA
pool (radio 1,626 B + TCP send buffer 5,760 B from sdkconfig); /api/info has
dmaFree/dmaLargest/dmaMin and [mem] prints `dma free/largest`.

**Verified.** Every page clicked through twice, fast clicks, six Save & apply,
three reloads, two browsers at once: 109/109 pings, 0 radio allocation failures.

**Left.** A page *reload* still loads HTML/CSS/JS in parallel through the browser
(not the queue); once it took the DMA block to 1,588 B without a failure. If it
ever fails there, inline portal.css into the page. Watchdog escalation and the
queue are the two things to check first if the drop comes back.

## 2026-09-22 (23:10): NickoScopeMatrix-64x128-01 is the main panel now

The owner gave the first panel, **NickoSha-64x128, to his son** for remote
testing. The second controller, **`NickoScopeMatrix-64x128-01`**
(`90:E5:B1:D2:0E:2C`, 192.168.4.89), is the main panel.

It was provisioned from **the same file the first panel was provisioned from
on 2026-09-14** - `~/AnimatedPixelClock/provision_secrets.ini` - through
`env:provision` over USB, then v2.5.2 flashed back over USB. All eight values
written (the sketch prints key names and lengths, never values), and after
boot: MQTT `connected: true`, AeroAPI key present, RTT token present,
aisstream key present. The copy made for the build was deleted; the original
stays where it was.

**A mistake to not repeat.** I first gathered the secrets from the NickoScope32
flagship's source tree and from Home Assistant's secrets.yaml, because
provision_secrets.py offers both. The owner stopped it: another project is not
this one's to read from just because a tool can. That file was deleted before
anything was flashed. The rule: a panel's secrets come from this project's own
provisioning file, and nowhere else without being asked.

**Still to do:**

  * ~~Home Assistant publishes to the OLD panel~~ - **done 23:20.** Presence
    and the rail board publish to device-independent topics and needed
    nothing. Media: one line in AppDaemon's apps.yaml (`matrix_media.device`).
    Markets: `device` lives in the app's private `local.json`, which overrides
    apps.yaml.

    **The markets move had a trap, and it is worth knowing.** The app builds
    each sensor's `unique_id` from the panel id but its `default_entity_id`
    without it. Change the id and HA sees 44 new unique_ids that want names
    already taken - and hands out `..._2` to all of them, blinding every
    dashboard. The app cannot withdraw its old discovery itself: it remembers
    what it sent only in process memory, and turning `ha.discovery` off
    withdraws nothing. So the order was: withdraw the 44 retained `d20ec8`
    configs by hand (an empty retained message is how MQTT discovery removes
    an entity; HA then removed the old device and freed the names), change
    `device`, then restart only that app by touching its module. Result: the
    same 44 entity_ids, no `_2`, device `matrix_market_d20e2c`, and the panel
    accepting market payloads under the new id.

    Two things learned on the way that cost a minute each: AppDaemon resolves
    `!secret` from **its own** secrets.yaml in the add-on directory, not
    `/config/secrets.yaml`; and an unauthenticated `mosquitto_sub` returns an
    empty list rather than an error - "nothing retained" looked exactly like
    "not allowed to look" until the credential lengths came out as 0.
  * **NickoSha left the house with the owner's credentials in its NVS** - the
    HA MQTT login, the paid FlightAware AeroAPI key, the RTT token and the
    aisstream key. It cannot receive HA data on another network, but the values
    can be read off its flash over USB in a minute. Rotating the MQTT password
    and the AeroAPI key is the reliable answer now that the panel is gone.

## 2026-09-22 (evening): a second panel, v2.5.2, and no broker by default

**A second controller** was installed from the web flasher on 2026-09-21 and
checked tonight over USB and the network: `90:E5:B1:D2:0E:2C`, now named
**`NickoScopeMatrix-64x128-01`** (192.168.4.89). Its image landed cleanly -
32 MB octal flash booted, no crash history, 31 KB internal free. **No secrets
in it at all**, as it should be: AeroAPI key, RTT token and aisstream key all
report not set; only Wi-Fi arrived, through Improv.

It was on **v2.5.0** - flashed during the window before v2.5.1 was published at
01:12, so it had four slots, a 24 KB cap and the upload bug. Now on v2.5.2 by
OTA, `app1 valid`, twelve slots, 50 KB.

**v2.5.2 fixes a default broker.** The firmware carried
`homeassistant.local` as the MQTT host for every panel, and `configured()`
only asked whether the host string was empty. So a freshly erased panel with
nothing entered reported `configured: true` and knocked on whatever Home
Assistant answered to that name - with no credentials. It also inverted last
night's bringup.py rule, which reads "configured but not connected" as a broker
that is down: on a new panel that meant refusing to switch off the MQTT pages
on the very board the rule was written for.

Now there is no default. Neither a host nor a user stored means NO BROKER. The
single exception keeps old panels alive through an OTA: credentials with no
host means one provisioned while the default existed, and it keeps
`homeassistant.local`. Proved on the new board: `configured: false`, and
`bringup.py --check` now offers to switch off media, markets, flights and
trains instead of refusing.

**The web flasher now offers one board** - the Waveshare, the only one ever
installed from it and seen to boot - and serves v2.5.2. The other two images
are gone from `docs/`, so not even a direct link reaches them.

**The wall panel (`NickoSha-64x128`) is still on v2.5.1** and was not touched.
It is safe to take to v2.5.2 whenever: its broker is connected with
credentials, so whether its host is stored or defaulted, the legacy fallback
covers it.

**Checked tonight, and clean: no secrets are compiled into the published
firmware.** The strings in the image hold only generic defaults, and the
provisioning secrets live in `[env:provision]`, which builds a separate one-shot
sketch, never the firmware. The real gap is the opposite of a leak: a panel from
the page has no way to receive AeroAPI, RTT, aisstream or MQTT credentials
short of PlatformIO and a USB cable. That is the owner's point 4, still to do,
with points 2 (name at setup) and 3 (the AP called `<name>-Setup`).

## 2026-09-22 (morning): the SDK handed to the OpenClaw fleet on nickol.local

The panel SDK is installed and registered on the Raspberry Pi, and the task of
building the agent itself is in the fleet's inbox:
`~/agents-vault/00-Входящее/2026-09-22-агент-светодиодной-панели.md`.

    ~/ledmatrix-mcp/                     clone of the public repo, updates with git pull
    ~/ledmatrix-mcp/tools/agent/.venv    Python 3.13 + mcp, pydantic
    ~/ledmatrix-mcp/tools/agent/run.sh   in the house pattern, like nickoscope-mcp
    ~/.openclaw/openclaw.json            mcp.servers.ledmatrix, scoped to agent id `ledmatrix`

Verified rather than assumed: the server starts over stdio and lists its 23
tools, and the panel answers from the Pi - v2.5.1, ~18 KB internal free. The
config was backed up first (`openclaw.json.bak-20260922-084506`) and diffed
after: the only change anywhere in it is `+ mcp.servers.ledmatrix`.

**The gateway was restarted at 08:56**, on the owner's word rather than on my
own initiative - it carries his Telegram bots and the rest of the fleet. It
came back clean: active/running, port 18789 listening, `/health` answering
`{"ok":true,"status":"live"}`, the outbound connection to `api.telegram.org`
re-established and all 14 openclaw processes back. It has now read the config
containing `mcp.servers.ledmatrix`.

### The agent exists, and the SDK updates itself at night

Done at 09:10 on the owner's word, all of it on the Pi:

  * **Agent `ledmatrix`** created (15 agents now), sonnet-5 with an opus-4-8
    fallback like the others, and the MCP server is scoped to exactly that id.
    Config backed up and diffed each time: nothing outside the agent list moved.
  * **Its brief** is `~/.openclaw/agents/ledmatrix/workspace/AGENTS.md` - what
    it must not do (flash anything, invent a panel name, change what is on
    screen without reason), what the hardware will teach it the hard way
    otherwise, and that the panel hangs on a wall in a room where somebody
    lives.
  * **The launcher moved out of the clone** to `~/ledmatrix-run/`, so
    `git pull` can never argue with our own files and the clone stays something
    you can delete and remake. The clone was also unshallowed, because a
    rollback needs history to roll back to.
  * **Nightly update at 03:40**, `~/ledmatrix-run/update.sh`. It pulls, then
    **starts the server and counts its tools** - the only check that means
    anything, since whether an agent gets its tools is the question, not
    whether the files parse. If that fails it resets the clone to the previous
    commit and verifies *that* too, and reports through the fleet's own
    `mq.py` to the owner's Telegram. It is silent when nothing changed, because
    a message every night for no news is one nobody reads by the third week.
    Exercised on the spot: "no change (be67df1)".

**One step still needs a person:** `sudo apt install avahi-utils`, which needs
a password. Until then the SDK works by name rather than by discovery, which
is what the fallback added this morning is for.

One operational note for next time: `nickol.local` stopped resolving from the
Mac mid-session and an SSH command silently did nothing. Nothing was half-done
- the connection failed before it ran, and the config was checked afterwards to
prove it. The Pi is 192.168.4.37.

### What the Pi taught the SDK

It reported "no panels found on this network" while the panel answered
perfectly well by name - and that was the worst kind of wrong, because it had
not looked. Raspberry Pi OS runs `avahi-daemon`, so glibc resolves `.local`
through nss-mdns, but it does not install `avahi-utils`, where `avahi-browse`
lives. Browsing for services and resolving a name are different abilities and
the SDK had conflated them.

`can_browse()` now separates "searched and found nothing" from "could not
search", and says which apt package and which env var. `by_name()` resolves one
panel through `socket.getaddrinfo` and confirms it by asking `/api/info`, and
`resolve()` falls back to it - so the SDK works on a box with no avahi-utils
and no sudo, which is exactly the box it was being handed to.

## 2026-09-22 (to 01:04): our own flasher, twelve slots, a planted aquarium — and three tools caught lying

Everything below is on `main` in both repositories and pushed. The panel is on
firmware built tonight, flashed **over the air**, showing AQUARIUM at 15 fps
with the screen on and night mode off.

### What the panel has now

    12 upload slots (was 4), 50 KB a script (was 24 KB) — needs the flash it got
    5 slots used: aquarium 31.4 KB, pb_ferrari, pb_red_hat, red_hat, starship
    brightness 70%, scheduled power off DISABLED (see below), carousel off
    LittleFS 20.3 MB free, internal heap ~20 KB, largest block ~11 KB

### The four things worth remembering

**1. We have our own web flasher.** `pixelclock.stolaris.dev` is the *upstream
author's* domain — it resolves to `keralots.github.io`, and `docs/CNAME` in our
fork carried it as a fork artifact. Removed; GitHub Pages enabled on our own
repo at **<https://nickoscope.github.io/AnimatedPixelClock/>**, serving three
boards with the Waveshare RGB-Matrix as the default. Before this, a person with
our board would have picked the nearest button — the 16 MB WROOM image — and
got a board that installs cleanly and then dies in `do_core_init` on every
boot. `release.py` builds all three and its bootloader-header check is what
would catch a mislabelled image at packaging rather than on a wall.

**2. More colour is the wrong thing to spend bytes on, and the panel says so.**
A photograph at 24-bit colour and the same one at 256 dithered colours are
plainly different in a PNG and **indistinguishable on the panel**. The owner
looked and said so; the hardware agrees. The panel has no colour depth of its
own — FM6124 drivers are constant-current sources behind a latch, a LED is on
or off — all greyscale is the ESP32 library's BCM where **every extra bit
halves the refresh**, its own `doc/BuildOptions.md` says 24-bit at 64x64 and up
either flickers or loses the shadows, and a CIE 1931 table then folds each
channel's 256 inputs onto **174 distinct outputs**. The rule that came out of
it — *spend the budget on TIME, not colour* — is in `effect_api` and in
AGENTS.md §9 with the derivation and with what to spend it on instead.

**3. Uploading over the running effect did nothing until tonight.** Replace the
script behind the effect on screen and the old compiled chunk kept running
until you left the page and came back. `luaEffectsSelect` returns early when
the index has not changed, which is right for a knob and wrong for an upload:
the file moved under an index that did not. `luaEffectsReload()` bumps the
sequence word the effect task keys its reload off. Proved by uploading a copy
of the aquarium whose only difference was `FPS = 6` and watching the panel go
from 14 to 6 with no page change.

**4. Three tools were measuring against remembered constants.** `validate.py`
cached its host binary against the `.cpp`'s mtime while every limit it enforces
is a `#define` in the **header**, so raising the cap left it rejecting scripts
by the old number. `photo_to_lua.py` printed "N% of the panel's limit" against
a hard-coded 24576. And `photo_to_lua.py` resized straight to 128x64, squashing
a 1007x1078 portrait **2.14x flat** — invisible in a thumbnail, obvious on a
wall. All three fixed; the first two now read the firmware.

### AQUARIUM

`gallery/aquarium.lua`, 31.4 KB of the 50 KB a script may be, 12-15 fps.

Seven species over a **continuous depth**: each fish carries a depth from 0 at
the back glass to 1 at the front, drifting on its own 20-40 s cycle, which
picks its body from five precomputed sizes, sets the haze, sets the apparent
speed and decides what is drawn over what. A turn is a turn — `face` crosses
zero over a third of a second while the body foreshortens.

Two corrections from the owner that are now rules in the file: **the room
nudges a heading, it never tows a fish** (making the person the target dragged
the whole tank after them like iron filings), and **there is glass on all four
sides** — an aquarium is not a window on the sea.

It reads the room through `presence`, the same MTR-1 feed over MQTT that ROOM
RADAR draws, with every reaction damped in *seconds*: six to turn toward
somebody, one and a half to scatter, thirty to settle, forty-five of an empty
room before it sleeps.

### What is owed

**D11, sound for Lua effects** — registered tonight in
[22 §12.3](docs/22-audio-visualizer-onboard-mic.md) with the rest, written up
in full in [34-lua-sound.md](docs/34-lua-sound.md). Nothing built.
**Start at Q1: is there a speaker on the board at all, or only a pad.** A
negative answer there makes the rest of the document moot. It also sits
downstream of D1 and D2, because it needs TX DMA buffers in the internal heap
that is already the binding constraint.

### The flasher works — the owner installed a board from it

**It was flashed end to end, from the page, on 2026-09-21 night.** The owner
did it and said so at 01:08. I had written "nobody has installed a board from
that page" as a fact when it was only something I had not seen; the record is
corrected, and the lesson is the wording - *not observed here* is not *did not
happen*, and the person with the hardware sees more than the logs do.

Everything I could check without a cable was checked and passed: the page serves, `VERSION` reads v2.5.0, the
image downloads at 2,373,392 B with a SHA-256 matching the published checksum
exactly, the ESP Web Tools manifest points at our file at offset 0x0 with
chipFamily ESP32-S3, and the image's own header reads magic 0xE9, chip id 9,
32 MB flash, with an application at 0x10000. `release.py`'s checks passed too:
the bootloader header's flash size matches the board, both OTA slots sit at the
expected offsets and the firmware fits them. The rest - the cable, the port
dialog, Install - was the owner's, and it worked.

**He picked the Waveshare entry, and the Improv "Configure WiFi" step worked.**
That is the whole path proven, and it is the strongest of the three it could
have been:

  * The Waveshare entry is the one that did not exist before tonight. Its
    `matrix-waveshare-rgb` merged image had never been written to a board - the
    panel's own flashes were app-only OTAs, which never touch the bootloader or
    the partition table.
  * **It booted.** That is the `opi_opi` question answered by the hardware.
    The failure mode that made this entry worth building - a quad-flash image
    on a WROOM-2 module installing cleanly and then dying in `do_core_init`
    every boot, which cost us 2026-09-14 - did not happen, so the octal
    bootloader and the 32 MB flash size in the published header are right.
  * **Improv carried the credentials over USB in the same dialog**, so the
    `new_install_improv_wait_time: 15` in the generated manifest and the
    firmware's first-boot Improv window line up. No access point, no captive
    portal, no app switching.

Page, manifest, images, bootloader, partition table and provisioning: all of it
is now proven on hardware rather than verified on paper.

**And the published image is two firmware changes behind main.** It was
packaged at 23:06; `a4d8004` (twelve slots, 50 KB a script) landed at 00:09 and
`e3d99e1` (reload the running effect on upload) at 01:02. So a board installed
from the page today would come up with four slots, a 24 KB cap and the upload
bug — **while calling itself v2.5.0, exactly like the panel, whose bytes are
different.** The same version on two different binaries is the part that will
mislead somebody.

### It cannot fall behind quietly again

The page had come to serve bytes built at 23:06 while main had moved twice, and
to call all of it v2.5.0 - which is also what the panel called its different
bytes. Asked whether to fix it now or tomorrow, the owner's answer was the
right one: **this should not be a thing anyone remembers.**

So it is a hook, in the house pattern. `release.py` stamps
`docs/firmware/latest/SOURCE.sha` with the version it packaged *and* a hash of
everything that can change a binary - `src/`, `platformio.ini`, the partition
tables it names. `tools/firmware_stamp.py --check` compares that against the
tree whenever a commit touches those files:

  * it **fails** when the sources have moved while `FIRMWARE_VERSION` has not,
    because that is the actual defect - two binaries under one name, and a
    person comparing versions being told they match when they do not;
  * it only **notes** that the page is behind, because lagging is normal
    between a change and a release, and a hook that demands a three-board
    build on every commit is a hook people switch off.

Both paths were exercised, not assumed: stamped, it exits 0; append one line to
a header and it exits 1 with the message.

**v2.5.1 is published and live.** All three boards rebuilt, the v2.5.0 images
removed (the page only ever serves what `VERSION` names), and checked on the
live site: it reports v2.5.1, the Waveshare image downloads at 2,373,568 B and
its SHA-256 matches the published checksum.

### The panel finished the night on v2.5.1, with night mode back on

Flashed over the air at 01:19, `app0 -> app1`, waited for `ota.state` to read
`valid` before touching anything. Night mode was restored by the same
procedure as turning it off: all 122 form fields snapshotted, all sent, diffed
after - exactly one changed, `enableScheduledOff` False -> True. The window is
00:00-06:00, so the screen went dark within the minute, which is what was
wanted. Link counters clean: `linkBlindS 0`, `linkRecoveries 0`,
`allocFails 0`, ~18 KB internal free.

**One thing to look at with fresh eyes.** When I went to flash at 01:17 the
panel had an uptime of 43 s - it had restarted on its own about fourteen
minutes after the 01:03 boot, with `resetReason 3` (software reset). Nothing
crashed: the `lastCrash` record on the panel is from 2026-09-21 11:12 and
reports `sameFirmware: false`, `thisBoot: false`, so it belongs to an older
image and not to this. A software reset roughly fifteen minutes after a boot
is suspiciously close to `NET_BLIND_REBOOT_MS` (900 000 ms) in
`src/network/network.cpp`, but the panel was answering HTTP throughout that
window, so if that watchdog fired it fired on something other than HTTP
reachability. Worth one look; not worth a theory tonight.

### Two things left open

- **Night mode is off.** The window was 00:00-06:00 and the screen went dark at
  midnight. There is no narrow API for it, so it went through `/save` — the
  whole-form replace that silently clears every boolean it does not carry. All
  122 fields were snapshotted first and diffed after: exactly one changed.
  Turning it back on is the same procedure. The separate *dimming* schedule
  (22:00-07:00 down to brightness 11) was not touched.
- **`/api/log` could not be read reliably.** `?clear` did not appear to clear
  and paging by `from`/`X-Log-Seq` returned stale windows, so the panel's own
  30-second effect reports were never captured tonight. Frame rates here are
  from `/api/panel`'s `hz` with the panel left alone — polling it steals core 0
  from the effect and makes it read 4-5 fps, which is a measurement disturbing
  the thing it measures.

## 2026-09-21 (afternoon): the panel gets a name, an SDK and an MCP server — and then drops off the network

Branch `feat/net-broker` in the fork, pushed. Nothing was flashed.

### Where it stands right now

**The panel has been off the network since about 14:50 CEST.** It answers
neither HTTP nor ping, and its MAC `90:E5:B1:D2:0E:C8` is not in the ARP table
anywhere on 192.168.4.0/24. The gateway is up and every other device on the
subnet is reachable, so this is the panel and not the access point. The link
watchdog has not brought it back in 25 minutes.

The last reading it gave, at 14:46, through the new `panel_health` tool:

    largestHeapBlock 8692   freeInternalHeap 19496   minFreeHeap 972
    allocFails 109 (task wifi)   webRefused 4   wifiFailAgeS 918
    linkRecoveries 2   lastLinkRecovery "gateway unreachable"
    uptime 3249 s   loopMaxMs 7

`linkRecoveries: 2` with "gateway unreachable" says the watchdog had already
rescued the link twice in that boot, and the last time was fifteen minutes
before the heavy testing began. So the trouble did not start with the test
traffic — but the test traffic was heavy (a full MCP sweep, a live doc-29
verification and discovery every 30 s), and that share is not being disclaimed.

**It needs a power cycle, which is a person's job.** Nothing here reflashes a
wall-mounted panel.

### Closed the same day: merged to main, and the fix is on the panel

**`main` carries it all.** `feat/net-broker` was a strict superset of `main` —
241 commits ahead, 0 behind — so it went in by fast-forward and was pushed.
Anyone, or any agent, arriving at `github.com/NickoScope/AnimatedPixelClock`
now lands on `AGENTS.md` instead of a repository with no map. Before merging,
the diff was scanned for secrets: every hit was the provisioning *mechanism*
(templates, gitignored file names, the literal string `"mqtt-password"`), and
the apparent list of MAC addresses was the hex of the TLS root fingerprints in
`rtt_roots.h` and `aero_roots.h`. Two things worth knowing rather than fixing:
the panel's own MAC stands as the worked example for `--mac` in three files,
and `192.168.4.35` — the AppDaemon host — appears in five example configs. Both
were already public on the branch; the merge exposed nothing new.

**The watchdog fix is running on the panel**, flashed over the air at 18:50
because the USB cable is off the wall. 2,289,600 B into 4,718,592 B free,
checked on paper first; 86 seconds to upload; booted from `app1` with
`resetReason` 3, and `ota.state` reached `valid` at the 60-second mark before
anything else was done to it. `linkBlindS` reads 0 in `/api/info`, which is the
new field doing its job. After it: `linkRecoveries 0`, `allocFails 0`,
`webRefused 0`, largest block 12,276, weather in, clock synced.

**The SDK was driven end to end**, not just the panel half of it: a Lua effect
written through `effect_write` (the schema refused `bad-name` and the tool
refused a script with no `draw()`), rendered through `effect_preview`, and the
frame looked right — ring, hand, glow, and `14:37` from the simulator's
`--start`. The test script was removed afterwards rather than left to change
`LUA_EFFECT_COUNT`.

**Still not verified, and saying so:**

- `evaluation.xml` for the MCP server is not written. The house pattern wants
  read-only question-and-answer pairs taken from live hardware.
- `bringup.py`'s switch-off branch has been exercised across four cases of its
  decision table but never against a panel that genuinely has no broker.
- `effect_check` (`fx_parity.py`) was not run through the MCP tool; it needs a
  full PlatformIO build first and takes minutes.
- The blind timer cannot be proven in the field without reproducing the Wi-Fi
  task's buffer starvation. What can be said is that the field it exposes is
  live and reads 0, and that the arithmetic and the code path are right.
- The flight board has still never fetched through the broker.

### Why the watchdog did not save it — CONFIRMED after the power cycle

**Confirmed 2026-09-21 18:20, from the panel itself after the owner pulled the
power.** Three readings settle it:

- **`resetReason` is 1, `ESP_RST_POWERON`.** The firmware's own portal maps 1 to
  "Power on" and 3 to "Software restart" (`web_pages.h:2004`). `netRecover()`'s
  last resort calls `ESP.restart()`, which gives 3. **It gave 1.** So in more
  than an hour unreachable, the six-minute reboot backstop never fired once.
- **`lastCrash.thisBoot` is false**, and the stored record is from 11:12 today
  with `sameFirmware: false` — an earlier build of this morning, superseded by
  the 12:25 one. Nothing crashed during the outage.
- **The loop task was running the whole time.** `main.cpp:592-593` subscribes it
  to the task watchdog with a 15-second timeout and panic enabled, and
  `main.cpp:996` feeds it every pass. Had `loop()` hung for fifteen seconds the
  board would have panicked and come back with `resetReason` 6. It did not.

So the panel was alive, looping, feeding its watchdog and almost certainly still
drawing the clock on the wall — and `netHealthTick()` ran some thousands of
times across that hour without ever deciding the link was bad. That is the blind
spot below, and this is no longer a hypothesis.

### The blind spot, with line numbers

Read out of `src/network/network.cpp` while waiting, and it fits every number
the panel last gave.

The link watchdog has a last resort: `netRecover()` reboots the board if the
link has stayed bad for `NET_REBOOT_AFTER_MS` = 6 minutes
(`network.cpp:405-413`). **That backstop is armed by `netBadSinceMs`, which is
set only inside `netRecover()` itself.** So nothing reboots unless something
first decides the link is bad.

Two paths through `netHealthTick()` decide nothing at all, and both are the
paths a memory-starved panel takes:

1. **`netStartProbe()` cannot create the ping session** (`network.cpp:395-398`).
   It needs a 3,072-byte task stack plus the session struct. Under pressure
   `esp_ping_new_session` fails, the function returns false, and the tick simply
   returns. Nothing counted, nothing armed.
2. **The session exists but nothing left the board** — `sent == 0`, the branch
   at `network.cpp:454-462`. This one is deliberate and the comment explains
   why: on 2026-09-20 the watchdog counted "ping_sock: send error=0" as
   *gateway unreachable*, restarted a Wi-Fi link that was working, and became
   the outage it exists to prevent. The root cause was on the line above it in
   the log — the Wi-Fi task could not get its **1,626 B** buffer.

That reasoning is right as far as it goes. But it stopped one step short: the
branch declines to blame the gateway **and** declines to arm any backstop. A
panel whose Wi-Fi task cannot get a buffer therefore cannot probe, cannot count
a failure, cannot recover and cannot reboot — it just sits there, unreachable,
for as long as the power is on.

The last reading before it vanished says exactly that state:

    allocFails 109   allocFailBytes 1626   allocFailTask "wifi"
    largestHeapBlock 8692

1,626 bytes is the same figure as in the comment, and it is also the web
back-off threshold. Not proof — that needs the serial log — but the hypothesis
has a line number and the arithmetic agrees.

**The shape of a fix, not to be written without the owner.** Keep refusing to
blame the gateway; add a separate, slower backstop on the state itself: nothing
has reached this panel from outside in N minutes *and* it cannot even raise a
probe. In that state the device is useless to everyone regardless of whose fault
it is, and a reboot cannot make it worse. N wants to be generous — fifteen
minutes, not six — precisely because this path has already caused one outage by
acting too eagerly. This is also directly relevant to PR 7 upstream, which is
the link watchdog.

### What was built

- **The panel is now `NickoSha-64x128`.** Each panel gets its own name; the MAC
  is what identifies it. The configuration portal did *not* take the new name —
  it saved, rebooted, and came back unchanged — so it went through
  `POST /api/rename`, which writes NVS and restarts mDNS with no reboot. All
  other settings were checked afterwards and are intact.
- **`tools/agent/bringup.py`** — bringing a new panel to life. Without `--name`
  it **asks for one and exits 3**; it will not invent a name. Then it probes
  MQTT and switches off only the pages that have no source without Home
  Assistant: cards, media and the four market pages are MQTT-only; flights and
  trains are left alone when they hold a direct API key of their own; yachts,
  the clock, the world clock, the Lua effects and the indoor sensor never needed
  Home Assistant at all. The decision table was exercised across four cases.
- **`tools/agent/mcp_server.py`** — eighteen MCP tools over stdio, with
  `panel.py` as the transport. Works from any machine against any panel; every
  tool takes an optional `panel` (MAC, name or address), and with several on the
  network it lists them and asks rather than guessing. Driving, debugging, and
  the whole effect-writing loop. **No flashing tool, and there will not be one.**
- **`AGENTS.md`** gained the "bringing a new panel to life" section (the name,
  the no-Home-Assistant case, and the rule that configuration lives in the
  user's own fork while issues and PRs come back upstream) and a finished
  section 8 on adding a screen, both routes, written from a source survey that
  was re-verified line by line before anything was written down.

### Two real faults found by testing, not by reading

- **`discover.py` treated any HTTP error as "not there".** A panel answering 503
  is unambiguously present — 503 is its designed back-off — yet it vanished from
  the list at exactly the moment it was being used. Fixed: an answer is an
  answer, marked busy.
- **On macOS, Local Network access is granted per binary.** A Python that an MCP
  client launches can be denied it while identical code from a terminal works.
  It does not look like a denial: a `192.168.x.x` address gives
  `[Errno 65] No route to host` **instantly**, which reads exactly like a panel
  that is switched off. Measured: under `uv run python`, example.com answered in
  0.54 s and the panel's own IP gave Errno 65 in 0.00 s; the system Python
  reached both. mDNS still works under `uv` because it shells out to `dns-sd`,
  so the panel is found and then appears dead. `panel.py` now tells the two
  apart and says which; register the server with a venv, not with `uv run`.

### Documents caught stating numbers the source contradicts

Three in one afternoon, which is the whole argument for reading the handler
rather than the prose:

- **`docs/29-panel-control-map.md`** — five errors, all fixed. The headline
  instruction `POST /api/panel {"showPage":N}` does nothing at all and answers
  200; brightness is a percent, not 0..255; `/api/fx3d` is 404 on the shipping
  build; the clock style ids are not a contiguous range (4 and 13 do not exist);
  and the route table was missing `/api/rename`'s rules and `/api/railboard`'s
  `favourites` entirely.
- **`AGENTS.md` §2.e** described fx3d as a working screen. 404, confirmed
  against the panel.
- **`src/lua/README.md`** claimed a 16 KB Lua task stack where `kStackBytes` is
  `12 * 1024`, and listed four effects where `LUA_EFFECT_COUNT` is 6.

### Next

1. **The panel.** Power-cycle it, then read `/api/info` for `resetReason` and
   `linkRecoveries`. "gateway unreachable" twice in one boot before any load is
   the thread worth pulling.
2. **`evaluation.xml` for the MCP server** — the house pattern wants read-only
   question-and-answer pairs taken from live hardware, and there is no live
   hardware right now.
3. **The flight board has still never fetched through the broker.** It was at
   its daily API cap; its path and its 192 KB mailbox are inherited, not
   measured.
4. Rail behaviour on HTTP 429 and at daily-budget exhaustion; a station change
   *during* a fetch sequence; the 30→10 minute history cut against real delays.

## 2026-09-21: the network broker lands, and one portal visit stops killing the panel

Integration session, branch `feat/net-broker`, running on the panel by the
owner's instruction.

### What was done

- **All four network consumers moved onto one broker.** Weather, world clock,
  rail board, flight board. **No module creates a fetch task at run time any
  more.** One 10 KB stack in `.bss` replaces four run-time allocations of
  8-13 KB, and the demand for a *contiguous* internal block at a moment nobody
  chose - which is what was actually taking the panel off the network - is gone.
- **Built to NickoScope32's NetGate design** (v1B Main-S3 v33.64.0, ADD-62),
  read from its source at the owner's direction: one permanent worker task, a
  TLS client built per request and destroyed *before* the answer is published,
  the body copied into a per-caller PSRAM mailbox and published by bumping a
  `seq`, the parse on the loop task. The broker never runs consumer code, which
  is what makes its stack a knowable quantity. What was deliberately **not**
  taken - its queue costs ~12 KB of internal RAM copying job structs by value -
  and what copying it cost us, is in `docs/32-net-broker.md`.
- **The rail board stopped downloading half an hour of history.** It was
  fetching 110 services and 120,619 B to fill eight rows. The request now asks
  for 10 minutes of past instead of 30; the forward reach is untouched at 60
  minutes, because that is what decides whether a quiet station can fill the
  board at all.
- **Two operator tools**, `tools/nsc/`: `nsc.py` (one JSON object per command,
  meaningful exit codes, every state change verified by reading it back) and
  `functional.py` (the control map as an executable sweep). `docs/33-one-cli-json.md`
  explains the shape, and is honest that JSON alone would not have prevented the
  estate's famous "counter instead of effect number" bug.
- **Four audit rounds**, every finding closed.

### What was verified, and how

- **The complaint itself, reproduced before it was fixed.** One portal visit -
  six concurrent requests, the way a browser opens it - against both builds,
  fresh boot, same script (`scratchpad/visit.py`).
- **Seven boots of each build**, one reading each at a fixed point, nothing
  driven between (`scratchpad/paired.py`). Not single readings: the method
  itself had been wrong for two days, see below.
- **Deliberate abuse:** 250 requests, ten at a time, every two seconds for a
  hundred seconds, with the rail board fetching 93 KB through it
  (`scratchpad/stress.py`).
- **A functional sweep of everything doc 29 lists** (`tools/nsc/functional.py`):
  all 16 pages set *and confirmed by reading the state back*, seven clock
  styles, all five boards' data, the weather, the portal's six assets, four
  diagnostics routes, and the link-recovery and crash counters compared before
  and after.
- **Stack frames measured from the object file**, not estimated, the way the
  audit measured them.
- **Every new host test broken on purpose** to confirm it could fail.

### Results

| | `fix/panel-tonight` (was on the wall) | `feat/net-broker` |
|---|---|---|
| One portal visit | every asset served, **then the panel died** and needed a reflash | every asset served, **panel kept working** |
| Link recoveries during that | n/a - it was gone | **0** |
| Under 250-request abuse | not attempted | 88 served, 162 refused by design, **0 link recoveries, never needed a reset** |
| Functional sweep | - | **41 checks, all passed** |
| Free internal heap | ~34,500 B | ~19,000-23,000 B |
| Largest contiguous block | 16,372-24,564 (median 23,540) | 8,692-14,836 (median 13,812) |
| Rail body | 120,619 B | **85,677 B** |
| Broker stack use | - | 5,780 B of 10,240 measured worst |

**The memory numbers got worse and the panel stopped dying.** Both are true.
What killed it was never the quantity of free RAM - it was four modules each
demanding 8-13 KB of it contiguous, at unchosen moments, while a browser held
six connections open. The broker does not make the heap bigger. It removes the
demand.

### Three things worth remembering that are not about code

1. **A measurement method was wrong for two days.** `largestHeapBlock` does not
   decay over hours - it is identical to the byte within one boot and varies
   *between* boots, in 1,024-byte steps, with one boot in seven landing 6 KB
   low. Every "before and after" in this project built from single readings was
   therefore worthless, including several of mine.
2. **Three verifications that could not fail, all found the same day** - a
   documented payload key that was wrong (`{"styleId"}` answers HTTP 200 and
   does nothing; it is `{"style"}`), a host test whose sweep stopped exactly at
   the precondition so the one dangerous input was never offered, and an exit
   code taken from `head` instead of from the test. All three surfaced only
   because each was broken deliberately to see whether it would notice.
3. **A borrowed design carries its own mitigations, and they do not come across
   in the code you copy.** Two MAJOR findings were in code taken verbatim from
   NetGate. Its unbounded read is safe *there* because `netTask` carries a 30 s
   watchdog that restarts the chip - three files away from what I copied.

### Later the same day, after the migration landed

- **The knob picks the station.** Click walks LISTS -> STATION -> out, a turn in
  STATION changes the station at once and reaches the broker as an interactive
  request. It follows the media and market pages rather than inventing a long
  press, which this firmware folds into a click on purpose. The list is data in
  NVS - up to eight, `POST /api/railboard {"favourites":[...]}` - because the
  portal's station controls were removed on the owner's instruction and this
  replaces them. **His five: GLD, WAT, CLJ, WOK, SUR.** Verified end to end over
  the serial knob console, reading the station back after every step.
- **`-fstack-usage` is on**, our sources only (in the libraries it is eight
  permanent "unbounded" warnings from variable-length arrays, and permanent
  warnings are how a real one gets skimmed). `-Wstack-usage=2048` is a ratchet
  set from the distribution - 9,407 functions, median 32 B, 99th percentile 256,
  worst 2,000 - so it warns about nothing today and about anything worse than
  anything we have ever had. `tools/nsc/stackreport.py` prints the list.
- **The indoor sensor reads its own heat.** 32.3 C against a room at 24, so a
  -8.7 C offset, set through the portal. One point of calibration, not a model:
  it tracks screen brightness and will be wrong at night. Recorded in doc 29
  because it lives only in NVS.
- **PR 7 sent to Keralots**: https://github.com/Keralots/AnimatedPixelClock/pull/10
  The first one upstream that fixes a bug in his code rather than offering ours -
  the link watchdog restarting Wi-Fi over a probe the driver never sent. Also the
  first without the Claude Code attribution line, on the owner's instruction.
- **MicroPixel**: not forked and not cloned - read through the API, and watched
  by two files (`tools/manager/micropixel_manager.py`, `AGENTS.md`) plus releases.
  What was taken and what it caught is `docs/33-one-cli-json.md`; the delta was
  written back into the NickoScope32 v1b project's own HANDOFF, where that
  session had already proposed the same CLI and was waiting on the owner's word.
- **Doc 29 carried three false claims**, all found in one day: `{"showPage":N}`,
  `{"styleId":N}` (both answer HTTP 200 and do nothing), and "the serial knob
  console does nothing" - it works, and the whole station picker was verified
  with it. The document was written to be read by a person and there was nothing
  that could check it. Now there is: `tools/nsc/functional.py`, 41 checks.

### Not done, and it matters

**The flight board has never once fetched through the broker.** It was at its
daily API cap all day, so its broker path and its 192 KB mailbox are
**inherited from its old buffer, not measured**. Until it has fetched, this is
not finished.

### Next, in order

1. The flight board, when the daily cap rolls over.
2. Rail behaviour on HTTP 429 and at daily-budget exhaustion - two of today's
   three MAJOR findings lived exactly there.
3. A station change *during* a fetch sequence (the two-step token flow).
4. The 30->10 minute history cut against real delays: a thrice-delayed train now
   leaves the board where it used to stay. Only a live timetable shows this.
5. `-fstack-usage` in `platformio.ini`. NickoScope32 enforces stack frames at
   build time; we have it in no environment, and it is what catches an oversized
   stack before a flash rather than after one.

### Open debts, unchanged

The radio's `allocFails` climb under load (task `wifi`, 1,626 B DMA buffers) -
nothing fails visibly and the link holds, but the shortage is real and its cause
is the 131 KB HUB75 framebuffer, which cannot move to PSRAM (tried 2026-09-14:
stripes and TLS failures) and whose colour depth the owner has ruled out cutting.
Yacht radar's 17.5 KB outside the lock; MQTT's blocking connect; OTA not taking
the lock; station and airport selection still to move onto the knob.

## 2026-09-20, night: the network broker is built and audited, and the panel rejected it (integration session, `feat/net-broker`)

- **Done:** `feat/net-broker` `21e6adc`, pushed. One task owns the outbound socket, with its
  stack in `.bss` - confirmed in the map at 12,288 B, 0x3fca52f0, internal DRAM, 16-aligned - so
  it is taken at link time and can neither fail to be allocated at the worst moment nor leave a
  hole when a fetch ends. The queue (`src/net/nb_queue.h`) is a pure model with a host test:
  27 checks, 0 failed, at c++11 and c++17 under ASan/UBSan. Weather migrated as the first
  consumer. Two audit rounds: **APPROVED**, no BLOCKER, no MAJOR, clean rebuild 0 warnings,
  cppcheck 0 defects, gitleaks clean.
- **And then the panel said no.** Flashed over the cable and measured against the known-good
  build minutes apart on the same board: largest contiguous internal block **16,372 B before,
  9,716 B after**. The flight board refuses to fetch below 13,312 B, the rail board below
  10,240. It is the `net_reserve` mistake again - take a large contiguous block at boot and the
  modules that still need one starve - and it is inherent to migrating one consumer at a time,
  because that whole window is *after* the 12 KB is gone and *before* the three thresholds are.
  Panel returned to `fix/panel-tonight` the same minute; rail board verified working after
  (London Waterloo, synced, three trains).
- **Also learned:** `served` stayed 0 - the broker was never asked, with the weather page on
  screen and the settings good. Cause not known, and not guessed at. Separately, weather was the
  wrong first consumer: it has reported `weatherValid:false` on this panel for days, on the old
  firmware too, so it could not have validated anything. The doc's criterion ("least visible if
  it breaks") should have been "actually fetches today".
- **Next, in order:** (1) turn the remote log on (`/api/log?on=1`) and find out why weather never
  submitted - read it, do not reason about it; (2) get one real `stackFreeMin` reading and size
  the broker's stack from it instead of from the largest of the four - 12 KB is unmeasured, and
  the rail board's own task used 6,152 B of 12,288, so ~6 KB may return enough contiguity on its
  own; (3) then either land all four consumers together or confirm the smaller stack keeps every
  un-migrated threshold satisfied. Nothing goes on the panel until the arithmetic is checked
  first, on paper, against `largestHeapBlock`.
- **Open debts unchanged:** yacht radar 17.5 KB outside the lock; MQTT blocking connect; OTA not
  taking the lock; `rttDirectOnScreen` deriving "on screen" from a render timestamp; station and
  airport selection still to move onto the knob; the redundant `WiFi.begin()` on a genuine
  disconnect.

## 2026-09-20, morning: the glasses profile, and everything on the panel at 30 Hz but the blobs (feature session, `feat/fx3d`)

- **Done:** `feat/fx3d` `26a1be4`. The glasses profile lives in NVS (namespace `fx3d`, one
  typed key per value, described in [27](docs/27-fx3d.md)): the owner's calibration survives a
  reboot, a write costs under 10 ms of `loop()`, and reading never refuses - a missing, foreign
  or out-of-range key costs that value's default, never the boot. Then the looks card and drum
  and the four heavy scenes, on the panel's own numbers: drum 2.0x and card 1.7x; tunnel 5.5x,
  globe 3.9x, the landscape 2.5x with its map opening in 258 ms instead of 452; blobs 1.25x and
  more since. In mono every scene but the blobs holds 30 Hz; with the glasses every scene but
  the blobs and the landscape; seven looks of eight.
- **What made the difference, and it is the project's to keep:** on this firmware the S3's FPU
  adds, multiplies, compares and converts inline, and nothing else. A float division calls
  `__divsf3` in ROM (69 cycles, Espressif's own measurement), `sqrtf`, `floorf`, `ceilf`,
  `sinf`, `cosf`, `atan2f` and `asinf` are newlib calls, and `x / 255.0f` is a call too. The
  table with the sources is in `src/fx3d/README.md`, "What floats cost on the S3"; the row in
  [27](docs/27-fx3d.md) points at it. Every scene was made cheap by taking those out of the
  per-pixel loops - tables where the geometry does not change, reciprocals worked out once,
  integer floors - and each one is held to what it drew before by the host test, which keeps
  the old code verbatim.
- **Checked:** 140,293 host checks, 0 failed (C++11 and C++17, ASan/UBSan); the `/fx3d` page's
  request queue runs in JavaScriptCore, 26 checks, with five broken queues as the controls;
  three audits, all APPROVED with no blocker or major, their findings answered; flag off
  byte-identical; the bench env and the two flag-matrix rows build.
- **Waiting for the owner:** the session with the glasses has not happened. Two things wait on
  him: where the chosen scenes and looks go, and whether the blobs may change to hold 30 Hz
  with the glasses (fewer rays, or a march that carries on from the last frame). Everything
  that could be made cheaper without changing a pixel is done.
- **Lesson, paid for twice:** the Mac is not the panel. It said the drum was 3.6x and the card
  about even; the panel said 2.0x and 1.7x. It says the globe's table would be bound by PSRAM;
  the panel says the gain is the same in both modes. Time the change on the panel, or say it is
  not measured.

## 2026-09-18, evening: 3D on the panel, measured and three times faster (feature session, `feat/fx3d`)

- **Done:** `feat/fx3d` `80eb788` is on the panel (OTA, by the integration session). Three
  rounds of measure-and-fix on the panel's own numbers: the blit writes runs of one colour
  (14.3 ms -> 6.3-9.7); blobs march a ray per 2 x 2 (111.8 -> 41.7 ms mono); the landscape
  opens in 0.45 s instead of 1.08; the looks lost a per-frame linear copy of the page and relief
  writes bytes directly - six of eight looks now hold 30 Hz, none did before. Every change is
  host-tested (138,454 checks), the glasses looks byte-for-byte against the old walk; flag off
  byte-identical to the branch's base; four audits APPROVED.
- **Left, by price:** card 46 ms and drum 31.5 ms a frame; heavy scenes in red-blue (blobs 82,
  globe 88, tunnel 69, voxel 62 ms), which also dip the largest free internal block to 14.8 KB
  while they run (hypothesis: the network queues under a slow loop - a 30 s no-request check is
  proposed in the coordination record); the landscape's 0.45 s open; the glasses profile in NVS.
- **Next step:** the owner's word. He last spoke at 15:44 («все, но нужно смотреть с очками»);
  whether the glasses session happened is not known here. Ask what matters more: faster heavy
  scenes, or the profile kept across reboots.

## 2026-09-18, afternoon: 3D on the panel (feature session, `feat/fx3d`)

- **Where:** worktree `/Users/apple/AnimatedPixelClock-fx3d`, branch `feat/fx3d` `264d6f1`,
  module `src/fx3d/` behind `-DFX3D_ENABLED`; everything in [27](docs/27-fx3d.md).
- **Done:** two layers on one model - 14 scenes (the training ground, the brief's anaglyph MVP
  first) and 8 looks that show any page in 3D without touching it (the owner, 15:22), both mono
  and red-blue; the capture of any page's frame; `/api/fx3d`; the owner's remote at `/fx3d`;
  a bench on demand. Host 132,413 checks; flag off byte-identical to the branch's base with a
  fixed build date; two audits APPROVED (0 blocker, 0 major), their findings fixed.
- **Unfinished:** nothing has run on the panel. Next: the integration session flashes the
  ordinary firmware with the flag once, runs `/api/fx3d?bench=1`, and the owner looks with the
  glasses at `/fx3d` (his words at 15:44: «все, но нужно смотреть с очками»). Then: the profile
  in NVS, the chosen scenes as pages and clock styles, the visualizer's bands into the sound
  hills, and the 30 Hz ceiling under a look revisited with the bench's numbers.
- **Found for the integration session:** `env:matrix-waveshare-rgb-luabench` does not build
  (presence needs the Lua effects it turns off); importing `tools/flag_matrix.py` runs the matrix.

## 2026-09-18, morning: the lighter portal, and how the work is split from here

**Done.**
- **The last item in Keralots' queue is out: PR #9, the lighter portal**
  (https://github.com/Keralots/AnimatedPixelClock/pull/9). The page, the style,
  the script and the icon are gzipped into a generated header by
  `tools/web_assets_gen.py`; the page had to become static for that, so its 232
  `%TOKEN%`s are gone and its values come from a new `/api/portal` keyed by his
  own form control names. `matrix-s3` goes **82.9 % -> 76.1 %**, -133,212 bytes;
  the four assets gzip to 32,965 against the 32,956 he predicted himself.
- **Measured on the panel, both firmwares.** This branch, then his `517b37d`,
  then the fork back: a first load goes from 160,713 B / ~0.47 s to 39,478 B /
  ~0.19 s, and a reload to a 304 with no body. The portal was then driven in a
  browser against the panel's own settings - 57 timezone regions with ours
  selected, 69 colour pickers, 15 rotation rows, no console errors.
- **Both audits earned their keep.** The first found that the generator would
  write CRLF on Windows - and his `upload_port` is `COM9`. The second found a
  blocker: the layout editor was built before the values arrived, so a metric
  outside row mode 0's grid fell back to "None" and the next Save would have
  written that back. Both fixed before the PR was opened.
- **How the work is split from here:** [00](docs/00-how-we-work.md). One
  repository, one worktree per line of work, one session per worktree, and only
  the integration session flashes. `tools/new-feature.sh` starts a feature with
  its worktree, its module behind its own flag, a flag-matrix row and a
  knowledge-base stub.
- **First feature started this way: the 3D effect.** Worktree
  `/Users/apple/AnimatedPixelClock-fx3d`, branch `feat/fx3d`, module `src/fx3d/`
  behind `-DFX3D_ENABLED`, notes in [27](docs/27-fx3d.md). The skeleton builds
  both with the flag and without it; nothing is designed yet - that is the next
  session's first job, and the owner's words go at the top of doc 27.

## 2026-09-17: five upstream PRs, five merged, and the panel's own crash report

**Done.**
- **Upstream: five offered, five merged, not one review comment.** Today's four:
  `bbb861c` the settings `isKey()` fix (PR #5), `9fa9ba4` the weather fetch in a
  task that deletes itself (#6), `eb43f15` the crash report in `/api/info` (#7),
  `517b37d` keeping the crash cause name across a firmware update (#8). Each was
  merged within ten minutes to an hour of being opened. **His release is still
  v2.3.1**, so none of it has reached users yet.
- **The crash report is now one module in both trees.** `src/utils/crash_report.{h,cpp}`
  in the fork is byte for byte the file upstream merged, so a later merge is a
  no-op instead of two modules fighting over the same core dump; `src/health`
  keeps only the OTA rollback. What the fork gained: the dump's checksum is
  checked before it is parsed, `abort()` and the task watchdog are named instead
  of reading as `StoreProhibited` at address 0, `sameFirmware`, sixteen backtrace
  addresses, the dump erased only after the record is saved, and no NVS error on
  a board that never crashed.
- **Verified on the panel, end to end.** A build with a deliberate `abort()` was
  flashed, crashed, and the next boot printed `task loopTask, abort(), pc
  0x40377886, addr 0x00000000, ELF 458f86d0c9eb2166`; `addr2line` resolved the
  five backtrace addresses to `panic_abort`, `esp_system_abort`, `abort`,
  `loop()` and `loopTask`. That test then found the bug behind PR #8: the cause
  name was decided when the JSON was built, so a firmware update lost it.
- **The portal says whose firmware it is.** Bottom of the menu: version, our
  repository, upstream under it. The version pill in the topbar no longer
  disappears on a phone. Flashed over the air; the image confirmed itself as
  valid after 60 s and the unconfirmed one before it was rolled back by the
  bootloader - the rollback path proved itself by accident.
- **The header question is closed with numbers, not drawings.** Owner's meter:
  the pull-up pads at IO45/IO46 are open, and both pins read 10 kΩ to GND.
  `espefuse.py summary` on our own board: `VDD_SPI_FORCE = True`, `VDD_SPI_TIEH = 0`,
  "Flash voltage (VDD_SPI) set to 1.8V by efuse" - so GPIO45's strapping role is
  dead here and a receiver holding that line high at reset is harmless. Told
  Keralots on issue #3, twice (comments 5721338404 and 5721465891), with a
  marked-up photo served from this repository.
- **A study of the playable screens**, `docs/drafts/28-playable-screens-study.md`:
  four screens are already games with the AI holding the controller, the cheapest
  proof is Arkanoid, and the architecture is one guarded hook per screen rather
  than an engine. Seven questions for the owner at the end, two of them
  architectural.

**Judgement.**
- The upstream relationship is now a channel, not an experiment: four changes in
  one evening, each one small, each one with its numbers in the description.
  What he has never done is comment on the code, so the review bar is ours, not
  his - which is exactly why the audits keep earning their keep.
- The hardware test is what found the real bug. Three builds and an audit had
  passed the same code; a deliberate crash on a real board found what none of
  them could.

**2026-09-18, evening (fx3d).** Four rounds on the panel in one evening, each after a clean
audit: `264d6f1`, `3d2a1c5`, `80eb788`, `0f3b2c7` (the last one flashed twice - see below).
Where it ended: **seven of the eight looks hold 30 Hz** (was: none), `card` alone at 26.3.
The glasses profile now survives a reboot - NVS namespace `fx3d`, write under 10 ms, all four
steps verified on the panel. Reports in `docs/drafts/27-fx3d-panel-measurements-*.md`.
Three things learned that outlive fx3d: **overlapping HTTP requests starve the internal heap**
(new debt below, it took the radio down once); **`NickoScope-64x128.local` costs 5 s a request**
on this Mac, so measure by IP; and **after an OTA, wait for `ota.state` = `valid` before any
reboot** - a reboot at 45 s rolled the image back and cost a confusing half hour.
Next from the fx3d session: one image with `tunnel`, `blobs`, `voxel` and `globe` made cheaper.
Waiting on the owner: the glasses.

**Debts, in the order they block things.**
1. **Audio D1** - the portal's ~20 KB internal-heap spike, [22](docs/22-audio-visualizer-onboard-mic.md) §12.3.
   Still the first item: nothing audio moves until it is paid.
1. **Overlapping HTTP requests starve the internal heap, and on 2026-09-18 they
   took the radio down with them.** Measured on `80eb788`
   ([drafts/27-heap-block-experiment-2026-09-18.md](drafts/27-heap-block-experiment-2026-09-18.md)):
   a heavy frame alone costs nothing, sequential requests cost nothing, but requests that
   overlap step the largest free internal block down for good - 23,540 -> 21,492 -> 20,468 B,
   no recovery. Pushed further the panel reported `minFreeHeap` 1,648 B, `allocFails` 7,
   314 B each, task `wifi`, and went off the network for ~25 s until its own link recovery
   brought it back. No reboot, no crash, the clock stayed on screen. Same family as D1 and
   it blocks the same things: any third consumer of internal RAM.
2. **The IR receiver has never run.** Everything electrical is now known and
   measured, so the next step is purely physical: solder a 38 kHz part on IO45
   with 2.2 kΩ into the empty pull-up pad, measure the idle voltage, and send
   Keralots the number he asked for on 2026-09-16.
3. **`ir.enabled` read false after a flash** although the default is on - never explained.
4. **The fork's weather scheduler still compares a signed difference against a
   deadline** (`6e91d54`), the class of bug the IR audit killed. Fix it the way
   upstream PR #6 does.
5. **Crash report, tail case:** `resetReason` is taken from the boot that found
   the dump, so if the NVS save fails the next boot can relabel a task watchdog
   as `abort()`.
6. **The audio module skeleton** on `feature/ma-player` is unaudited.
7. **The second person on the radar** - parked until the next tests.
8. **The owner's e-mail is public on GitHub** and sits in the upstream history;
   that is almost certainly where today's cold-sales mail came from. Two clicks
   in his account settings, which only he can make.

**Next.**
- The **gzip portal** is the last item in Keralots' queue and the biggest: he
  measured 144,451 bytes of literals gzipping to 32,956, matrix-s3 from 82.6 %
  to about 77 %, and he asked for the generator and a loud failure when the
  generated header goes stale. Our fork already does all of it.
- Then the owner's call on the playable screens: "a game that is also the clock"
  or "games on the panel", and whether the minute change interrupts a session.

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
   GND**, and the eFuse read the same evening confirms `VDD_SPI_FORCE = True`, so
   GPIO45's strapping role is dead on this board: the pull-up positions at IO45/IO46 are empty and nothing on
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

