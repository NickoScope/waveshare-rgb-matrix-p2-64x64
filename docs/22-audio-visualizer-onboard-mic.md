# Audio visualizer from the onboard microphones — design

**Owner's picks, 2026-09-15 19:30:** build all eight proposed effects (Prism EQ, Neon Mirror+, Spectrogram, Scope Afterglow, Synthwave Grid, Radial Bloom, Beat Particles, Twin VU). Keep the six current effects alongside them. Being implemented on `feat/audiofx-onboard-mic`.

**2026-09-15 · research, design, previews and the capture pipeline. Nothing
flashed** (the USB port was busy with the flash backup and the repartition).
Written by the audio-visual effects helper. The owner chooses which "wow"
versions get built (§10); until then no effect's drawing changes.

**Where this stands at the end of the session.** Done: the hardware facts
(§1), this design, the previews (§10), and the capture pipeline in firmware
behind `-DAUDIO_MIC_ENABLED`, with its host test and builds (§11); local commits
on `feat/audiofx-onboard-mic`, not pushed. Left: flash it and run the panel
tests (§12); the owner's choice among W1–W8 (§9); then build the chosen
effects on `audioSnapshot()`. **Next step:** flash the branch and run §12
items 1–4.

Owner's request (2026-09-15 18:27, in short): take the upstream author's
visualizer effects, which today need the PC companion's stream, raise them to a
"wow" level, and run them from the board's own microphones.

Path aliases:
- `APC` = the firmware worktree `AnimatedPixelClock-audiofx`, branch
  `feat/audiofx-onboard-mic`, started from `feature/market-dashboard` at `776fc04`.
  **Line numbers in `APC/src/...` and `APC/tools/flag_matrix.py` are those of
  `776fc04`**, before this branch's hooks moved them; `src/viz/` is unchanged.
- `WS` = [waveshareteam/ESP32-S3-RGB-Matrix](https://github.com/waveshareteam/ESP32-S3-RGB-Matrix)
  at `4047e4e`, under `example/idf_v5.5.2/`.
- `CODEC` = [espressif/esp-adf](https://github.com/espressif/esp-adf) `components/esp_codec_dev/`;
  `device/es7210/es7210.c` last changed in `2047df4` (2023-06-16).
- `IDF` = [espressif/esp-idf](https://github.com/espressif/esp-idf) tag `v4.4.7`, the IDF inside
  arduino-esp32 2.0.17 (`FW/tools/sdk/versions.txt:1`).
- `FW` = `~/.platformio/packages/framework-arduinoespressif32` (3.20017.241212 = arduino-esp32 2.0.17);
  `SDK` = its `tools/sdk/esp32s3/opi_opi/include/sdkconfig.h`, this env's memory type.
- `COMP` = `APC/PC-Companion-App-v4/companion-common/audio_spectrum.py`.
- `SCH` = `reference-drawings/controller/ESP32-S3-RGB-Matrix-Schematics.pdf` in this KB.

## 0. Summary

1. **Two analog microphones through an ES7210 ADC.** MIC1 and MIC2 are 4-pin SMD
   microphones (VDD, GND, GND, DAT; "1.6V-3.6V 3.76x2.95x1.1mm" on SCH, **no part
   number**), biased from the ES7210's MICBIAS12 and AC-coupled into its MIC1/MIC2
   inputs. The ES7210 (U10) answers on I2C at 0x40 and sends 16-bit standard
   (Philips) I2S as a slave on IO39; the S3 drives MCLK IO12, BCLK IO43, WS IO38.
   Not PDM; with two mics not TDM. A register sequence over I2C must run before
   the first sample. No GPIO switches the mic power: IO46 goes only to the header,
   which answers [12](12-bringup.md) question 5 from the schematic.
2. **The existing visualizer reads 32 bytes.** Six styles, all fed by the
   companion's `FFT1` UDP packet on port 4210: 32 band bytes (dB under AGC over
   38 dB) and 128 waveform bytes, 25 packets a second. The panel draws them at
   60 Hz. Upstream main has byte-identical files.
3. **Design.** A capture task on core 0: 48 kHz, Hann 2048, hop 960 (50 frames a
   second), the companion's own band table, noise gate, AGC, attack/release, peak
   hold, spectral-flux beats. Every 40 ms it builds the same 164-byte `FFT1`
   packet and loop() hands it to `vizIngest()`, so every existing effect draws the
   room unchanged. New effects read a richer frame: levels, peaks, beats, dB.
   In auto the PC's packets win while they arrive.
4. **Budgets.** Internal SRAM about 10.5 KB (DMA 4 KB, stack 5 KB, the rest
   small); PSRAM about 52 KB. CPU estimated at 2 ms per 20 ms on core 0, only
   while the visualizer is on screen, and reported by `/api/info`. Latency
   estimated at 30–90 ms before the codec's own filter delay.
5. **Previews** (`APC/tools/audiofx/`): an offline simulator runs synthetic WAVs
   through the same DSP and renders the six current effects and eight proposed
   ones as GIFs at 6x, MP4s with sound and contact sheets (§10).
6. **Built, not flashed** (`APC/src/audio/`, `-DAUDIO_MIC_ENABLED`): ES7210 driver,
   capture task, DSP, source switch, `/api/info` fields, four portal settings. A
   host build of the DSP matches the Python reference frame by frame (§11).

---

## 1. The microphones

### 1.1 What is on the board

| Fact | Value | Source |
|---|---|---|
| ADC | ES7210, U10, four mic inputs, SDOUT1/TDMOUT to the S3 | SCH, U10 |
| Microphones | MIC1, MIC2: "贴片麦克风 1.6V-3.6V 3.76x2.95x1.1mm" (SMD microphone), pins VDD, GND, GND, DAT. **Part number not printed** | SCH |
| Output type | **analog**: DAT runs through L2/L3 (0 Ω) and C14/C15 (1 µF) to MIC1_P/MIC2_P; VDD comes from ADC_MICBIAS12, decoupled by C22/C23 100 nF and C18/C20 2.2 µF | SCH |
| Count | two, read as left and right: the vendor example prints `M1`/`M2` peaks from interleaved L/R | `WS/main/examples/08_Matrix_Audio/matrix_audio.c:212` |
| MIC3 | ADC_MIC3_P/N, which the text layer puts beside the codec's OUTP/OUTN: probably the playback reference for echo cancellation. **Not traced** | SCH |
| I2C address | AD0 = AD1 = 0: R36, R37 0 Ω to AGND; R32, R33 to 3V3 not fitted. 0x40 as 7 bits | SCH; `CODEC/device/include/es7210_adc.h:16` `ES7210_CODEC_DEFAULT_ADDR (0x80)`; `es7210_reg.h:47` `ES7210_AD1_AD0_00 = 0x80` |
| I2C bus | SDA IO47, SCL IO48, port 0, 400 kHz | `WS/components/bsp/esp32_s3_matrix/include/bsp/config.h`; `.../bsp/esp32_s3_matrix.h:220-221` |
| I2S pins | MCLK IO12, BCLK IO43, WS IO38, ASDOUT → IO39 through R39 51 Ω; port 0 | SCH GPIO table; `bsp/config.h`; `bsp/esp32_s3_matrix.h:161` |
| Format | standard I2S, 16 bit, stereo; the S3 is master, the codec slave | `WS/components/bsp/esp32_s3_matrix/esp32_s3_matrix.c:587-605` (`I2S_STD_PHILIPS_SLOT_DEFAULT_CONFIG(..._16BIT, STEREO)`); `:707-709` (`es7210_codec_cfg_t` sets only `ctrl_if`, so `master_mode` is false) |
| Vendor settings | 16 kHz, 2 channels, 16 bits; mic gain 30 dB | `matrix_audio.c:3-5, :180`; `esp32_s3_matrix.c:592` |
| Mic power switch | none. IO45/IO46 go only to header U8, with 10 kΩ pull-downs R59/R60 | SCH GPIO table and header |
| Needs codec setup | yes, over I2C, before any audio | `CODEC/device/es7210/es7210.c:405` (`es7210_open`), `:296` (`es7210_start`), `:474` (`es7210_set_fs`) |

**No microphone is missing**, so Phases 3 and 4 went ahead.

### 1.2 The bring-up sequence

Ported to Arduino Wire in `APC/src/audio/es7210.cpp`, in esp_codec_dev's order:
`esp_codec_dev_open()` calls `set_fs` then `enable` (`CODEC/esp_codec_dev.c:147-197`).

| Step | Registers | Source |
|---|---|---|
| open | 0x00←0xFF, 0x00←0x41, 0x01←0x3F, 0x09←0x30, 0x0A←0x30, HPF 0x23←0x2A, 0x22←0x0A, 0x20←0x0A, 0x21←0x2A; slave 0x08 bit0←0; 0x40←0x43; bias 0x41/0x42←0x70 (2.87 V); OSR 0x07←0x20; 0x02←0xC1; select MIC1+MIC2; gain | `es7210.c:405-460` |
| set_fs | 0x11: bits 16 (`|0x60`), normal I2S (`&0xFC`). In slave mode the clock dividers are skipped | `es7210.c:474-490`, `:143` |
| start | 0x01←saved value, 0x06←0x00, 0x40←0x43, 0x47–0x4A←0x08, select MIC1+MIC2 again, 0x40←0x43, 0x00←0x71, 0x00←0x41 | `es7210.c:296-310` |
| mic select | clear 0x43–0x46 bit4; 0x4B/0x4C←0xFF; per mic: 0x01 &=~0x0B, 0x4B←0x00, gain reg bit4←1, low nibble←gain; 0x12←0x00 (TDM only from three mics) | `es7210.c` `es7210_mic_select()` |

**A quirk kept deliberately:** `es7210_mic_select()` writes `codec->gain`, which
nothing sets, so on esp_codec_dev's own path the PGA sits at 0 dB after `start`
until `esp_codec_dev_set_in_gain()`; Waveshare's example calls it with 30 dB
straight after opening (`matrix_audio.c:180`). The port writes the wanted gain
in both places: the same end state.

### 1.3 Sample rate

- es7210.c's coefficient table gives, for MCLK = 256·fs, **the same divider
  values at 16, 32 and 48 kHz**: adc_div 1, DLL 1, doubler 1, OSR 0x20
  (`es7210.c:76, 89, 98`). Those are exactly the values `es7210_open()` writes
  (0x02←0xC1, 0x07←0x20), and slave mode never touches the dividers
  (`:143`). So 48 kHz at the S3's default MCLK multiple needs no extra register.
- **Chosen: 48 kHz.** The companion also samples at 48 kHz with FFT 2048
  (`COMP:42-44`), so the FFT bins and the band table are identical, and the top
  band (13.4–16 kHz) sits well inside Nyquist. At the vendor's 16 kHz, bands
  28–31 (above ~7.8 kHz) would be empty: half the treble group the starfield
  and the purple stage react to.
- **Not read:** the ES7210 datasheet. Its anti-alias passband and group delay are
  unknown, and so is whether its DLL locks cleanly on the S3's fractional MCLK
  (no APLL on the S3, [17](17-media-player.md) §1 table).

### 1.4 Pins

Audio uses IO11, 12, 21, 38, 39, 43; none collide with HUB75, the TF card
(1/17/44), the encoder (45/46) or USB (19/20) ([17](17-media-player.md) §2.3).
This pipeline takes 12, 38, 39, 43 and I2C 47/48 only. Carried over from there:
- **IO43** carries the ROM boot log onto the codec's BCLK at every reset.
- **IO11** (amp enable) is not driven by this code; if it floats high the NS4150B
  may sit enabled with no signal.
- **I2C 47/48** are shared with the RTC, SHTC3 and IMU. `Wire.begin()` on a bus
  someone already started warns and returns true, and Wire takes its own lock
  (`FW/libraries/Wire/src/Wire.cpp:300-303`, `:50`), so another module can share it.
- [12](12-bringup.md) question 6 (do 47/48 run at 1.8 V?) is still open.

### 1.5 Still unverified

Microphone part, sensitivity and SNR; the ES7210's filter delay; what MIC3 is
wired to; the 48 kHz lock on a fractional MCLK; whether anything else on the
board couples into the mic bias (§12).

---

## 2. The visualizer as it ships

### 2.1 The PC packet

| Field | Value | Source |
|---|---|---|
| Transport | UDP to port 4210, the port the stats JSON also uses | `APC/src/config/user_config.h:45`; `COMP:5-8` |
| Layout | `FFT1` (4 B) + 32 band bytes + 128 waveform bytes = 164 B. Older companions send 36 B and the scope asks for an update | `APC/src/viz/visualizer.h:14-19`; `COMP:414` |
| Rate | 25 packets a second: 1920-sample (40 ms) blocks at 48 kHz, sent from the capture thread; a watchdog repeats, then fades, the last frame when capture stalls | `COMP:42-43`, the pacing comment above `GAP_S` |
| Bands | 32 log-spaced, 50–16 000 Hz; FFT 2048 of a Hann-windowed 1920-sample block; band = RMS of its bin magnitudes; bins `lo = int(edge/bin_hz)`, `hi = max(lo+1, int(next/bin_hz))` | `COMP:44-46, 261-266, 359` |
| Scaling | dB; reference = max(ref − 1.5 dB/s·dt, loudest band, −55); 0..255 across the 38 dB below it | `COMP:59-61, 359` |
| Peaks | not sent; the panel computes its own peak holds | `APC/src/viz/visualizer.cpp`, `displayVisualizer()` from `:198` |
| Waveform | block averaged down by 8 (~3 kHz), started on the first rising zero crossing, 128 points, own AGC (decay 0.55/s, floor 0.02, gain 118), offset binary around 128 | `COMP:51-55, 373` |
| Loudness | block RMS in dBFS, used only by the companion's auto-start | `COMP` `_block_level_db()` |

### 2.2 Receive and render path

- `handleUDP()` in loop() reads the datagram; `vizIngest()` checks the magic and
  copies. Spectrum packets skip the JSON parser and do not mark the PC online
  (`APC/src/network/network.cpp:514-519`, `visualizer.cpp:148`).
- The visualizer shows while forced by `/api/mode/viz` and fed within 10 s, or for
  10 s after forcing (`visualizer.cpp:176`, `APC/src/web/web.cpp:364-373`). With
  no packet for 2 s it says "No audio data..." (`visualizer.cpp:211, 273`).
- It renders at **60 Hz** while shown (`APC/src/main.cpp:273-276`), from the
  display branch of loop() (`main.cpp:1047, 1115`). The "up to 20 fps" in the
  brief is true of other pages, not of this one.

### 2.3 The six effects

| Style | Draws | Reads | Colour, font |
|---|---|---|---|
| 0 Classic EQ | 32 bars 3 px wide + 1 px gap, up to 56 px, three fixed zones (28 / 45 px); peak dots fall at 60 px/s²; smoothing 0.35 per frame | bands | colour slots low/mid/peak, default green/yellow/red (`APC/src/config/settings.cpp:68-70`) |
| 1 Neon Mirror | bars mirrored about row 32 (36 with the clock), ±24 px, every third row dark, cyan→white up, purple down; pale peak caps | bands | fixed palette (`visualizer.cpp:88`) |
| 2 Phosphor Waterfall | 26-row history, a row every 40 ms, 4 px columns, green→amber→orange by level, 7/255 dimmer per row | bands | fixed (`:111`) |
| 3 Purple LED Stage | 32×16 lamps on a 4 px grid; each column a light wave that sways; bass (bands 0–5) opens it, treble (24–31) adds pink | bands, time | fixed (`:49`) |
| 5 Starfield Overdrive | 96 perspective stars; speed follows bass; a boost from packet-to-packet bass flux (threshold max(0.035, 1.8 × average), cooldown 160 ms) stretches the trails; colour by band group | bands, packet serial | fixed (`starfield.cpp:44-61`) |
| 6 Oscilloscope | graticule, 128-point trace, up to four ghost traces; grid, fill, flat and gain options | waveform | colour slots grid/trace/peak (`settings.cpp:75-77`); "Update PC companion" without a waveform (`oscilloscope.cpp:101`) |

All six can put HH:MM top right in the Adafruit GFX classic 5×7 font, white
(`visualizer.cpp:181`). The render path allocates nothing and touches no files.

### 2.4 Upstream

Keralots/AnimatedPixelClock main at `9e37721` (v2.3.1, 2026-09-15): the git blob
SHAs of `src/viz/visualizer.cpp`, `visualizer.h`, `starfield.cpp` and
`oscilloscope.cpp` equal this fork's. Nothing newer upstream.

---

## 3. Platform limits

### 3.1 Internal SRAM

- The brief's figure: about 40 KB free after boot, with the HUB75 double buffer
  taking about 148 KB. [12](12-bringup.md) question 7 recorded a 56.7 KB
  low-water mark once TLS moved to PSRAM. Either way, every KB counts.
- `malloc` below 4096 B stays internal (`SDK:317`, `CONFIG_SPIRAM_MALLOC_ALWAYSINTERNAL 4096`),
  and task stacks cannot live in PSRAM (`CONFIG_SPIRAM_ALLOW_STACK_EXTERNAL_MEMORY`
  is absent from `SDK`). Every DSP buffer is therefore allocated with
  `MALLOC_CAP_SPIRAM` explicitly.
- Baseline of this branch before any audio code: RAM 100 576 B static, flash
  2 146 893 of 4 718 592 B.

### 3.2 The I2S driver (legacy, IDF 4.4.7)

- DMA buffers come from `heap_caps_calloc(..., MALLOC_CAP_DMA)`: internal
  (`IDF/components/driver/i2s.c:740, 747`). `dma_buf_count` 2–128,
  `dma_buf_len` 8–1024 frames (`:1960-1961`); real size = frames × channels ×
  bytes (`FW/.../driver/include/driver/i2s.h:107-113`).
- MCLK only exists in master mode (`i2s.c:313-314`); an RX-only channel binds
  MCLK to the RX clock (`IDF/components/hal/i2s_hal.c:200-208`,
  `i2s_ll_mclk_use_rx_clk`), so an RX-only master still clocks the codec.
- `I2S_CHANNEL_FMT_RIGHT_LEFT` sets the slot mask CH0|CH1 (`i2s.c:1873-1876`).
- An overflow arrives as `I2S_EVENT_RX_Q_OVF` on the driver's queue (`FW/.../driver/i2s.h:146`).
- The HUB75 library drives LCD_CAM on the S3, not I2S: I2S0 is free ([17](17-media-player.md) §2.2).
- This driver is deprecated in IDF 5 and removed in 6.0 (Espressif's 6.0 migration
  guide, "Legacy I2S Driver is Removed"). Moving to arduino-esp32 3.x means the
  `i2s_std` API.

### 3.3 FFT options

| Option | API as verified | CPU on the S3 | Memory | Verdict |
|---|---|---|---|---|
| esp-dsp, already in the framework (`master 9b4a8b4`, `FW/tools/sdk/versions.txt:7`; linked as `-lespressif__esp-dsp`) | `dsps_fft2r_init_fc32(float*, int)` (`FW/.../dsps_fft2r.h:61`), `dsps_fft2r_fc32`, `dsps_bit_rev_fc32`, `dsps_wind_hann_f32(float*, int)` (`dsps_wind_hann.h:33`); esp-dsp API reference | 97 847 cycles for 1024 points, optimised, -O2 (esp-dsp benchmarks, ESP32S3): ≈0.41 ms at 240 MHz | its init mallocs a RAM bit-reverse table even when handed a buffer (esp-dsp master, `dsps_fft2r_fc32_ansi.c`; **the framework's `9b4a8b4` was not read**); one global FFT size | fastest; a hidden small internal allocation |
| ArduinoFFT (kosme) | `ArduinoFFT<float>(vReal, vImag, samples, fs)`, `windowing()`, `compute(FFTDirection::Forward)`, `complexToMagnitude()` (context7 `/kosme/arduinofft`) | no benchmark found | caller's arrays; not in lib_deps | a new dependency for nothing the others lack |
| Hand-rolled radix-2 | `audiodsp::Dsp::fft()` | esp-dsp's own ANSI radix-2 at -Os takes 198 336 cycles for 1024 points (≈0.83 ms); for 2048 **estimated ≈1.8 ms** | tables and arrays where we put them: PSRAM | **chosen**: the host test compiles this very file, and nothing allocates behind our back |

### 3.4 CPU

Core 0 carries Wi-Fi, the Lua effect task (priority 1, `APC/src/lua/lua_effects.cpp:63-65`),
the clip reader (priority 1, `APC/src/clips/clip_sd.cpp:108`) and the fetchers;
loop() and the panel refresh stay on core 1 (`SDK:87`, `CONFIG_ARDUINO_RUNNING_CORE 1`).
The audio task runs at priority 5 on core 0. Per 20 ms hop: FFT ≈1.8 ms plus
windowing, 1024 magnitudes, 32 logs and the beat maths, **≈2 ms estimated**,
about 10 % of core 0 — and only while the visualizer is on screen and the mic
is its source (plus 5 s). Otherwise the task only reads I2S and keeps a level
meter. `/api/info` reports `audioDspUs` and `audioDspUsMax`.

---

## 4. The audio pipeline

```
ES7210 --I2S 48 kHz, 16 bit, L = MIC1, R = MIC2--> DMA 4 x 256 frames (internal)
 core 0, task "audio", priority 5
  960-frame hop (20 ms) -> mono (L+R)/2, peak |sample|, RMS
  ring of 2048 (PSRAM) -> Hann -> FFT 2048 -> |X| * 2/sum(w)
  -> 32 bands, the companion's bin table -> dBFS
  -> noise gate on the hop RMS -> AGC reference -> band bytes 0..255
  -> levels (attack 12 ms, release 200 ms), peak hold 350 ms then gravity
  -> bass flux over bands 0-9 -> beat, strength, BPM
  every 2nd frame: 128-point waveform -> "FFT1" packet (164 B)
  -> frame copy under a spinlock (internal, 0.7 KB)
 core 1, loop(): audioPoll() -> vizIngest(packet) when the mic is the source
```

| Parameter | Value | Where from |
|---|---|---|
| Sample rate | 48 000 Hz | §1.3 |
| Window, FFT | Hann (numpy's symmetric form), 2048 = 42.7 ms, 23.4 Hz bins | `COMP:44` |
| Hop | 960 = 20 ms, 50 frames a second | half the companion's block: twice its time resolution |
| Bands | 32, log 50–16 000 Hz, the same bin spans | `COMP:45-46, 261-266` |
| Band value | RMS of bin magnitudes in dBFS (a full-scale sine reads 0 dB) | the companion's, normalised |
| Noise gate | hop RMS below −60 dBFS for 240 ms → bands 0 | **starting value** |
| AGC | ref = max(ref − 1.5 dB/s·dt, loudest band, −70 dBFS); 38 dB span; gated frames cannot raise it; off → fixed ref −20 dBFS | span and decay: `COMP:59-60`; the floor and the fixed reference are **starting values** (the companion's −55 is on an unnormalised scale) |
| Attack / release | 12 ms / 200 ms, one pole | starting values |
| Peak hold | 350 ms, then 2.5 full heights/s² | starting values (Classic EQ's 60 px/s² over 56 px is 1.07) |
| Flux | mean over bands 0–9 (50 to ~300 Hz) of max(0, x − x_prev), x = band dB floored at −90 dBFS | spectral flux on log power, as librosa's `onset_strength` defines it (context7 `/websites/librosa_doc`); band range and floor: reference values |
| Beat rule | flux ≥ max(3 dB, mean + 2.5·std over the last second) ∧ rising ∧ ≥ 160 ms since the last beat ∧ bass mean ≥ 3 dB above its last-second mean | shaped on librosa's `util.peak_pick` (mean + delta, wait), made causal; 160 ms is the starfield's cooldown; **the numbers are reference values** (below) |
| BPM | 60 / median of the last ≤ 8 beat intervals within 0.3–1.0 s; 0 after 3 s without a beat | starting value |
| Loudness | hop RMS, dBFS | — |
| Clipping | any sample at or above 32 700, flag held 500 ms | starting value |
| Silence | gated for 2 s | starting value |
| Waveform | newest 1920 samples, averaged by 8, first rising zero crossing, 128 points, AGC 0.55/s, floor 0.02, gain 118 | `COMP:51-55, 373` |
| Packet | every 2nd frame, 40 ms | the companion's cadence, which the starfield's per-packet beat logic was tuned on |

**How the beat numbers were chosen.** Six synthetic WAVs (§10): 120 BPM kicks
over a pink bed, a groove with snares and a sweep, steady pink noise at −30
dBFS, a tone start, a log sweep, a clipped burst. A first draft (flux relative to
the AGC floor, threshold mean + 1.5·std) found every kick but fired 8 false beats
on the pink noise and 2 on a tone start. A grid of 320 variants
(`scratchpad`, not kept) left a family with no miss and no false beat on all six:
the rule above, with K anywhere in 2.5–3.0 and the delta anywhere in 1–6 dB. The
choice sits in the middle. **By the project's rule these are reference values**:
six synthetic files are not five independent real examples. Beats only drive
visuals, but the numbers must be re-checked on real music through the
microphones (§12) before anything leans on them.

---

## 5. The data contract

```cpp
struct Frame {                     // APC/src/audio/audio_dsp.h
  uint32_t k, samples, packets, beats;
  uint8_t bands[32], wave[128], packet[164];   // packet = "FFT1" + bands + wave
  float level[32], peak[32];                   // 0..1
  float bass, mid, treble;                     // mean level of bands 0-7, 8-23, 24-31
  float levelDb, refDb, flux, thr, strength, bpm;
  bool published, gated, silent, clipping, beat;
};
```

- **One writer, one reader, one lock.** The task copies its PSRAM work frame into
  an internal copy inside a `portMUX` spinlock (≈0.7 KB memcpy). loop() copies
  out the 164-byte packet and its counter under the same lock. No heap, no queue.
- **The adapter is `vizIngest()` itself.** The microphone's packet is
  indistinguishable from a current companion's: AGC'd bands over 38 dB and a
  waveform. The only differences are invisible after the AGC: normalised dB and
  a different AGC floor.
- **Richer effects** call `audioSnapshot(Frame&)`.

| `audioSource` | PC packet within 1.5 s | Mic state | The visualizer draws |
|---|---|---|---|
| 0 auto (default) | yes | any | PC |
| 0 auto | no | ok | microphones |
| 0 auto | no | not ok | nothing: "No audio data..." after 2 s |
| 1 PC | — | — | PC only; mic packets are not ingested |
| 2 mic | — | ok | microphones; PC spectrum packets are dropped, the stats JSON is untouched |
| `-DAUDIO_MIC_ONLY` build | — | ok | microphones, fixed; the portal hides the source choice |

---

## 6. Budgets

| Buffer | Size | Where | Why there |
|---|---|---|---|
| I2S DMA | 4 × 256 frames × 4 B = 4 096 B, plus descriptors | internal | the driver allocates `MALLOC_CAP_DMA` |
| I2S event queue | 8 events | internal | the overflow counter |
| Task stack | 5 120 B | internal | stacks cannot be in PSRAM here; trim after reading `audioStackFreeBytes` |
| Shared frame | ≈0.7 KB | internal .bss | copied inside a spinlock |
| I2C (Wire) | driver plus small buffers | internal | **not measured**; shared with any other I2C user |
| Ring, window, FFT real and imaginary | 4 × 2 048 × 4 B = 32 768 B | PSRAM | |
| cos, sin tables | 2 × 1 024 × 4 B = 8 192 B | PSRAM | |
| Bit-reverse table | 2 048 × 2 B = 4 096 B | PSRAM | |
| DSP state, hop buffer, work frame | ≈6.5 KB | PSRAM | |
| **Total** | internal ≈10.5 KB + I2C; PSRAM ≈52 KB | | `/api/info` `audioInternalBytes` measures the internal side (free before the task, minus free once the codec is up; approximate) |

Flash and static RAM: §11.

**Latency**, estimated:

| Stage | Delay |
|---|---|
| sound to microphone at 1 m | 3 ms |
| ES7210 decimation filter | **unknown** (datasheet not read) |
| DMA buffer fill | up to 5.3 ms |
| hop accumulation | up to 20 ms |
| a transient reaching the analysed window | ≈10–20 ms; in the simulator kicks are detected 10–20 ms after their first sample (§11) |
| packet cadence, existing effects only | up to 40 ms |
| render at 60 Hz | up to 16.7 ms |
| DMA flip at the end of the panel's scan | up to one refresh (`main.cpp` comment above the clear) |

About 30–90 ms for the existing effects, 20–50 ms for effects reading the frame
directly, plus the codec. The PC path adds its own 40 ms block and Wi-Fi on top
of the same render. To be measured with a clap and a phone's slow-motion camera.

---

## 7. Settings

| Setting | Form / JSON key | NVS key | Range | Default | State |
|---|---|---|---|---|---|
| Source | `audioSource` | `audioSrc` | 0 auto, 1 PC, 2 mic | 0 | **built** |
| Microphone gain | `micGainDb` | `micGainDb` | 0–37 dB (PGA steps: 3 dB to 33, then 34.5, 36, 37.5) | 30 (Waveshare's example) | **built** |
| Noise gate | `micGateDb` | `micGateDb` | −90 … −30 dBFS | −60, starting value | **built** |
| AGC | `micAgc` | `micAgc` | on/off | on | **built** |
| Band count | — | — | fixed at 32 | 32 | not a setting: the packet, every effect and the wow designs index 32 bands |
| Effect | `vizStyle` | `vizStyle` | existing list | existing | exists; wow styles append after the owner's choice |
| Palette | per wow effect | — | e.g. synth, fire, ice, mono | per effect | with the wow effects |
| Beat reactivity | `vizBeatFx` | — | 0–100 % (flash, palette shift, particle count) | 60 % | with the wow effects |
| Beat sensitivity | `micBeat` | — | 1–10, scales K and the rise | 5 = today's numbers | after the real-music check |
| Auto-start on sound | — | — | like the companion's `VizAutoTrigger` | off | later |

The portal shows a **Sound source** card on the Audio visualizer page only when
`/api/portal` says the build has microphones (`audioMic`). The four values are
stored and exported in every build, so a settings backup moves between builds.

---

## 8. Failure states

| State | Detected by | The panel shows | `/api/info` |
|---|---|---|---|
| No codec (no ACK at 0x40) | the first I2C writes of `es7210::begin()`; retried every 30 s | with the mic as source: "No audio data..." after 2 s; auto falls back to the PC | `audioMic: "no codec"` |
| I2S install failed | `i2s_driver_install` / `i2s_set_pin`; retried every 30 s | as above | `"i2s failed"` |
| No PSRAM | a failed `heap_caps_calloc` | as above | `"no memory"` |
| No samples for 1 s | `i2s_read` returning nothing | codec brought up again; stale screen meanwhile | `"stalled"`, `audioStalls` |
| DMA overflow | `I2S_EVENT_RX_Q_OVF` | a glitch in one frame | `audioOverruns` |
| Silence | gated for 2 s | the effects' own empty look; wow designs fade to an idle state | `audioSilent` |
| Clipping | a sample at 32 700 or above | drawn normally | `audioClipping`; the portal hint says to lower the gain |
| Dead microphone | not detected yet: the mix of both halves one mic's level | lower bars | per-channel levels are a later field |

---

## 9. "Wow" upgrades

House style: black ground, bright but never blown out — **no channel above 235**,
no full white. Every design uses the GFX calls the panel already makes, plus at
most one PSRAM buffer. All have been rendered (§10).

| # | From | The look | Bass | Beat | Silence | Panel cost |
|---|---|---|---|---|---|---|
| W1 Prism EQ | Classic EQ | bars graded violet (bass) → green (treble), each brightening to its own top; caps held 350 ms then falling with gravity; a floor reflection | taller left bars | palette slides one step, a violet floor line flashes | caps settle, bars dark | ≈1 700 hline calls a frame, no buffer |
| W2 Neon Mirror+ | Neon Mirror | bars grow from the centre out, bass in the middle, mirrored up and down, a glow column beside each | the centre swells | cyan/magenta warm toward gold/violet, the horizon flashes | peak dots drift down | pixels only |
| W3 Spectrogram | Phosphor Waterfall | full-screen time–frequency history, 2.6 s wide, bass at the bottom, inferno palette | bright floor | bright column, amber tick on top | black | 128×64 B in PSRAM, a blit a frame |
| W4 Radial Bloom | Purple LED Stage | 64 spokes in four mirrored lobes (bass top and bottom, treble at the sides) round a breathing core, slowly turning | core radius | a violet shockwave ring expands and fades | a small dim ring | lines and circles |
| W5 Beat Particles | Starfield Overdrive | fountains of 18–58 particles from the bottom centre in the colour of the loudest band group, trails, drifting stars, a bass glow along the floor | floor glow, star drift | a fountain | slow stars | 128×64×3 B in PSRAM, ≤180 particles |
| W6 Scope Afterglow | Oscilloscope | the waveform on a phosphor that decays in ~90 ms, green shading to amber with deflection | slow swings | the trace thickens, the graticule brightens | a flat line | 128×64 B in PSRAM |
| W7 Twin VU | new | two analog meters, LO and HI, auto-ranging, needle inertia with a little overshoot, fading ghost needles, a red peak LED | the LO needle | the pivot caps glow | needles rest left | lines and circles |
| W8 Synthwave Grid | new | a striped sun on the horizon, mountains cut from the spectrum (bass at the edges) standing in front of it, a perspective grid rushing forward faster with the energy | the sun grows | grid flash and a speed kick | the grid idles, the ridge flattens | lines |

Beat-driven extras to share across all of them once built: a global brightness
pulse capped by the dimming schedule, a palette shift per beat, and a
`vizBeatFx` strength setting.

---

## 10. Previews

`APC/tools/audiofx/` (see its README):

```bash
cd APC
python3 tools/audiofx/gen_wavs.py          # six synthetic WAVs + ground truth
python3 tools/audiofx/render.py            # 14 GIFs, 14 MP4s, 2 contact sheets
make -C tools/audiofx/host check           # C++ DSP against the Python reference
```

Everything is rendered from `wav/showreel.wav` (5 s: kick and bass → full groove
with snares → an 80 Hz–12 kHz sweep → silence with 50 Hz hum below the gate → the
groove again). The current effects get a packet every 40 ms, as `vizIngest()`
would; the wow effects get every 20 ms frame; everything is drawn at 60 Hz.

| File (`APC/tools/audiofx/out/`) | What it shows |
|---|---|
| `contact_current.png`, `contact_wow.png` | one row per effect; stills at 0.62 s (kick), 1.90 s (groove), 2.95 s (sweep), 3.90 s (silence), 4.62 s (return) |
| `classic_eq.gif` | the shipping EQ fed by the microphones: green/yellow/red bars, red peak dots falling; kicks lift the left bars, the sweep walks a hump rightwards, silence empties it |
| `neon_mirror.gif` | cyan-up, purple-down segmented bars about the horizon; the same reactions at half height |
| `phosphor_waterfall.gif` | green and amber rows scrolling down; kicks leave short bright bands at the left, the sweep a diagonal, silence a black gap |
| `purple_led_stage.gif` | the dim purple lamp grid swaying, opening on bass; it was always low-contrast |
| `starfield_overdrive.gif` | stars flying with the bass, hyperspace boosts on kicks from its own packet flux |
| `oscilloscope.gif` | the trace with three ghosts; kicks as slow swings, the sweep fills the screen (the ÷8 decimation aliases above ~3 kHz, as the companion's does) |
| `w1_prism_eq.gif` … `w8_synthwave_grid.gif` | the eight designs of §9 |
| `*.mp4` | the same at 60 fps with the audio track, to judge sync |

---

## 11. What was built and checked

Branch `feat/audiofx-onboard-mic` in `APC`, local commits only.

| Part | Files |
|---|---|
| ES7210 driver | `src/audio/es7210.{h,cpp}` |
| DSP | `src/audio/audio_dsp.{h,cpp}` (portable, host-tested) |
| Capture task, source switch, adapter, `/api/info` | `src/audio/audio_mic.{h,cpp}`; hooks in `main.cpp`, `network/network.cpp`, `web/web.cpp` |
| Settings | `config/config.h`, `config/settings.cpp`, the portal card in `web/web_pages.h` |
| Build | `-DAUDIO_MIC_ENABLED` in `matrix-waveshare-rgb`; `-DAUDIO_MIC_ONLY` optional |
| Simulator and previews | `tools/audiofx/` |
| Host test | `tools/audiofx/host/` |

**Host test (C++ against Python, same WAVs), 2026-09-15:** all six files agree:
same frame count, same gate/beat/clip/silence/publish flags on every frame, band
bytes within ±1 (float32 FFT against numpy's float64), waveform bytes ±0, dB
±0.000. Beats: `kick120` 12/12 kicks, nothing else, mean 10 ms after the kick
starts; `showreel` 7/7, nothing else, 20 ms; `pink` none; one onset each where a
sound starts in `tone_1k_100` (the 100 Hz tone), `sweep` and `silence_clip`.

**Build and checks, 2026-09-15:**

| Check | Result |
|---|---|
| `pio run -e matrix-waveshare-rgb`, the env now carrying `-DAUDIO_MIC_ENABLED` | success, no compiler warnings |
| Static RAM | 100 576 → **101 640 B** (+1 064) |
| Flash | 2 146 893 → **2 205 053 B** (+58 160), 46.7 % of the 4.5 MB slot |
| `python3 tools/flag_matrix.py` | **42/42**. New rows: `mic on` builds, `mic only, no PC stream` builds, `mic only, no mic` refused by the `#error` in `audio_mic.cpp:5` (checked with the preprocessor); `everything` now includes the mic |
| `python3 tools/web_assets_gen.py --check` | passes: the Sound source card's four controls are filled by `/api/portal` |
| Pre-commit hook (`core.hooksPath=.githooks`) | ran on the integration commit (it staged `web_pages.h`, `web.cpp`, `web_assets.h`); clock styles unchanged, portal assets current |
| Host test | as above: C++ and Python agree on all six WAVs |

Commits, local, not pushed: `4965550` previews and the Python DSP; `5fa0e92`
ES7210 driver, C++ DSP, host test; `090005c` GIFs in real time; `e924c94`
capture task, source switch, `/api/info`, portal settings. The branch against
`776fc04`: 26 files, +4 039 / −1 011, of which about 2 000 lines are the
regenerated `web_assets.h`.

---

## 12. To test on the panel

1. **Codec present:** the serial line `[audio] ES7210 up`, `/api/info`
   `audioMic: "ok"`; an I2C scan shows 0x40.
2. **Levels and gain:** speech at 1 m and music at a normal level: read
   `audioLevelDb`, `audioAgcRefDb`, `audioClipping`; adjust the 30 dB default.
3. **Latency:** a clap filmed in slow motion with the Classic EQ and with W1;
   compare with the PC stream.
4. **Noise from the LED supply:** a silent room, panel on full white and on black,
   brightness 128 and 255. Watch `audioLevelDb` against the −60 dBFS gate and
   which bands light. The 5 V rail feeds both the panel and, through the 3V3
   buck, the ES7210 and its mic bias.
5. **Panel PWM coupling:** look for a steady line at the panel's refresh rate
   and its harmonics (`display.refreshRateHz()` prints under `MEM_TRACE`),
   and for beats firing on a static full-screen page.
6. **Speaker and amp:** there is no buzzer on the board; there is an NS4150B amp
   with a speaker header. With IO11 floating, check the speaker for hiss and the
   mics for feedback. The ES7210's MIC3 is probably the playback reference; unused.
7. **Wi-Fi bursts:** 2.4 GHz rectified in the mic preamp as a buzz at beacon rate:
   check for false beats while `/api/info` is polled fast.
8. **Boot:** the click from the ROM log on IO43; whether the codec comes up
   after every reset and after an OTA reboot.
9. **Real music against the beat numbers:** 5+ tracks of different genres
   through the room; count missed and false beats; then decide K, delta and the
   rise, and only then give them the portal setting.
10. **Budgets:** `audioInternalBytes`, `audioStackFreeBytes`, `audioDspUs` /
    `audioDspUsMax`, `loopMaxMs`, `freeInternalHeap`, with the Lua effects and a
    clip playing at the same time.
11. **Enclosure:** the mics need an acoustic path through the case ([10](10-mechanical.md)).

---

## 13. Upstream

[09](09-upstream-contributions.md) §4 still holds: "discuss first". What is
fork-only: the ES7210 driver and its pins (one board), the build flag, the
Sound source card, the wow effects until the owner picks. What could go upstream
as an idea: a local source feeding `vizIngest()` with the companion's packet
unchanged, and the portable DSP with its host test. The companion and its packet
need no change.

---

## 14. Sources

| Source | Used for |
|---|---|
| `SCH` (KB copy, Apache-2.0, Waveshare) | microphones, ES7210 straps, I2S and I2C nets, IO46 |
| `WS/components/bsp/esp32_s3_matrix/esp32_s3_matrix.c`, `include/bsp/config.h`, `include/bsp/esp32_s3_matrix.h` | pins, I2S format, I2C port and speed, ES7210 in slave mode |
| `WS/main/examples/08_Matrix_Audio/matrix_audio.c`, `components/Middleware/Audio/middle_audio.c` | 16 kHz stereo, 30 dB, two channels read as L/R |
| `CODEC/device/es7210/es7210.c`, `es7210_reg.h`, `device/include/es7210_adc.h`, `esp_codec_dev.c` | register sequence, coefficient table, address, gain codes, open order |
| `IDF/components/driver/i2s.c`, `components/hal/i2s_hal.c` | DMA allocation and limits, MCLK in RX-only master mode, slot mask |
| `FW/tools/sdk/esp32s3/include/driver/include/driver/i2s.h`, `hal/include/hal/i2s_types.h` | config fields, events, MCLK multiples |
| `SDK` | PSRAM malloc threshold, stacks, cores, tick rate |
| `FW/tools/sdk/versions.txt`, `tools/platformio-build-esp32s3.py` | IDF and esp-dsp versions, esp-dsp linked |
| [esp-dsp API reference](https://docs.espressif.com/projects/esp-dsp/en/latest/esp32/esp-dsp-apis.html) and [benchmarks](https://docs.espressif.com/projects/esp-dsp/en/latest/esp32/esp-dsp-benchmarks.html) (espressif-docs MCP) | FFT API, cycle counts |
| esp-dsp `modules/fft/float/dsps_fft2r_fc32_ansi.c` (master) | the init's allocations |
| context7 `/kosme/arduinofft` | ArduinoFFT API |
| context7 `/websites/librosa_doc`: `onset.onset_strength`, `util.peak_pick` | spectral flux, mean + delta + wait peak picking |
| [ESP-IDF 6.0 migration guide](https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/migration-guides/release-6.x/6.0/peripherals.html) | legacy I2S removed |
| `FW/libraries/Wire/src/Wire.cpp`, `libraries/Preferences/src/Preferences.h` | shared bus behaviour, `putChar`/`getChar` |
| `APC/src/viz/*`, `src/network/network.cpp`, `src/main.cpp`, `src/web/web.cpp`, `src/config/*` | the shipping visualizer and its plumbing |
| `COMP` | the packet: bands, AGC, waveform, cadence |
| Keralots/AnimatedPixelClock main `9e37721` (GitHub API) | upstream is identical |
| The HUB75 library header `ESP32-HUB75-MatrixPanel-I2S-DMA.h` `color565to888()`, Adafruit GFX `writeLine()`, `drawChar()` | pixel-exact previews |
| [02](02-controller.md), [07](07-sources.md), [12](12-bringup.md), [17](17-media-player.md) | earlier pin work, open questions |
