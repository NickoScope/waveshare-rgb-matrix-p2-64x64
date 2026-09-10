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
| `RGB-Matrix-P2-64x64.dwg` | factory 2D drawing |
| `panel-2d.zip` | the archive it came in |

Source: `files.waveshare.com/wiki/RGB-Matrix-P2-64x64/`. Mechanical only —
Waveshare publishes **no schematic** for the panel itself, which is normal: the
panel is a commodity HUB75 module and its interface is the connector pinout,
already recorded in [docs/01](../docs/01-panel.md).

## Why this matters for the software

The pin map in [docs/02](../docs/02-controller.md) was verified against three
independent vendor **code** sources. The schematic is the fourth, and the only
one that is the hardware rather than a description of it. Anything that
contradicts it wins.
