# Versus the Apollo Automation M-1

Context for why this hardware was chosen. The Apollo M-1 is the best-known turnkey
HUB75 product in the Home Assistant world, and it is the natural comparison.

## Is the Apollo panel a clone of the Waveshare one?

No — but neither is it an Apollo design. Both companies resell the same commodity part.

Waveshare's `RGB-Matrix-P2.5-64x64` (SKU 23708, $25.99) matches the Apollo panel on every
published parameter: 64x64, 2.5 mm pitch, 160 x 160 mm, 1/32 scan, dual HUB75 headers.
Apollo charges $36.99 for it.

A 64x64 panel at 2.5 mm pitch on a 160 x 160 mm board with 1/32 scan is an **industry
standard part**. Dozens of Shenzhen factories have built it for years for advertising
displays, and it is resold under many brands. None of them designed it.

Waveshare is a reseller here too, and says so: the panel wiki warns that silkscreen and
board layout change between batches while software compatibility is preserved. That is what
vendors write when they source from varying contract manufacturers.

No public evidence was found that Apollo buys panels from Waveshare specifically. The
specification match is a fact; the provenance of particular batches is not established.

**The controllers, by contrast, are definitely not clones.** Their HUB75 pin assignments
differ almost everywhere — Apollo Rev6 puts the clock on GPIO18 and the latch on GPIO8,
while Waveshare uses GPIO41 and GPIO40. Two independent designs.

## Panel comparison

| | Waveshare P2-64x64-B | Apollo M-1 panel |
|---|---|---|
| Resolution | 64 x 64 = 4096 | 64 x 64 = 4096 |
| Pitch | **2 mm** | 2.5 mm |
| Dimensions | **128 x 128 mm** | 160 x 160 mm |
| Diagonal | 181 mm | 226 mm |
| Screen area | 164 cm² | 256 cm² |
| Density | **25 dots/cm²** | 16 dots/cm² |
| Scan rate | 1/32 | 1/32 |
| Protection | **GOB** | none |
| Data connectors | two HUB75, in and out | JIN and JOUT |
| Power connector | VH4 | 4-pin header for their power module |
| Price | $31.99 | $36.99 |

Same pixel count, packed 1.6 times denser into half the area. Sharper image, physically
smaller, shorter comfortable viewing distance.

## Controller comparison

| | Apollo M-1 Rev6 | Waveshare ESP32-S3-RGB-Matrix |
|---|---|---|
| SoC | ESP32-S3 | ESP32-S3-N32R16 |
| Flash | 16 MB | **32 MB** |
| PSRAM | 8 MB octal | **16 MB octal** |
| Current on the 5 V rail | ~3 A | **10 A** |
| Power inputs | USB-C or WAGO | **two connectors** |
| Panels in cascade | 4 | **6** |
| Microphone | $6.99 add-on, one | **two onboard** |
| Audio output | none | **ES8311 + 8 Ω 5 W speaker included** |
| Echo cancellation | none | **ES7210** |
| IMU | none | **QMI8658, 6 axes** |
| Real-time clock | none | **PCF85063 with battery connector** |
| Temperature and humidity | none | **SHTC3** |
| Storage | none | **TF card slot** |
| GPIO expansion | none | **header** |
| Form factor | sized to hide behind the panel | 50 x 42 mm, mount it yourself |
| Price | $27.99 | **$24.99** |

Cheaper, with twice the memory, more than triple the current path, and a set of peripherals
Apollo simply does not have.

The practical consequence matters most: ten amps and two power inputs remove the problem
that makes an Apollo 2x2 build awkward, where each additional panel needs its own USB-C
charger because the controller's rail carries roughly one panel's worth.

## Where Apollo wins: software readiness

| Capability | Apollo | Waveshare |
|---|---|---|
| WLED | custom build on 16.0.1, factory presets, first-boot setup card, migration from WLED-MM | official upstream `ESP32-S3_Waveshare_HUB75.bin` |
| Browser-based installer | yes | no |
| Board preset in ESPHome core | `apollo-automation-m1-rev4` and `-rev6` | **none** |
| Prebuilt hub75-studio binary | rev4 and rev6 | **none** |
| hub75-studio controller package | yes | yes, but you write the top-level config |
| Documentation | a twenty-page wiki in plain language | Waveshare wiki, terse, partly machine-translated |
| Community | Discord, reviews, YouTube coverage | examples repo created 2026-04-23, three stars |
| Enclosure and mounting | stand, printable wall frames on Printables | screws in the box, the rest is on you |

## Cost of a 2x2 build, both routes

**Apollo**, from apolloautomation.com:

| Item | Qty | Each | Total |
|---|---|---|---|
| M-1 LED Matrix (controller + panel + stand) | 1 | $64.99 | $64.99 |
| Panel only | 3 | $36.99 | $110.97 |
| Data cable | 3 | $1.99 | $5.97 |
| Power module | 3 | $5.99 | $17.97 |
| **Hardware subtotal** | | | **$199.90** |

Plus four USB-C sources capable of 5 V / 3 A each, roughly $40–60, because the controller's
rail covers one panel. Apollo's own multi-panel kit, which bundled a charger, was sold out
at the time of checking. Realistic total lands near $260.

Note that buying the controller and one panel separately costs $64.98 against $64.99 for the
complete kit. There is no reason to split them.

**Waveshare**:

| Item | Qty | Each | Total |
|---|---|---|---|
| RGB-Matrix-P2-64x64 (SKU 23706, uncoated) | 4 | $28.99 | $115.96 |
| ESP32-S3-RGB-Matrix (SKU 34422) | 1 | $24.99 | $24.99 |
| 5 V 15–20 A supply | 1 | ~$30 | ~$30 |
| **Total** | | | **≈ $171** |

Roughly $90 cheaper, with a considerably cleaner power topology: one supply instead of four
chargers.

Caution for a 2x2 on this board: four P2 panels at worst case draw 12 A against the board's
10 A rating. Cap brightness, or feed the panels directly.

## Firmware requirement for a 2x2 grid on Apollo

Worth recording because it is easy to miss. A 1x4 row and a 2x2 grid are not the same thing
on Apollo hardware. The grid needs WLED 16.0.1, which requires a **Rev6** controller; Apollo's
build notes confirm 1x4 and 2x2 verified on hardware. The older WLED-MM 14.5.1 documentation
covers horizontal rows only. Alternatively hub75-studio with `layout_rows: 2`,
`layout_cols: 2`.

## Summary

**Gained by going Waveshare:** eight dollars on the pair, twice the PSRAM for effects, twice
the flash, a current path three times wider with two inputs, two microphones with echo
cancellation instead of a paid add-on, a speaker, an IMU, a clock, a climate sensor, a card
slot, a GPIO header, GOB protection on a fine-pitch panel, and a six-panel cascade limit
instead of four.

**Given up:** out-of-the-box readiness. No web installer, no factory presets, no board
preset in ESPHome, no prebuilt hub75-studio binary, no stand or frames, and noticeably drier
documentation. The picture is also physically smaller, 128 mm against 160.

Better hardware, assembled by hand.
