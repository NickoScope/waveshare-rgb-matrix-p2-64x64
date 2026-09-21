# 34 — Sound for Lua effects

A task, written 2026-09-21 because the owner asked whether an effect could make
a noise. It can, and the board is ready for it, but nothing in the firmware is.
This says what is known, what has to be measured before a line is written, in
what order, and where it will hurt.

**Status: not started.** Nothing here has been built. Section 2 is what was read
off the tree tonight; section 3 is what is not known and has to be found before
any of it is designed.

---

## 1. What is being asked for

A Lua effect that draws *and* sounds: the fireworks with a thud and a crackle,
a clock that chimes, a radar that pings. The script stays a script - the
question is what it should be able to say, and what carries it.

**And, from the owner on 2026-09-21: enough helpers for any kind of
accompaniment, including playing sound files from a library on the SD card.**
That is two features, not one, and they want different things:

| | needs | costs |
|---|---|---|
| **Synthesis** - tones, sweeps, noise, envelopes | a few oscillators in C++ and a trigger API | CPU, no storage, no latency |
| **Samples** - a library on the card, played by name | a reader, a ring buffer and an SD lock | storage and I/O, and a first-read latency |

Both end in the same mixer and the same I2S feed, so they are one task - but
the sample path carries the risk (section 4.4) and should be built second.

---

## 2. What is already true, from the tree

Every line here was read out of the repository tonight, not remembered.

| | |
|---|---|
| **Output codec** | **ES8311**, on the shared I2C bus. `src/board/board_i2c.h:3-4` and `src/climate/README.md:21` both list it — and the latter says plainly **"This firmware uses none of them"** |
| **Its data line** | **IO21**, named in `src/audio/audio_mic.cpp:176`: `pins.data_out_num = -1; // I2S_PIN_NO_CHANGE: IO21, the ES8311's input, is left alone` |
| **Input codec** | ES7210, four-channel ADC, two analog microphones (`src/audio/es7210.h:2`) |
| **The I2S in use** | **I2S0**, 48 kHz, RX only: MCLK **IO12**, BCLK **IO43**, WS **IO38**, DIN **IO39** (`audio_mic.cpp:37-38`, `:161`, `:173-177`) |
| **I2S peripherals available** | **two** — `SOC_I2S_NUM (2)`, from the SoC caps header of this exact toolchain |
| **Audio output anywhere in the firmware** | **none**. No `I2S_MODE_TX`, no `i2s_write`, no `tone()`, no DAC. Searched the whole tree |
| **I2C rule** | every `Wire` call in this fork runs on the loop task, and one module owns the bus (`src/audio/README.md`, "The I2C bus"). An ES8311 bring-up has to obey it |
| **Lua sandbox** | a script sees `px.*` and, on a presence build, `presence.*`. Nothing else. No `sys`, no clock in milliseconds |
| **SD card** | already in use: `SD_MMC` in **1-bit mode** (`SD_PIN_CLK/CMD/D0`) at `SDMMC_FREQ_DEFAULT`, a `/clips` directory, upload over HTTP and frames streamed into a ring buffer (`src/clips/clip_sd.cpp:89-99`, `clip_stream.cpp:27-57`) |
| **Effect task** | 12 KB stack, core 0, `draw()` capped at 500 ms and 2,000,000 VM instructions, 1–30 fps |
| **Measured on the panel tonight** | the fireworks effect draws in ~120 ms at 8.2 fps, of which the bench rate accounts for ~40 ms; the rest is being preempted on core 0 by Wi-Fi |

### The one that shapes everything

BCLK, WS and MCLK are **one set of lines**, and the ES7210 already drives them
from I2S0. The ES8311 sits on the same clocks with only its data line separate.
So the natural shape is **one port in full duplex** — `I2S_MODE_MASTER | TX |
RX` on I2S0 with `data_out_num = 21` — and not the second peripheral.

That couples sound to the microphones, and the microphones are **switched off by
the owner's instruction** (2026-09-15) until the audio-visualizer hang has a
root cause. Which means:

> **Sound is downstream of debts D1 and D2** in `docs/22 §12.3`. Not a
> preference — the same I2S0 and the same internal DMA buffers are the thing
> that is already suspected.

Whether the second I2S could drive the ES8311 on its own set of clock pins is
**unknown and is question Q2 below**. It would decouple them, and it would cost
three more GPIOs the board may not have free.

---

## 3. What is not known — answer these before designing anything

Per the project's own rule: no code for new hardware until a research report
with sources exists (`nickoscope-hw-deep-dive`). These are its questions.

| # | Question | Where the answer is |
|---|---|---|
| **Q1** | **Is there a speaker, and what drives it?** The ES8311 has a small integrated amplifier; many Waveshare boards add an NS4150. Nothing in this repository says which, or whether a speaker is fitted or only a pad | the Waveshare schematic for ESP32-S3-RGB-Matrix; then eyes on the board |
| **Q2** | Are the ES8311's BCLK/WS/MCLK really shared with the ES7210, or separately routed? | the same schematic. Decides duplex-vs-second-port, and Q2 decides most of the design |
| **Q3** | What does a TX DMA buffer set cost in **internal** RAM? The mic uses 4×256; TX needs its own | measure. The panel runs with ~21 KB free internal and a minimum of 7,344 B under load — this is the binding constraint on the whole board |
| **Q4** | ES8311 bring-up sequence and errata | Everest datasheet; Espressif's `esp_codec_dev` ES8311 driver as the reference implementation, the way `es7210.cpp` was written |
| **Q5** | Can I2S0 be reconfigured to duplex **without** disturbing a running capture, or does it need a stop/start? | IDF i2s driver source for this version; then a bench test |
| **Q6** | What does the ES8311 do with no MCLK? Today MCLK only runs while the mic task wants it | datasheet + bench |

---

## 4. The design that looks right, subject to section 3

### 4.1 Lua gets a control rate, not a sample rate

The effect task cannot feed audio. It runs at 8–20 fps with a 500 ms budget on
the core Wi-Fi is on, and 48 kHz needs a sample every 20 µs. A script that
synthesised samples would starve the DAC on its first slow frame.

So the script **triggers**, and C++ **synthesises**:

```lua
snd.play(snd.NOISE, 0.35, 0.9)          -- the burst: noise, 350 ms, loud
snd.tone(220, 0.12, 0.4)                 -- a thud
snd.sweep(1400, 200, 0.5, 0.3)           -- the shell going up
```

Four to six voices, mixed in C++, each with an envelope. The whole Lua surface
is a handful of calls that cost nothing and return immediately. This also keeps
`fx_parity` meaningful: sound leaves no pixels, so the frame comparison is
unaffected, and the trigger calls are deterministic like everything else.

### 4.2 Samples from the card

The clips module is the pattern, and most of it transfers: a directory on the
same card, an upload route beside `/api/clips/upload`, a name-keyed library, and
a reader that streams into a ring rather than loading a file.

| Decision | Take | Why |
|---|---|---|
| **Format** | 16-bit PCM mono WAV at the I2S rate | No decoder at all - read and push. The CPU is the scarce thing here, not the card |
| **Not MP3, at first** | | libhelix is ~30 KB of code and a decode buffer, on a core already at 120 ms a frame. If the library outgrows the card, revisit |
| **Where** | `/audio` on the same card | beside `/clips`, same upload shape, same validation habit |
| **Rate** | one rate, fixed, matching I2S | resampling in software is a second thing to get wrong. Convert on the way in, with the upload tool |
| **Buffer** | ring in **PSRAM** | the file side has room; only the I2S DMA must be internal |

From a script it should be one call, and a name, not a path:

```lua
snd.play("boom")             -- from the library
snd.play("chime", 0.6)       -- quieter
```

### 4.3 What the whole surface looks like

```lua
-- synthesis, for what wants a parameter
snd.tone(220, 0.12, 0.4)              -- Hz, seconds, volume
snd.sweep(1400, 200, 0.5, 0.3)        -- from, to, seconds, volume
snd.noise(0.35, 0.9)                  -- seconds, volume
-- the library, for what wants to sound like something
snd.play("boom")
snd.play("chime", 0.6)
-- and the housekeeping
snd.stop()                            -- everything
snd.volume(0.7)                       -- the effect's own level, under the panel's
```

Every one of them returns immediately. Nothing in this list can block `draw()`,
and nothing in it needs the script to know a sample rate.

### 4.4 The hazard nobody will see coming: two tasks on one SD card

`clip_stream` seeks and reads 4 KB a frame from the loop task while a clip is
playing. An audio reader would be on its own task, on the same `SD_MMC`, and
**Arduino's SD_MMC has no lock of its own**. Two tasks interleaving a seek and a
read on one card is not a slow read; it is the wrong bytes.

So before any of this: **one owner for the card, or one mutex around it**, the
way `src/board/board_i2c` owns the I2C bus and `src/audio/README.md` states the
rule that every `Wire` call runs on the loop task. The same rule has to exist
for SD_MMC and be written down before a second reader exists.

Bandwidth is not the problem - 48 kHz mono 16-bit is 96 KB/s and the card does
far more - the interleaving is.

### 4.5 The parts

| Part | Where | Note |
|---|---|---|
| `src/audio/es8311.{h,cpp}` | new | the register sequence, on the loop task, like `es7210.cpp` |
| `src/audio/audio_out.{h,cpp}` | new | the mixer and the I2S TX feed, on its **own task** |
| `src/audio/snd_voice.{h,cpp}` | new | the oscillators and envelopes, host-testable like `audio_dsp` |
| `src/audio/snd_library.{h,cpp}` | new | `/audio` on the card, the reader and its ring |
| `POST /api/audio/upload` | new | beside `/api/clips/upload`, same shape |
| the feed task | **core 1** | core 0 already carries Wi-Fi, the effect task and the DSP; the fireworks measurement shows preemption there is already the dominant cost |
| `src/lua/lua_snd.cpp` | new | the `snd` table, bound in `LuaFx::open` beside `px` and `presence` |
| `tools/luasim` | changed | `snd.*` as no-ops on the host, so a script written for the panel still runs in the simulator |

### 4.3 What it must not do

- **Not allocate internal RAM at run time.** The DMA buffers are sized once at
  boot or not at all, and if Q3 says there is no room, the answer is that this
  feature does not fit until D1 is paid.
- **Not touch I2C off the loop task.** The rule is absolute in this fork.
- **Not make `draw()` block.** Every `snd.*` call returns without waiting.
- **Not start without the owner.** A panel on a wall that begins making noises
  by itself is a fault, whatever the code says. Off by a flag, off by a setting,
  and silent until asked.

---

## 5. The order to work it

1. **Research report** — Q1 through Q6 answered with sources, and a pin audit
   table. No code before it.
2. **Pay D1 and D2** (`docs/22 §12.3`): find the ~20 KB portal consumer and put
   a headroom gate on capture. Sound shares I2S0 and the internal heap with the
   microphones; building on top of an unexplained hang is how the hang becomes
   two hangs.
3. **Bench: one tone.** A standalone sketch, or a build flag nobody ships, that
   brings up the ES8311 and plays 440 Hz. Nothing else. Measure internal RAM
   before and after, and the CPU the feed task takes.
4. **The voice engine**, host-tested first — `tools/audiofx/host` already has
   the pattern of a DSP checked against a Python reference.
5. **The `snd` binding** for the synthesis half, with the simulator no-ops in
   the same change.
6. **One effect that uses it**, and it should be the fireworks: a thud at the
   burst is the smallest thing that proves the whole chain, and the timing is
   already there in `burst()`.
7. **Only then the library**: the SD ownership rule first, written down and
   enforced, then `/audio`, the upload route, the reader and `snd.play(name)`.
   Samples are the half that can corrupt a clip playing at the same time, and
   they are worth nothing until the synthesis half proves the feed is steady.
7. **The gate**: `senior-code-audit`, then a hardware QA run. Expect the audit to
   go more than one round - the sound path touches the two things this panel is
   worst at, internal RAM and core 0.

---

## 6. Risks, ranked

1. **Internal RAM.** ~21 KB free, 7 KB at its worst under load. If TX DMA wants
   more than is spare, the feature does not fit, and no amount of design makes
   it fit. **This is the one that decides.**
2. **Core 0 is full.** The fireworks measurement is the evidence: 40 ms of
   computation taking 120 ms of wall clock. Audio starves visibly - a gap in a
   tone is far more noticeable than a dropped frame.
3. **Duplex couples sound to the microphones**, which are off by instruction and
   carry an unexplained hang.
4. **There may be no speaker.** Q1. If it is a pad and not a part, the whole
   thing is a soldering job first.
5. **Two tasks on one SD card**, with no lock in Arduino's SD_MMC. This is the
   sample library's own risk and it is not a performance one: interleaved seeks
   give the wrong bytes, to a clip and to a sound alike.
6. **Scope.** A codec driver, a feed task, a synthesiser, a sample reader, an
   upload route and a language binding. It is an ADD and several sessions, not
   an afternoon - and the two halves should ship separately.

---

## 7. What would say it is done

- The fireworks thud on the panel, in time with the burst, with the log showing
  no dropped frames and no new internal-heap minimum.
- A sound played from the card by name while a clip is playing, with both
  correct - which is the SD ownership rule doing its job.
- `/api/info` reports the feed task's stack high-water and its underruns, the
  way the effect task now reports `stackFreeMin` - a number anyone can read
  rather than a claim.
- Silent by default, and silent when the owner says so.
