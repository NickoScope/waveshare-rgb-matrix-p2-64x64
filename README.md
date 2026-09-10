# Waveshare RGB-Matrix-P2-64x64 + ESP32-S3-RGB-Matrix

Knowledge base for the Waveshare **RGB-Matrix-P2-64x64-B** LED panel (SKU 33838, GOB
version) driven by the Waveshare **ESP32-S3-RGB-Matrix** controller board (SKU 34422).

Everything here is traced to a primary source. The complete board pinout was verified
against Waveshare's own firmware sources, not copied from a forum post.
See [docs/07-sources.md](docs/07-sources.md) for the full audit trail.

Compiled 2026-09-06.

## Quick start

If the hardware has not been powered up yet, read in this order:

1. [The panel](docs/01-panel.md) — specs, pinout, what GOB actually gives you
2. [The controller](docs/02-controller.md) — **the verified pin map**, peripherals, power
3. [Best practices](docs/04-best-practices.md) — **read this before first power-on**
4. [Firmware](docs/03-firmware.md) — pick a path and get something on screen

## Contents

| Document | Covers |
|---|---|
| [01-panel.md](docs/01-panel.md) | RGB-Matrix-P2-64x64-B: specifications, HUB75 pinout, GOB coating, box contents |
| [02-controller.md](docs/02-controller.md) | ESP32-S3-RGB-Matrix: SoC, memory, power budget, **complete verified pin map** |
| [03-firmware.md](docs/03-firmware.md) | WLED, ESPHome, ESP-IDF, Arduino — what to choose and how to install |
| [04-best-practices.md](docs/04-best-practices.md) | Power, ghosting, flicker, brightness, memory, wiring |
| [05-troubleshooting.md](docs/05-troubleshooting.md) | Symptom → cause → fix |
| [06-projects.md](docs/06-projects.md) | Community projects worth building on |
| [07-sources.md](docs/07-sources.md) | Every source, every contradiction found, what is still unverified |
| [08-apollo-m1-comparison.md](docs/08-apollo-m1-comparison.md) | How this hardware compares to the Apollo Automation M-1 |
| [09-upstream-contributions.md](docs/09-upstream-contributions.md) | Roadmap for contributing this board back to the AnimatedPixelClock project |

## Ready-to-use configs

| File | Purpose |
|---|---|
| [configs/esphome/waveshare-matrix.yaml](configs/esphome/waveshare-matrix.yaml) | Minimal ESPHome config: one 64x64 panel, onboard sensors, brightness entity |
| [configs/arduino/smoke_test/smoke_test.ino](configs/arduino/smoke_test/smoke_test.ino) | Smoke test: prove the panel is alive before building anything around it |

Pin assignments in both files are verified. **Neither config has been compiled or flashed**,
so treat them as reviewed drafts rather than tested artifacts.

## The one thing worth knowing up front

Waveshare laid this board out on the **default ESP32-S3 pinout of the
`mrcodetastic/ESP32-HUB75-MatrixPanel-DMA` library**. Thirteen of fourteen pins match
upstream exactly. The single difference is pin E, which upstream leaves unassigned
(`-1`) because only 1/32-scan panels need it, and which Waveshare routed to GPIO9.

Practically: any sketch built on that library runs on this board with no pin configuration
at all. One line is enough.

```cpp
mxconfig.gpio.e = 9;
```

## Enclosure

An open design for a 128 x 64 wall panel built from two of these matrices lives in
[enclosure/](enclosure/): the design brief, three front-composition options and the split
scheme. The mechanical constraints behind it come out of the factory drawing —
[docs/10-mechanical.md](docs/10-mechanical.md).

## Flight board simulation

Lives with the firmware, not here:
[NickoScope/AnimatedPixelClock](https://github.com/NickoScope/AnimatedPixelClock/tree/board/waveshare-esp32-s3-rgb-matrix/sim),
branch `board/waveshare-esp32-s3-rgb-matrix`, directory `sim/`.

## Fact-checking convention

| Marker | Meaning |
|---|---|
| unmarked | verified against a primary source, cited in 07-sources.md |
| FYI | secondary source or industry practice — must not drive decisions |
| UNVERIFIED | taken from a third-party config or a blog, needs checking against hardware |
