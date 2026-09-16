# The panel as a Music Assistant player — research and design

**Status 2026-09-16: research only. No code on the panel, nothing flashed.** The
owner asked for the board's *whole* audio module: streaming playback from Music
Assistant, announcements with the music ducked, the two microphones with noise
suppression and echo cancellation, and the existing visualizer folded into the
same module rather than fighting it.

This document says what the hardware can actually do, with the numbers, and
names the one constraint that shapes every design here.

## 0. Summary — the verdict in numbers

1. **Playback from MA is feasible.** The cheapest honest route needs **no audio
   decoder at all**: both Snapcast and slimproto can be told to send raw PCM
   (§1.1). That removes 28–89 KB of decoder state and 6–8 % of a core.
2. **Announcements with the music ducked are NOT available on any route we can
   implement.** True ducking — music keeps playing, quieter, with the clip mixed
   over it — exists in MA for exactly one route we could take (AirPlay), and
   there the mixing is done **on the server**, not the device. Every other route
   stops the music, plays the clip, and resumes (§1.2). This is the owner's
   stated requirement and it is the thing that does not fit.
3. **The binding constraint is the board, not the chip.** BCLK and WS are shared
   between ES8311 and ES7210 on the PCB, and an I2S port carries **one sample
   rate for both directions**. Playback and capture therefore cannot run at
   different rates — and a second I2S controller does not fix it, because the
   shared wire is what forces it (§4).
4. **Voice (wake word + AEC) does not fit.** Espressif's own figure for our exact
   configuration — two microphones plus a reference channel — is **79.1 KB of
   internal SRAM**, against **~33 KB free** on this firmware. That is not "tight",
   it is two to three times over (§6).
5. **The speaker is an announcement speaker, not a music speaker.** The amplifier
   runs from **3.3 V**, read off the schematic, so its ceiling into the supplied
   8 Ω driver is about **0.68 W** (§3.2).

**What is proposed:** a module that plays a PCM stream from Music Assistant and
feeds the visualizer from what it plays, with announcements accepted in MA's
stop-and-resume form. Ducking, microphones and voice are explicitly out of scope
until the heap debts of [22](22-audio-visualizer-onboard-mic.md) §12.3 are paid.

---

## 1. How a device becomes a Music Assistant player

MA reached over its own API on the owner's network: **Music Assistant add-on
2.10.3**, Home Assistant **2026.9.2**. Read live, read-only, 2026-09-16.

### 1.1 The routes, compared

Source for the whole table is the MA server tree at commit `8756e45`, read
directly; the provider directory listing and each provider's `constants.py` /
`player.py` were opened.

| Route | First-class MA player? | Grouping | Can it be sent raw PCM? | Native announcements | ESP32 reality |
|---|---|---|---|---|---|
| **slimproto / Squeezelite** | yes — the richest: `PLAY_MEDIA`, `ENQUEUE`, `GAPLESS_PLAYBACK`, `PAUSE`, `POWER`, `VOLUME_SET`, `SET_MEMBERS`, `MULTI_DEVICE_DSP` | yes, MA's own playpoint algorithm | **yes** — `output_codec = wav` | **no** → stop / play / resume | `sle118/squeezelite-esp32` is a whole firmware, not a library; needs ≥4 MB PSRAM; S3 "compiles & runs", not in releases |
| **Snapcast** | partial — `PLAY_MEDIA`, `VOLUME_SET`, `VOLUME_MUTE`, `SET_MEMBERS`, `PLAY_ANNOUNCEMENT`; no `PAUSE`, no `ENQUEUE`, always flow mode | yes, snapcast's own | **yes** — `snapcast_server_built_in_codec = pcm` | yes, but **stream switching, not ducking** | protocol is small enough to write ourselves; server ships inside MA |
| **ESPHome `media_player` via HA** | mirrors the HA entity's features | only if the entity declares it | device declares its formats | yes — and the **device** ducks | makes the whole board an ESPHome project |
| **DLNA / UPnP** | `PLAY_MEDIA`, `ENQUEUE`, `GAPLESS`, conditional volume/pause | **no** | per-player codec | **no** | no ESP32 renderer found — NOT VERIFIED |
| **AirPlay (as receiver)** | `PLAY_MEDIA`, `PLAY_ANNOUNCEMENT`, `SET_MEMBERS`, `MULTI_DEVICE_DSP`, volume | yes | 44.1 kHz/16 PCM, ALAC on the wire | **yes — real ducking, done on the server** | writing an AirPlay receiver is the largest job of all |
| **Sendspin** (MA's own protocol) | volume/mute per client capability; queue, metadata, sync | yes | native format is PCM | only via a bound HA entity | ESPHome component, marked experimental; needs IDF ≥ 5.x |

Verified in the owner's own MA instance: a `squeezeplay:` player and a DLNA
player already exist there, and the flagship `NickoScope32 Audio S3` node is a
live MA player. Its `supported_features` decodes to `8320575`, which includes
`MEDIA_ANNOUNCE`, `GROUPING`, `MEDIA_ENQUEUE` and `SEARCH_MEDIA`.

**Why "raw PCM" is the headline.** At 48 kHz / 16 bit / stereo a PCM stream is
**192 000 B/s (187.5 KB/s)**. In exchange the firmware carries no decoder:
no 28 KB of MP3 state, no 89.4 KB of FLAC state, no 6–8 % of a core (§5.1).
On a board whose scarce resource is internal SRAM, that trade is the whole
design.

### 1.2 Announcements — the mechanism, and why the owner's ask does not fit

This is the part the owner cared about most, so it is spelled out from the code
rather than the documentation (the two disagree — see §9).

MA renders the **chime and the announcement into a single clip** before it plays
anything (`controllers/streams/announcements.py`), then does one of four things:

| Behaviour | Who does it | Which routes |
|---|---|---|
| **True duck + mix** — music never stops, drops in level, clip mixed over it | the **MA server** (`cliairplay`) | **AirPlay only** |
| **Stream switching** — the group is moved to a separate announcement stream and back | MA | Snapcast |
| **Delegated to Home Assistant** — `media_player.play_media` with `announce: True`; the *device* ducks | the device's own firmware | hass_players (ESPHome), Sendspin |
| **Stop → play → resume** | MA | **slimproto, DLNA**, and everything that does not declare `PLAY_ANNOUNCEMENT` |

The AirPlay path is the only real ducking, and its constants are explicit —
read personally in `providers/airplay/constants.py`:

```
AIRPLAY_ANNOUNCE_DUCK_DB     = -18   # "-12 was field-judged too shallow";
                                     # "<= -60 mutes the music entirely"
AIRPLAY_ANNOUNCE_DUCK_LEAD_S = 0.5   # ducked silence before the clip
AIRPLAY_ANNOUNCE_DUCK_TAIL_S = 1.0   # ducked silence after it
```

The clip is wrapped in that ducked silence so the announcement volume can be
raised and restored inside a window where the music is already quiet. The
binary "mixes a raw-PCM clip over the outgoing music with the music ducked
underneath — no flush, no re-anchor". **The receiver does nothing for this**:
it is handed one already-mixed stream. That is why AirPlay is the only route
where ducking costs the device nothing — and also the route that is hardest to
implement.

Announcement volume settings, read from `music_assistant/constants.py`:

| Key | Default |
|---|---|
| `announce_volume_strategy` | `percentual` (options: `absolute`, `relative`, `percentual`, `none`) |
| `announce_volume` | 85 |
| `announce_volume_min` | 15 |
| `announce_volume_max` | 75 |
| `tts_pre_announce` | true; the chime ships as `helpers/resources/announce.mp3` |

**Consequence for us.** Choosing Snapcast or slimproto means accepting that an
announcement interrupts the music. MA's own feature request for ducking on
queue-flow players ("Sendspin, Snapcast, Squeezelite") was closed as a duplicate
with no implementation. Promising the owner ducking on those routes would be a
promise the server cannot keep.

### 1.3 The full player feature list

`PlayerFeature`, read in full from `music-assistant/models`,
`music_assistant_models/enums.py` — 16 real members plus `UNKNOWN`:

`POWER`, `VOLUME_SET`, `VOLUME_MUTE`, `PAUSE`, `SET_MEMBERS`,
`MULTI_DEVICE_DSP`, `SEEK`, `NEXT_PREVIOUS`, `PLAY_ANNOUNCEMENT`, `ENQUEUE`,
`SELECT_SOUND_MODE`, `SELECT_SOURCE`, `OPTIONS`, `GAPLESS_PLAYBACK`,
`GAPLESS_DIFFERENT_SAMPLERATE`, `PLAY_MEDIA`.

The deprecated value `sync` maps to `SET_MEMBERS`. The enum's own docstring
documents an `accurate_time` member **that does not exist** — see §9.

### 1.4 The route nobody proposed: `PlayerType.VISUALIZER`

Found while reading the enums, and worth recording because it fits this project
exactly. `PlayerType` (same file) contains:

```
VISUALIZER = "visualizer"   # "A device that visualizes music on a screen
                            #  (e.g. animations, LED matrices)"
DISPLAY    = "display"      # "shows metadata (e.g. album art, track info)
                            #  but does not play audio"
```

MA has first-class player types for a device that **shows** music without
playing it. That is what this panel already is today via `src/media/`. Whether a
third-party device can register as one of these without an in-tree provider is
**NOT VERIFIED** — no documented out-of-tree player-provider API was found. But
it reframes the question: the panel does not have to play audio to be a citizen
of Music Assistant.

---

## 2. Our own yard: what NickoScope32 actually has

The owner pointed at the latest NickoScope32 release, whose name contains
`radiola_input`, as existing audio work to port. It was checked file by file
(`NickoScope32_ESP32S3_v33.55.0_fx32_radiola_input_2026-08-27`).

**There is nothing to port.** The grep is the evidence:

| Searched | Files hit |
|---|---|
| `i2s` / `I2S` | 1 (a comment in `main.cpp`) |
| `es8311` | 0 |
| `helix`, `libhelix`, `minimp3`, `opus`, `flac` | 0 |
| `AudioGenerator`, `AudioFileSource`, `ESP32-audioI2S` | 0 |

What that tree's "audio" actually is:
- `audio_capture.cpp` — **ADC** capture of a DFPlayer's analog DAC output on
  GPIO7/GPIO8, FFT, packets over ESP-NOW. Not streaming, not I2S.
- `audio_browser.cpp` — a track browser driving a **DFPlayer** module.
- `echo_chimes.cpp` — Westminster chimes sent over ESP-NOW to an **Atom Echo**.
- `loud_uart.cpp` / `loud_metadata.cpp` — NSP commands and LRCLib lyrics for a
  **separate** "Loud" ESP32 that does the Spotify playback.

Every one of those is a remote control or an analog tap for audio produced by
*another device*. The genuine prior art is not there but in
[17](17-media-player.md): the flagship's U601 audio node, which is an **ESPHome
on IDF 5.x** design and does not port into this firmware (arduino-esp32 2.0.17 =
IDF 4.4.7).

---

## 3. The hardware, read off the schematic

`reference-drawings/controller/ESP32-S3-RGB-Matrix-Schematics.pdf` in this
repository, rendered at 400 dpi and read page by page. Everything in this
section was read from the drawing itself, not from the vendor's prose.

### 3.1 The audio chain as wired

| Signal | GPIO | Goes to |
|---|---|---|
| I2S MCLK | 12 | both codecs |
| I2S SCLK (BCLK) | 43 | **both codecs — one wire** |
| I2S LRCK (WS) | 38 | **both codecs — one wire** |
| I2S DSDIN | 21 | ES8311 (U9) input |
| I2S ASDOUT | 39 | ES7210 (U10) output, through **R39 51 Ω** in series |
| PA_CTRL | 11 | NS4150B (U7) CTRL, through R27 0 Ω |

ES7210's I2C address is set by straps and confirmed on the drawing: **R32 and
R33 are NC, R36 and R37 are 0 Ω to AGND**, so AD1 = AD0 = 0 → 7-bit address
`0x40`. That matches what `src/audio/es7210.h` already states, so the firmware's
existing driver is right about the address for the right reason.

### 3.2 The amplifier, and what it can really deliver

The part is **NS4150B (U7)**, a filterless mono class-D amplifier. Three things
read off the drawing matter:

1. **Its supply is 3V3, not 5 V.** Pin 6 `VDD` runs to the `3V3` net, decoupled
   by C46 10 µF / C47 100 nF / C48 1 µF.
2. **`PA_CTRL` is pulled down by R28 10 kΩ to AGND.** The amplifier is therefore
   **off by default** until GPIO11 is driven high. This answers an open worry
   recorded in `src/audio/README.md` ("GPIO11 floats from reset"): electrically
   it does not float, it is held low.
3. **The output filter is not fitted.** `PA_OUTL+` and `PA_OUTL−` pass through
   L4 and L5, both **0 Ω links**, and C42 / C43 / C45 are all marked **NC**,
   straight to the J2 PH2.0 2P speaker connector.

**What that means for loudness.** A bridged (BTL) class-D output from a 3.3 V
rail can swing at best about 3.3 V peak across the load, so into the supplied
8 Ω driver the ceiling is

> P = V²pk / 2R = 3.3² / (2 × 8) ≈ **0.68 W**

and about 1.36 W into 4 Ω. This is arithmetic from the confirmed supply rail,
not a measurement, and it ignores THD and switch losses — the real figure is
lower. The "8 Ω 5 W" in the brief is the **speaker's** rating, i.e. what the
driver tolerates, not what this board delivers into it.

⚠️ The NS4150B datasheet itself could **not** be read: datasheet4u returned 403,
the LCSC PDF returned only a page title, utmel returned a browser check. The
distributor card states 3 V–5.25 V supply and "3 W into 4 Ω at 5 V" — that is a
**secondary source, NOT VERIFIED**, and there is no first-party figure at all
for 8 Ω or for 3.3 V. The verdict above does not depend on it: it rests on the
supply rail, which was read from the schematic.

### 3.3 The echo-cancellation reference path — it exists

This was the one genuinely open hardware question, and the drawing settles it:

```
ES8311 OUTP ──[ R18  0Ω ]── ADC_MIC3_P ──[ C62 1µF ]── ES7210 pin 31 (MIC3P)
ES8311 OUTN ──[ R23  0Ω ]── ADC_MIC3_N ──[ C63 1µF ]── ES7210 pin 32 (MIC3N)
```

So the board **does** carry a playback-reference loopback into the ADC's third
channel, AC-coupled, exactly the convention Espressif uses on ESP32-S3-Korvo-2.
Without it, acoustic echo cancellation could not work at all on this board;
with it, AEC is *physically* possible and only the CPU budget stands in the way
(§6).

Two details worth recording:
- The reference is taken from the **ES8311 DAC output**, not from the amplifier
  output. Distortion and clipping introduced by the NS4150B are therefore
  invisible to the reference, and an AEC fed from it cannot cancel them.
- **MIC4 is not routed.** `MIC4P`/`MIC4N` appear only as pin names on the ES7210
  symbol; no `ADC_MIC4*` net exists anywhere in the drawing.

### 3.4 ES7210: what is silicon and what is marketing

Waveshare calls the ES7210 an "echo cancellation chip". **It is not.** The
datasheet's FEATURES list a four-channel delta-sigma ADC, 102 dB SNR, TDM
support and a low-power standby — and contain no mention of echo, cancellation,
noise suppression or beamforming. Espressif's own driver writes only high-pass
filters, per-channel gain, microphone power and the serial format. The chip's
role in "echo cancellation" is to provide the **extra ADC channel** that carries
the reference signal (§3.3); the cancelling is arithmetic done on the ESP32-S3.

Espressif defines the term that causes the confusion: hardware AEC "is when the
reference signal comes from a chip other than the main controller (such as
ES8311 or ES7210)" — the label describes where the *reference* comes from, not
where the *computation* happens. The computation is ours either way.

### 3.5 ES8311 registers that matter

From the ES8311 datasheet (Rev 6.0, May 2019), read in full:

| Function | Register | Detail |
|---|---|---|
| Master/slave | `0x00` bit 6 `MSC` | 0 = slave (default) |
| MCLK source | `0x01` bit 7 `MCLK_SEL` | 0 = MCLK pin (default), **1 = derive from BCLK** |
| Word length (DAC) | `0x09` bits 4:2 | 0 = 24-bit (default), 3 = 16-bit |
| **Channel select** | `0x09` bit 7 `SDP_IN_SEL` | **0 = left channel to DAC (default)** |
| Volume | `0x32` | 8-bit, `0x00` = −95.5 dB, **0.5 dB per step**, `0xBF` = 0 dB, `0xFF` = +32 dB |
| Mute | `0x31` bits 6 and 5 | `DAC_DSMMUTE`, `DAC_DEMMUTE`; the Espressif driver sets both (`0x60`) |
| Volume ramp | `0x37` bits 7:4 | **0 = soft ramp disabled (default)** |

Two of these have consequences we must design around:

- **The chip is mono and takes the left channel only.** It does not sum L+R. A
  stereo stream played as-is loses everything that is only in the right channel.
  The downmix `(L+R)/2` must be done on the CPU.
- **The volume ramp is off by default**, so volume and mute changes step
  abruptly. If clicks are audible, `0x37` is the register to enable.

There is **no MCLK/LRCK ratio table** in the datasheet — only a statement that
standard 64/128/256/384/512 Fs clocks are supported, and limits of MCLK ≤ 51.2
MHz, LRCK ≤ 200 kHz. The practical list of proven ratios is the `coeff_div[]`
table in Espressif's driver, which includes 256 Fs (12.288 MHz at 48 kHz) —
the ratio our existing microphone code already uses.

---

## 4. The binding constraint: one sample rate per I2S port

This is the single most important finding in this document, and it was checked
three ways.

### 4.1 What the SDK we compile against actually says

Read locally, in the exact SDK this firmware builds with (arduino-esp32 2.0.17 /
ESP-IDF 4.4.7):

| Fact | File |
|---|---|
| Full duplex is a named, first-class feature: `i2s_hal_enable_master_fd_mode()`, `i2s_hal_enable_slave_fd_mode()` | `tools/sdk/esp32s3/include/hal/include/hal/i2s_hal.h:163-174` |
| The mechanism is a shared bit clock and word select: `i2s_ll_share_bck_ws()` writes `tx_conf.sig_loopback` | `hal/esp32s3/include/hal/i2s_ll.h:882-885` |
| MCLK binds to one direction's clock (`rx_clkm_conf.mclk_sel`) | `hal/esp32s3/include/hal/i2s_ll.h:107-120` |
| `i2s_mode_t` is a bit field, so `MASTER\|TX\|RX` is one port's configuration | `hal/include/hal/i2s_types.h:113-127` |
| The ESP32-S3 has two I2S controllers | `soc/esp32s3/include/soc/soc_caps.h:129`, `SOC_I2S_NUM (2)` |

And the legacy driver, read in IDF 5.5.4's copy of it, states the rule in a
comment:

```c
if (p_i2s[i2s_num]->dir == (I2S_DIR_TX | I2S_DIR_RX)) {
    i2s_ll_share_bck_ws(p_i2s[i2s_num]->hal.dev, true);
    /* Since bck and ws are shared, only tx or rx can be master
       Force to set rx as slave to avoid conflict of clock signal */
    is_rx_slave = true;
}
```

The modern driver enforces the same thing explicitly: full duplex is constituted
only when the two channels' sample rate and total frame bits match, and the
later-initialised channel is forced to slave.

**So: playback and capture can run at once on I2S0 — at one shared sample rate
and one shared frame width, with the receive side as clock slave.**

### 4.2 A second I2S port does not help

It is tempting to put ES8311 on I2S0 and ES7210 on I2S1. The chip has two
controllers and the GPIO matrix can feed one input pin to several peripherals,
so "one master, one slave on shared clocks" is electrically constructible.

**It still does not give two sample rates**, because on this board BCLK and WS
are *one wire each*, shared by both codecs (§3.1). Word-select frequency *is*
the sample rate. Two ports would buy independent DMA, independent slot layouts
and independent start/stop — not independent rates. This is a constraint of the
PCB, not of the driver, and no amount of software fixes it.

### 4.3 The three ways out, priced

The visualizer runs at 48 kHz today; music is usually 44.1 kHz; the voice
pipeline requires 16 kHz (ESP-SR supports no other rate for AEC).

| Option | What it costs | Verdict |
|---|---|---|
| **One shared rate, resample in software** | 48 kHz everywhere; MA is told to send 48 kHz (both Snapcast and slimproto can be pinned, §1.1), so **no resampling on the playback path at all**. Only a voice path would need 48→16 kHz decimation | **Chosen.** Costs nothing today because we are not building the voice path |
| Second I2S controller | independent DMA and slot layouts, still one rate; costs a second driver instance and its DMA buffers in internal RAM | Not worth it until something needs different slot layouts |
| Time-sharing (stop one direction, reconfigure, start the other) | changing a rate requires disabling the channel; if the *master* direction stops, the shared clocks stop with it | Rejected: audible gaps, and the surviving direction loses its clock |

The first option is free precisely because MA can be pinned to 48 kHz — which is
also the rate the existing DSP and the ES7210 already run at (`audiodsp::kFs =
48000`, MCLK 256 Fs = 12.288 MHz).

---

## 5. The cost of playing audio at all

### 5.1 Decoder cost — and why we pay none of it

Espressif's `esp_audio_codec` v2.4.0, measured on ESP32-S3R8:

| Decoder | Rate / channels | Memory | CPU |
|---|---|---|---|
| MP3 | 44.1 kHz stereo | 28 KB | 8.17 % |
| FLAC | 44.1 kHz stereo | 89.4 KB | 8.0 % |
| AAC-LC | 48 kHz stereo | 51.2 KB | 6.75 % |
| Opus | 48 kHz stereo | 26.6 KB | 5.86 % |

Its own caveats: these are heap only, **a further ~20 KB of stack per decoder**
is needed, and AAC with SBR is dearer than the AAC-LC figure.

**We pay none of this** by pinning the transport to PCM (§1.1). That decision is
worth 28–89 KB of heap and 6–8 % of a core, on a board where both are scarce.
The price is bandwidth: 187.5 KB/s at 48/16/2.

### 5.2 Internal SRAM — the real budget

Measured on this panel, from [22](22-audio-visualizer-onboard-mic.md) §12.1:

| | |
|---|---|
| Free internal heap, idle | **32 952 B** |
| Largest free block, idle | 20 468 B |
| Microphone capture, while running | **−10.4 KB** |
| Minimum after boot | 15 332 B |
| Minimum observed during the hang | **504 B** |

The HUB75 double buffer is **not** negotiable: moving it to PSRAM freed ~130 KB
and striped the picture ([03](03-firmware.md), HANDOFF). Task stacks cannot live
in PSRAM. DMA descriptors cannot live in PSRAM. So every one of those numbers is
the real ceiling.

A PCM player's internal cost is then: the I2S TX DMA buffers, one task stack,
and the socket. Everything else — the stream ring buffer, the resampler if any,
the PCM staging — goes to PSRAM, of which 16 MB is free.

### 5.3 Why the visualizer hangs the panel, and what must change

The current failure is documented in [22](22-audio-visualizer-onboard-mic.md)
§12.2: capture holds 10.4 KB, a portal page load spikes ~20 KB more, internal
heap reaches 504 B, Wi-Fi's own allocations fail (`caps 0x80c`), MQTT then
blocks `loop()` for 3 s at a time.

**The new module must not repeat this**, which means three rules rather than
good intentions:

1. **A heap gate before the stream starts, as a number.** Refuse to start unless
   free internal heap and the largest free block clear thresholds set from
   measurement on the panel — not guessed here.
2. **Every stream buffer in PSRAM, explicitly**, with `MALLOC_CAP_SPIRAM`, as
   `src/audio` already does for the DSP.
3. **Debt D1 first.** The ~20 KB portal spike is the actual cause of the hang;
   adding a second internal-heap consumer before it is fixed would reproduce the
   fault with a different name.

The visualizer then gains something it does not have today: when the panel plays
the music itself, the PCM is already in hand, so the visualizer can be fed from
**playback** with no microphone, no ES7210, no I2S RX channel and no acoustic
path at all. That is strictly cheaper and strictly cleaner than the microphone
route, and it is the strongest argument for this module existing.

---

## 6. Voice: wake word and echo cancellation

Espressif's published resource figures for the audio front end, for our exact
configuration — two microphones plus one reference channel (`MMNR`):

| Pipeline | Internal RAM | PSRAM | CPU |
|---|---|---|---|
| AEC → BSS → VAD → WakeNet, low cost | **79.1 KB** | 1153.7 KB | 23.7 % + 22.9 % |
| AEC → NS → VAD, one mic, low cost | 48.7 KB | 819.7 KB | 30.6 % |
| AEC alone, one channel, cheapest mode | 18.8 KB | 64 KB | 7.2 % |
| WakeNet9, 2 channels | 16 KB | 324 KB | ~3 ms / 32 ms |

Against **32 952 B free**, the full configuration is over budget by a factor of
two to three — before the AFE's feed buffer (which the Arduino HAL allocates
`MALLOC_CAP_INTERNAL`), before three task stacks (4 + 8 + 6 KB), and before
Wi-Fi.

For comparison, Home Assistant's own Voice Preview Edition pairs an ESP32-S3
having **8 MB PSRAM** with a **separate XMOS XU316** audio processor that does
the echo cancellation in hardware. That is the shape of the problem: HA did not
run AEC on the ESP32 either.

**Verdict: hearing a wake word while the panel plays music does not fit on this
chip.** Ducking by −20 dB, as ESPHome does, reduces the echo but does not remove
it; without AEC the microphone hears the speaker. What *does* fit is a wake word
**while the speaker is silent** — and that is a different product from the one
that was asked for.

⚠️ The ESP-SR benchmark page is titled for ESP32-S3 but its own test-setting note
says **ESP32-P4** at 240 MHz. That is a contradiction inside Espressif's own
document; the figures are quoted as published and must not be presented as
measured on an S3.

---

## 7. The decision

**Approved by the owner, 2026-09-16 21:42**, after the scope above was put to
him in plain terms - what the board can do, what Music Assistant will not give
us, and how loud it will actually be. His words: the functionality suits him.
So the shape below is settled and is no longer a proposal:

- a Music Assistant player that plays, takes volume, groups with other rooms
  and shows metadata;
- announcements in MA's stop-and-resume form, ducking accepted as absent;
- the visualizer fed from what the panel itself plays, which is the way to get
  the screen dancing without the microphones that hang it today;
- a talking speaker rather than a music one - about 0.68 W into 8 ohms;
- no microphones, no echo cancellation, no wake word while the speaker sounds.


**Build: a PCM player for Music Assistant, behind its own flag, feeding the
visualizer from what it plays.**

- **Transport: Snapcast client with `codec = pcm`.** It is the smallest protocol
  of the candidates, MA ships the server, it gives volume, mute, grouping and
  metadata, and it needs no decoder. Its announcements switch streams rather
  than ducking — accepted, with the limitation stated plainly rather than
  papered over.
- **slimproto stays the fallback**, since `output_codec = wav` makes the
  transport a plain HTTP GET and it is the richer player (gapless, enqueue,
  metadata on the device). It is worth a second look if Snapcast's missing
  `PAUSE` turns out to matter.
- **Rate: 48 kHz / 16 bit / stereo**, matching the existing DSP and the ES7210's
  configuration, so the shared-clock constraint of §4 costs nothing.
- **Downmix `(L+R)/2` on the CPU** before I2S, because the ES8311 would
  otherwise discard the right channel (§3.5).
- **Amplifier discipline:** raise GPIO11 only after the codec is configured and
  samples are flowing; drop it before stopping I2S. The 10 kΩ pulldown means the
  amplifier is safely off until we say otherwise (§3.2).

**Not built, and why:**

| Not built | Reason |
|---|---|
| Announcements with ducking | MA does not offer it on any route we can implement (§1.2) |
| Microphones, AEC, noise suppression | 79.1 KB internal against ~33 KB free (§6) |
| Wake word / HA voice satellite | same budget, plus it wants the ESPHome stack |
| Any decoder (MP3/FLAC/AAC) | unnecessary once the transport is PCM (§5.1) |

**Order of work:** debt D1 of [22](22-audio-visualizer-onboard-mic.md) §12.3
first — the portal's ~20 KB internal spike — because it is the live cause of the
hang and no audio module is safe on top of it. Then the module skeleton behind
its flag with a host test. Then, and only then, the stream on hardware with the
heap gate measured rather than assumed.

---

## 8. What is not verified

- **The NS4150B datasheet was never read.** Three sources refused (403, page
  title only, browser check). Its supply range and output power are from a
  distributor's card. No first-party figure exists for 8 Ω or for 3.3 V.
- **The 0.68 W figure is arithmetic**, from a confirmed 3.3 V rail, not a
  measurement, and ignores THD and switching losses.
- **Nothing in this document has run on the panel.** No codec was initialised, no
  stream was played, no heap figure for a player was measured.
- **The ESP-SR figures** are Espressif's published table, whose own note names a
  different chip (§6).
- **Whether a third-party device can register as an MA `VISUALIZER` or `DISPLAY`
  player** without an in-tree provider — no out-of-tree player-provider API was
  found documented (§1.4).
- **Snapcast client on ESP32-S3**: the community client `CarlosDerSeher/snapclient`
  states "ESP32 or ESP32-S2" in its README while carrying an
  `sdkconfig.defaults.esp32s3` in its tree. Not resolved.
- **The schematic was read, not traced.** Net names and component values were
  read off the drawing at 400 dpi; no continuity was followed through vias.

## 9. Contradictions found

1. **MA's documentation versus MA's code.** The Announcements page says only
   Sonos S2 and Sendspin support announcements natively. The code has
   `PLAY_ANNOUNCEMENT` declared by **snapcast, airplay, hass_players, sonos,
   samsung_wam, bose_soundtouch, yandex_station and sendspin**. The code wins.
2. **"Ducking is not supported" versus `airplay/announce.py`.** Maintainers in
   discussion #998 say ducking exists only for Sonos and Sendspin; the AirPlay
   provider implements genuine server-side mixing with a −18 dB duck. Both are
   true of different routes, which is exactly why §1.2 is a table and not a
   sentence.
3. **Waveshare calls the ES7210 an "echo cancellation chip".** Its datasheet
   contains no such function (§3.4).
4. **The brief's "8 Ω 5 W" speaker** versus a 3.3 V amplifier whose ceiling is
   ~0.68 W into 8 Ω (§3.2). The rating is the driver's, not the board's.
5. **Opus cost:** Espressif measures 5.86 % of a core; ESPHome calls Opus
   "extremely CPU and memory intensive" and S3-with-PSRAM only. Different
   implementations, unresolved — and moot for us, since we decode nothing.
6. **MA's `PlayerFeature` docstring** documents an `accurate_time` member that
   the enum does not contain (§1.3).
7. **ESP-SR's benchmark page** is titled ESP32-S3 and tested on ESP32-P4 (§6).
8. **The 150 kΩ resistors** reported as being in the AEC reference path are not:
   R26/R29 150 kΩ sit in the **amplifier input** path
   (`OUTP/OUTN → 100 nF → 150 kΩ → PA_INL±`). The reference path uses 0 Ω links
   (§3.3). Corrected by reading the drawing.

## 10. Sources

**Read personally, in full or in the cited part.**

| Source | Used for |
|---|---|
| `reference-drawings/controller/ESP32-S3-RGB-Matrix-Schematics.pdf` (this repo), rendered 400 dpi | §3 entire: the AEC reference path, NS4150B and its 3V3 rail, PA_CTRL pulldown, unfitted output filter, unrouted MIC4, ES7210 address straps, R39 51 Ω |
| music-assistant/server @ `8756e45`: `providers/airplay/{announce,constants}.py`, `providers/snapcast/{constants,provider}.py`, `constants.py`, `controllers/players/announcements.py` | §1.1, §1.2, announcement constants and codec options |
| music-assistant/models: `music_assistant_models/enums.py` | §1.3 `PlayerFeature`, §1.4 `PlayerType` |
| arduino-esp32 2.0.17 SDK, locally installed: `hal/i2s_hal.h`, `hal/esp32s3/.../i2s_ll.h`, `hal/i2s_types.h`, `soc/esp32s3/.../soc_caps.h`, `driver/i2s.h` | §4.1, the full-duplex and shared-clock mechanism in the version we compile against |
| ESP-IDF 5.5.4 tree, locally installed: `components/driver/deprecated/i2s_legacy.c`, `components/esp_driver_i2s/{i2s_std,i2s_common,i2s_tdm}.c` | §4.1, the rule stated in the driver's own comment |
| ES8311 datasheet Rev 6.0 (May 2019) | §3.5, registers, volume steps, mono channel select, ramp default |
| ES7210 datasheet Rev 22.0 | §3.4, what the chip does and does not do |
| Live Music Assistant 2.10.3 / Home Assistant 2026.9.2, read-only over the API | §1.1, the players that exist on the owner's network and their feature masks |
| NickoScope32 `…_v33.55.0_fx32_radiola_input_2026-08-27`, file by file | §2 |
| This repository: [02](02-controller.md), [03](03-firmware.md), [17](17-media-player.md), [22](22-audio-visualizer-onboard-mic.md), `HANDOFF.md` | §3.1, §5.2, §5.3, prior art |

**Not read personally — treat as secondary.**

| Source | Marked |
|---|---|
| NS4150B specifications (LCSC distributor card) | §3.2, §8 — datasheet refused three times |
| ESP-SR benchmark tables, `esp_audio_codec` v2.4.0 figures, micro-mp3 / micro-flac benchmarks | §5.1, §6 — published figures, not reproduced here |
| MA documentation pages, ESPHome component docs, squeezelite-esp32 and snapclient READMEs | §1.1, §6 — used for claims, contradicted by code where noted |
