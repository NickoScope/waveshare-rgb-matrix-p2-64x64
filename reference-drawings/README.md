# Vendor drawings

Kept locally so the software can be checked against the hardware without a
round trip to the internet — and so that what we verified against is still
there to re-check later.

## Controller — ESP32-S3-RGB-Matrix (SKU 34422)

| File | What it is |
|---|---|
| `controller/ESP32-S3-RGB-Matrix-Schematics.pdf` | full schematic, one page |
| `controller/ESP32-S3-RGB-Matrix-2D.pdf` | board outline and mounting |

Source: [waveshareteam/ESP32-S3-RGB-Matrix](https://github.com/waveshareteam/ESP32-S3-RGB-Matrix),
`hardware/`. **Apache License 2.0** — redistribution permitted; the copyright
stays with Waveshare Electronics.

Fetched 2026-09-10:

```
cbe74d347afbc5dd…  ESP32-S3-RGB-Matrix-Schematics.pdf   205 745 B
2cb249fe4275bab7…  ESP32-S3-RGB-Matrix-2D.pdf           165 502 B
```

Refresh with `tools/fetch-vendor-drawings.sh`.

## Panel — RGB-Matrix-P2-64x64-B (SKU 33838)

| File | What it is |
|---|---|
| `RGB-Matrix-P2-64x64.dwg` | factory 2D drawing, the only hardware document that exists |
| `panel-2d.zip` | the archive it came in |

Source: `files.waveshare.com/wiki/RGB-Matrix-P2-64x64/RGB-Matrix-P2-64x64.zip`.

### Waveshare publishes no schematic for the panel

Searched 2026-09-10, so that nobody repeats it:

| Where | Result |
|---|---|
| Wiki page `RGB-Matrix-P2-64x64` | four downloads, none a schematic |
| Wiki page `RGB-Matrix-P2-64x64-B` | does not exist |
| `files.waveshare.com/wiki/RGB-Matrix-P2-64x64/` | seven likely filenames probed, all 404 |
| Product page | no resources block |
| `Packages.rar` (122 MB) | the Arduino ESP32 core 1.0.6 cache. Nothing to do with the panel |
| `English_Character_Display_Principle.pdf` | a generic font-rendering tutorial for e-Paper. Boilerplate |
| `RGB-Matrix-P2-64x64-Demo.zip` (20 MB) | example code for ESP32, Pico, RPi and STM32. Code, not hardware |

This is normal and not a gap. The panel is a commodity HUB75 module: its entire
interface is the connector pinout, which is in [docs/01](../docs/01-panel.md),
and its scan behaviour, which is 1/32 with E mandatory. There is no board for a
schematic to describe beyond the LED array and its shift drivers — and which
shift driver it carries is exactly the thing a schematic would have settled and
does not exist to settle. Phase 2 of the [bring-up](../docs/12-bringup.md)
answers it empirically instead.

The demo archive is worth knowing about even though it is not kept here: it is
a fifth independent statement of the panel's interface, across four platforms,
should the pinout ever need re-checking.

## Why this matters for the software

The pin map in [docs/02](../docs/02-controller.md) was verified against three
independent vendor **code** sources. The schematic is the fourth, and the only
one that is the hardware rather than a description of it. Anything that
contradicts it wins.
