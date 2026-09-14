# Lua on the matrix — what our own three implementations teach

Studied 2026-09-10 from source, not from memory. Nothing here is built yet.

## The three we already have

| Where | Version | What it is |
|---|---|---|
| H743 `src/beamlua/` | v46.78.0 | the flagship. Vector CRT, 192 KB static pool, `beam.scene()`, `beam.kit` maths in C, 208 KB of embedded games, NSP transport to the S3 |
| Main-S3 `src/nslua/` | v33.58.0 | Phase 1 pilot. A port of the H743 sandbox to our chip. Stateless: a fresh `lua_State` per run. Proof the binding works, no render path |
| **Watch `nslua` + `beamlua` + `lua_store`** | v0.34.1 | **the one that matters here.** The same model, on a raster screen, on an ESP32-S3 with PSRAM |

## Why the Watch is the template and not the CRT

The Watch is our situation almost exactly:

| | Watch | This panel |
|---|---|---|
| Chip | ESP32-S3 + PSRAM | ESP32-S3 + 16 MB octal PSRAM |
| Display | raster, 466 × 466 | raster, 128 × 64 |
| Partition | `default_16MB.csv`, spiffs 0x360000 | **identical** — 3.375 MB, and LittleFS is already mounted for the custom animations |
| Web portal | :80, POST + JSON | :80, already there |
| MQTT | yes | added today |
| Second MCU | none — Lua runs locally | none |

The H743 differs in the two ways that matter: it draws vectors on a CRT, and it
is fed scripts over NSP from another chip. Neither applies to us.

## The three lessons the ADD calls "cannot be otherwise"

Written into `WATCH_ADD_Lua_Phase2` from S3 experience, and they cost real time
to learn:

1. **`S` is a global.** The prelude writes into a global `S`.
2. **`beam.t()` is a phase in [0,1), not seconds.** Wall time comes from
   `beam.now()`. Mixing the two is the classic bug.
3. **The `lua_State` must be persistent, not per-frame.** A fresh state thirty
   times a second hammers the PSRAM allocator. The Phase-1 S3 pilot is
   stateless and is explicitly *not* the model for rendering.

## The safety architecture, which is the valuable part

This is the bit worth copying verbatim, because it was derived from a real
failure mode rather than from caution:

**A dedicated FreeRTOS task with a 32 KB C stack.** The reasoning, verified
against the vendored Lua (`LUAI_MAXCCALLS = 200` in `llimits.h`): a hostile
deeply-nested script exhausts the **parser's C stack at compile time**, and a C
stack overflow is **not caught by `pcall`**. On an 8 KB loop task that is a
HardFault, not an error message. A separate task with a real stack plus a
wall-clock deadline closes it.

That matters more to us than to the Watch. Today's audit found two paths that
blocked `loop()` long enough to trip the 15 s watchdog; a Lua interpreter on the
loop task would be a third, and a worse one.

The rest of the sandbox:

- **single-flight** — exactly one `lua_State` and one instruction hook at a
  time, which is what makes a file-static instruction budget valid
- **instruction budget** 2 000 000, with a wall-clock deadline as the second line
- **`luaL_loadbufferx` mode `"t"`** — source text only, never precompiled
  bytecode, which can crash the VM by construction
- **forbidden forever** (ADR-0003): `beam.dac`, `beam.gpio`, `beam.timer`,
  `beam.dma`, `beam.register`, `beam.sleep`. Scripts cannot reach hardware
- **`beam.kit`** — hot scalar maths moved into C, because one C call costs a
  fraction of the instruction budget that the same arithmetic costs in bytecode

## What it would take here

| Piece | Effort |
|---|---|
| Vendor Lua 5.4.8 + `lcorolib` | copy; games need coroutines |
| `nslua` + `nslua_state` + `nslua_task` | near-verbatim port. Same chip, same allocator, same PSRAM |
| Script storage in LittleFS | `lua_store` ports; our partition and mount already exist |
| Galleries built from the filesystem | `lua_gallery` ports |
| Web upload page | ours is a different portal, so this is new work |
| **The render bridge** | **the real work** — see below |
| Register as a page | small: the encoder and page dispatch exist |

## The one decision that is not a port

The Watch bridges `beam` (normalised vector, [−1,1], Y up) onto its raster
primitives, deliberately keeping the S3 API 1:1 so galleries move between
devices. That portability is worth a lot: one script would then run on the CRT,
the Watch and this panel.

But 128 × 64 is not 466 × 466. Vector paths at our resolution are chunky, and
today's yacht radar taught the same lesson the expensive way: on a raster panel
a wireframe reads as noise, while filled shapes and per-pixel brightness read as
a picture. A pure `beam` port would inherit exactly the mistake I already made
once.

So: **both**, which the plug-and-play binding registry
(`NSLUA_BIND_REGISTER`) is built for.

- `beam.*` — the 1:1 contract, so the existing gallery runs, coarsely
- `px.*` — a raster group for scripts written for this panel: filled rects,
  sprites, GFX text, direct pixel access

## The risk that is ours alone

> **Measured on 2026-09-14 — see the last section.** In this build the HUB75 frame
> buffers are in internal SRAM, not PSRAM: `SPIRAM_DMA_BUFFER` is not defined, and
> the library then allocates with `MALLOC_CAP_INTERNAL | MALLOC_CAP_DMA`. The
> contention described below did not show; the limit turned out to be CPU time.

The Watch's framebuffer lives in PSRAM and so does its Lua heap, and that is
fine there. Here, **the HUB75 DMA buffer may also be in PSRAM** — that is what
lets the panel grow past internal SRAM at all — and PSRAM bandwidth is already
the binding constraint: the driver caps at ~13 MHz because GDMA gets only half
the bandwidth, sharing round-robin with the CPUs.

Putting a Lua heap in the same PSRAM, allocating during a frame, competes with
the DMA that is refreshing the panel. The visible symptom would be flicker
under script load. Nobody has measured this; it is the first thing to bench.

Mitigations, in order of preference: keep the Lua heap in internal SRAM (we use
only 25 % of it) and leave PSRAM to the DMA; or keep the framebuffer in internal
SRAM at 128 × 64, where it fits, and give PSRAM to Lua.

## Recommendation

Worth doing, and cheaper than it looks: flash is at 25 % of 6.5 MB, the
filesystem is already mounted, and two thirds of the code is a port between
identical chips.

Sequence, so that each step is provable:

1. Port `nslua` Phase 1 — the stateless self-test. Proves the toolchain and the
   PSRAM allocator on this board. Costs a day and settles the memory question.
2. Bench the PSRAM contention above **before** building anything on top.
3. Port the persistent state and the dedicated task.
4. Write the `px.*` raster bridge first, `beam.*` second — our own scripts
   before portability.
5. Storage, gallery, upload.

Do **not** start until the panels are here and phase 4 of the
[bring-up](12-bringup.md) is green. Every question above is answered by
measurement, and there is nothing to measure yet.

## Measured on the panel — 2026-09-14

### The phase 6b bench

Env `matrix-waveshare-rgb-luabench`, the clock held on Snake, three 20 s phases.

| | Result |
|---|---|
| Driver refresh | 84 Hz; frame buffers in internal SRAM |
| One `nslua_run`, empty script (a fresh sandboxed state) | 2.54 ms |
| 50 000-iteration compute loop | 64.1 ms |
| Building 3000 strings | 182.5 ms |
| A — the clock alone | 58–62 frames/s, render avg 1.9–2.2 ms, max ~3 ms |
| B — that string script once per frame, inline | 5.3 frames/s: the script is the frame |
| C — the same script back to back in a task on core 0 | render avg 2.2–2.5 ms, max 2.4–4 ms, frame rate unchanged |
| PSRAM | back to its start value after every phase |
| Internal heap minimum | ~32 KB with or without Lua |

The first run failed every script: the sandbox removes `collectgarbage`, and the
script called it last. Not yet done: the owner's eye on phase C for flicker.

### The effects on the panel

The luasim scripts as pages (`src/lua/`): one persistent state per effect on a
core-0 task with a 16 KB internal stack, drawing into a PSRAM canvas that the
render on core 1 only blits. From the `[luafx]` serial lines over a carousel lap:

| Effect | Frames/s | Draw avg / max | Open | Heap peak |
|---|---|---|---|---|
| minecraft | 20.0 (the cap) | 33.6 / 42.4 ms | 33 ms | 30 KB |
| room_radar | **2.6** | **378.6 / 396.4 ms** | **1.78 s** (1.02 M instructions) | 87 KB |
| tetris_clock | not captured — the page left before the 30 s report | | 29–31 ms | |
| snake_clock | not captured, likewise | | 23–26 ms | |

- The task took 16.8 KB of internal heap (89.9 → 73.1 KB free at start); the stack
  never had less than 11.6 KB free.
- Every close returned PSRAM to the same value.
- Heap polled over the same lap: internal low-water mark 39.5 KB, largest block
  never under 34.8 KB, PSRAM dipping 108.5 KB, no restart.
- **room_radar is too slow as written:** its per-pixel background and grid loops run
  in Lua every frame (~310 000 instructions). Moving them into C helpers, or
  drawing the static grid once, is the obvious next step.

### The new looks, same evening

The owner asked for the Tetris and snake clocks on a fully black ground with
digits as big as the world clock's, and a Minecraft with more contrast and
livelier characters. Merged as `f332d7b`. The scripts no longer call
`px.glow` or `px.blend`, whose double-precision math the S3 does in software.

| Effect | Frames/s | Draw avg / max | Open | Heap peak |
|---|---|---|---|---|
| minecraft (new) | 20.0 (the cap) | **18.0 / 23.5 ms**, was 33.6 / 42.4 | 78 ms, ~20 000 instructions | 55 KB |
| tetris_clock (new) | 19.9 | 15.7 / 217.7 ms | 25–27 ms | 131 KB |
| snake_clock (new) | not captured: the page left before the 30 s report | | 24–26 ms | |

- The minecraft that does more now draws in about half the time. Dropping
  glow and blend is the likely reason, not measured separately.
- tetris_clock's 218 ms max, ~87 000 instructions, is a single frame, most
  likely the minute change when every digit is rebuilt (the helper measured
  the same pattern on the host). At 20 frames/s that frame costs about four
  frames: a hitch once a minute, not yet seen by eye.

