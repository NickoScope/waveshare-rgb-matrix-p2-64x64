# 33. One way to talk to a device: the tooling estate, and `nsc`

**The complaint this answers.** An agent has three ways to learn what a device is doing - read a
text log, call an HTTP route and read the answer, push something over MQTT and hope. Every one of
them ends with a model reading prose and deciding. That has already cost this project real time.

**The proposal it answers.** One utility per device, every command printing exactly one JSON
object and setting a meaningful exit code, so the agent acts on data and the result is checked by
a number rather than by reading. Modelled on MicroPixel.

---

## 1. What MicroPixel actually does, read from the repository

`github.com/78/micropixel` (site `micropixel.ai`), by the account `78` - the author of
`xiaozhi-esp32`. It is a **WebAssembly application runtime for Espressif MCUs**: ESP-IDF 6.1, a
pinned WAMR fork (AOT v6), a restricted C++23 guest SDK on a single-threaded event loop, one
`AppSession` at a time. Boards: Metalio-Claw4, ESP-Mosaico, ESP32-S3-BOX-3, LCKFB SZPI, M5Stack
CoreS3. The CLI is `tools/manager/micropixel_manager.py`, 722 lines, invoked as `micropixel`.

**The envelope is richer than the summary that reached us.** From `micropixel_manager.py`:

```python
envelope = {'schema_version': 1, 'ok': code == 0,
            'code': error['code'] if error else 'ok',
            'result': result, 'error': error, 'warnings': manager.warnings}
```

So: `schema_version`, `ok`, `code`, `result`, `error`, **`warnings`**. And the important
distinction - **`code` is a symbolic string** (`environment_not_ready`, `checksum_mismatch`,
`input_required`) while the 0-4 is the **process exit status**. Two different things on purpose:
a symbol to branch on, a coarse class to act on. `ok` is derived from the exit code in one place,
so it cannot drift.

**The exit ladder**, recovered from ~60 `Failure(...)` sites:

| code | meaning | examples in their source |
|---|---|---|
| 0 | done | |
| 1 | `execution_failed`, `interrupted` | retrying may work |
| 2 | `invalid_arguments` | the call was wrong |
| **3** | **a person must decide** | `input_required`, `project_unlocked` |
| 4 | inputs or environment are wrong; retrying is pointless | `checksum_mismatch`, `incompatible_lock`, `environment_not_ready`, `invalid_manifest` - about 50 sites |

**Three is the one we did not have.** For an autonomous agent it is the difference between
stopping to ask the owner and giving up.

### Four techniques worth taking

1. **stdout is sacred.** `with contextlib.redirect_stdout(sys.stderr) if json_mode else ...` -
   in JSON mode *everything* anyone prints goes to stderr. One line, and "exactly one JSON
   object" becomes true rather than hoped for.
2. **`warnings[]` carry `next_command`** - a literal command string, e.g.
   `'next_command': 'micropixel update --yes --json'`. Machine-actionable guidance, not prose.
3. **Incompatible modes are refused, not fudged.** `run --json` requires `--no-follow`
   (`Failure('invalid_arguments', ..., 2)`): a live log tail and one JSON object cannot coexist.
   This kills the naive `nsc log --follow --json` before it is written.
4. **`doctor` verifies identity, not presence.** It re-checks `toolchain_id` against the
   manifest and fails `incompatible_lock`. The defence against a tool that has become a confident
   liar.

### And their `AGENTS.md` is the bigger prize

Two lines from it land directly on what this project got wrong on 2026-09-20:

> *"Do not bypass stack-frame checks or simply increase task stacks to accommodate work buffers."*
> *"Host builds enforce stack-frame limits and emit GCC `.su` reports next to object files … measure task minimum free stack on the selected board after success and failure paths; a frame limit is not a total call-stack bound."*

They catch oversized stacks **at build time** with `-fstack-usage`. **We have that flag in no
environment** (checked in `platformio.ini`, 2026-09-21). That is the cheapest single improvement
available to us, and it is the exact failure of the night the broker was sized at 12 KB by taking
the largest of four rather than by measuring. Also worth copying: *"identify the chip by MAC, not
a re-enumerating port name"* - during the same session `/dev/cu.usbmodem2101` vanished mid-test -
and *"only one serial tool may own a device at a time"*, which we keep as the spoken rule
`pkill -f panel_logger`.

---

## 2. The correction that matters most

The case quoted in support of the proposal was *"a counter instead of the effect number"*. It is
real, and the post-mortem is written into the NickoScope32 source itself,
`urri_http.cpp:349-356`:

> *"the TRUE effect comes from the H743 heartbeat, not from currentEffect. That one is an S3-local counter in 0..NUM_FX-1 (NUM_FX == 8), it drifts and has nothing to do with the device's effect: /status showed «fx8 Teletype» while the tube was running fx39 with the game SCOOM. The lying field has already cost a false diagnosis."*

**A JSON CLI would not have prevented it.** `/status` was JSON from the start; `current_fx` was
already machine-readable. What lied was not the presentation but the **value**: a field named for
the effect number carried a local counter. The cure that worked was taking the value from the
authority - the H743's own heartbeat - rather than from a convenient local proxy.

**The disease is naming and derivation, not formatting.** It is still live in four places:

| where | the trap |
|---|---|
| `nsc status` output | prints `{"current_fx": 9, "fx_name": "fx26 Lissajous"}` - **two different numbers on one line**, both looking like the answer. `SKILL_NickoScope32.md:18`: *"the «fxNN …» names are historical, NOT ids!"* |
| `mcp_nickoscope/device.py:467` | `"effect_index"` holds a **name**, not an index, beside `"effect_name"` |
| `protocol/nsp.h:338-349` | `index` (0..count-1), `fx_id` (0..127), `total_count`, `fx_version` (a monotonic counter) - four adjacent fields, four different meanings |
| `mcp_nickoscope/README.md` | **`run` answers twice**; whoever takes the first reply gets `points` = the slot number |

So the envelope is worth having, but the three things that actually cure this are: **name a field
for what it holds; derive it from whoever knows it; and have `doctor` cross-check two sources and
fail when they disagree.**

---

## 3. The tooling estate as it stands, 2026-09-21

About forty tools across four projects. The live device tooling for NickoScope32 is **not** in
`~/NickoScope` (that is the GitHub profile repo) or `~/NickoScope32-git` (bare repos) - it is
under `Dropbox/.../Oscilloscope/` in `Beam-OS/tools/` and `NickoSClock/NickoBridge/`.

**`nsc` already exists.** `NickoBridge/deploy/nsc`, bash: `nsc status`, `nsc fx 31`,
`nsc console "BFX 10 1"`, over HTTP to the bridge on `:8081`. It passes the answer through raw -
`/status` is JSON because the endpoint is, everything else is free text - and it **always exits
0** (the last statement of every `case` arm is an `echo`). So the work is not to build a CLI; it
is to finish the one that exists.

Who is on which channel:

| channel | who | shape |
|---|---|---|
| HTTP `:8080` | the NickoScope32 **ESP32-S3 ("MAIN")**, `urri_http.cpp:120`; ~25 routes; `/status` is JSON, the rest plain text | firmware |
| HTTP `:8081` | the Raspberry Pi bridge, deliberately mirroring the same API one port up (`nickobridge/config.py:17`) | service |
| serial, VID `0483` | **STM32H743** render engine, 921600, NSP binary frames + a text console; **held by the bridge, never open it directly** | |
| serial, VID `303a` | **ESP32-S3 / MAIN**, 115200, Arduino log; reached with `deploy/s3`, which finds the port by VID and exits 2 with a helpful table when it cannot | |
| MQTT | scenes: `nickoscope32/lua/h743/{tx,res}`, `begin`/`data`/`end`/`ctl` JSON frames, 8191-byte slots | |
| HTTP `:80` | the **LED matrix panel** - a different device entirely; `/api/*`, one serial port | |

Already well-behaved and worth copying **locally**: `AnimatedPixelClock/tools/railboard/rtt_client.py`
prints one JSON object and returns the CLI result as its exit code. It is the closest thing in the
estate to the target shape, and it is ours.

Everything else that touches hardware prints free text, and most of it exits 0 whatever happened:
`nsp_monitor.py`, `verify.py` (undocumented, IP hard-coded), `panel_logger.py`, the whole bridge
log. The host-side `check_*.py` gates are the honourable exception - they all end
`sys.exit(1 if bad else 0)`.

---

## 4. `nsc` for the LED panel: what was built and what it caught

`tools/nsc/nsc.py` in this repository. Mac-side, no firmware change. Envelope and exit ladder
exactly as section 1. Commands: `status`, `budget`, `page N`, `style N`, `doctor`.

Two rules are the whole point:

- **stdout carries one object.** Everything else is redirected to stderr in `--json` mode.
- **A command that changes something reads the state back.** `POST /api/panel {"showPage":N}` is
  silently ignored *and* answers `success:true` - the failure that cost two test sweeps. Verified
  again on 2026-09-21: the panel answered `{"success":true, ...}` to `{"showPage":3}` while
  staying on page 9. `nsc page` compares and exits **3** when the panel agreed politely and did
  not change.

`nsc budget` is the command this project needed and did not have. It subtracts what each module
requires as a **contiguous** internal block from the panel's `largestHeapBlock` and exits 3 when
the answer is negative. Live on the restored firmware:

```
largest_block 17396 · flight needs 13312 (headroom 4084) · rail 10240 · weather 9216 · worldclock 9216
```

Every number needed to refuse the broker build hours earlier was available beforehand. Nobody
subtracted them.

### What `doctor` caught on its first run - the part worth keeping

It failed, correctly, with `threshold_drift` and exit 4: the table said the rail board needs
10,240 B, the firmware checkout it was pointed at said 13,312. **The table had been written from
a branch that had cut that stack from 12 KB to 9.** `nsc budget` would have been optimistic by
3,072 bytes, in exactly the direction that gets a bad build flashed - and the tool caught itself
before a human could be misled.

The fix exposed something the panel cannot answer. `/api/info` reports `version` ("2.5.0") and a
`build` timestamp, but **no git commit and no branch**, so nothing can work out which tree
produced what is running. Rather than check the wrong tree quietly, `doctor` now refuses:
`input_required`, **exit 3** - the MicroPixel category we did not previously have. The proper fix
belongs in the firmware: report the build's commit in `/api/info`, the way MicroPixel checks
`build_id` before trusting its own runtime.

### And one finding that was not about tooling at all

While testing, every route registered through `route()` in `web_panel.cpp` began answering
**HTTP 503** - the `webBusyRefuse()` gate - persistently, not transiently, with the TRAINS page on
screen; and `/api/info`, which bypasses that gate, returned **truncated JSON** (cut at 1,434
bytes). That is the owner's long-standing complaint - *"the rail board wrecks the web"* - observed
as an exit code rather than as an impression. The panel then left the network entirely and the USB
port disappeared with it, so the episode is recorded here and not yet explained.

---

## 5. What to do, in order

1. **`-fstack-usage` in `platformio.ini`.** One flag. It is the thing that would have stopped the
   12 KB broker stack, and it is what MicroPixel enforces on every host build.
2. **Report the build's git commit in `/api/info`.** Without it no tool can verify its own
   assumptions against the firmware that is actually running, and `nsc doctor` must keep asking a
   human.
3. **Publish what each module needs** as a small array in `/api/info` - they are compile-time
   constants - so `nsc budget` stops being a second source of truth.
4. **Finish `deploy/nsc` for NickoScope32** the same way: exit codes, `--json`, and a `doctor`
   that cross-checks `current_fx` from the S3 against the H743's heartbeat and **fails when they
   disagree**. That is the only one of these that automatically catches the disease in section 2,
   which has already cost two false diagnoses.
5. **Rename the lying fields.** `effect_index` that holds a name; `current_fx` beside an
   `fx_name` containing a different number.
