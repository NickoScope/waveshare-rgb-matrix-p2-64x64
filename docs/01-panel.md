# Panel: Waveshare RGB-Matrix-P2-64x64-B

SKU 33838, part number `RGB-Matrix-P2-64x64-B`. The GOB-coated variant.
$31.99 on waveshare.com. The uncoated version (SKU 23706) is $28.99.

## Specifications

| Parameter | Value |
|---|---|
| Resolution | 64 x 64 = 4096 dots |
| Pixel pitch | 2 mm |
| Dimensions | 128 x 128 mm |
| Pixel composition | 1R1G1B |
| Viewing angle | ≥140° |
| Control method | synchronous |
| Scan rate | **1/32 scan** |
| Interface | HUB75 |
| Supply | 5 V / 3 A via VH4 socket |
| Power draw | ≤15 W |
| Protection | GOB coating |

Source: docs.waveshare.com/RGB-Matrix-Px-64x64 and waveshare.com/wiki/RGB-Matrix-P2-64x64.

Note the discrepancy: the spec table says 3 A, but the product page separately recommends
**a 5 V 4 A supply**. Size the supply from the recommendation, not the table.

## What GOB gives you — and what it does not

Waveshare's own wording: the GOB (Glue On Board) coating process improves the impact
resistance of the LED screen and reduces the risk of LED damage during disassembly,
transportation and installation, and is especially suited to fine-pitch displays.

Physically it is a layer of transparent epoxy poured over the mounted LEDs. The surface
becomes monolithic, and individual LEDs stop protruding and acting as levers under impact.

**What Waveshare does not claim:** water resistance, an IP rating, or outdoor suitability.
The spec table carries exactly one line, `Protection: GOB coating process`. LED display
manufacturers' blogs advertise IP65 for GOB products, but that is about their own products.
FYI only, and not grounds to treat this panel as weatherproof.

**The trade-off** (FYI, from industry sources rather than Waveshare): a single dead LED
under the epoxy cannot be desoldered. Repair becomes panel replacement.

At a 2 mm pitch the coating earns its keep — the finer the pitch, the smaller and more
fragile the individual LEDs.

## HUB75 pinout

| Pin | Function | Pin | Function |
|---|---|---|---|
| +5V | 5 V power input | GND | ground |
| R1 | red, upper half | R2 | red, lower half |
| G1 | green, upper half | G2 | green, lower half |
| B1 | blue, upper half | B2 | blue, lower half |
| A | row select bit 0 | B | row select bit 1 |
| C | row select bit 2 | D | row select bit 3 |
| E | row select bit 4 | CLK | clock input |
| LAT/STB | latch | OE | output enable |

**Pin E is mandatory here.** The panel has 64 rows and a 1/32 scan rate; without E the
image falls apart.

A warning straight from the Waveshare wiki: silkscreen and board layout **vary between
production batches** while remaining software-compatible. Trust the markings on your own
board, not photographs found online.

## Connectors

Two HUB75 headers: one input from the controller, one output to the next panel in a chain.
Power arrives separately through a VH4 socket.

## Box contents

| Item |
|---|
| GOB panel |
| 2 x 8-pin cable, ~30 cm |
| 16-pin flat ribbon cable, ~200 mm |
| VH4 2-pin cable, ~500 mm |
| Power terminal adapter |
| Magnetic screws, 4 pcs |

## Mandatory check before first power-on

Waveshare issues this as a standalone warning: **measure the voltage at the terminal
adapter output before connecting the panel.** If the meter reads minus five volts, the
terminal polarity is wrong and the part must be replaced through support.

The panel runs on 5 V only. Any other voltage destroys it.

## Platform support

Waveshare documents tested operation with Raspberry Pi, Raspberry Pi Pico, ESP32,
Arduino Mega2560 and STM32F103RBT6. The Raspberry Pi path uses
`hzeller/rpi-rgb-led-matrix` and supports up to three panels per Pi.

## Versus the Apollo M-1 panel

| | Waveshare P2-64x64-B | Apollo M-1 panel |
|---|---|---|
| Pitch | 2 mm | 2.5 mm |
| Dimensions | 128 x 128 mm | 160 x 160 mm |
| Density | 25 dots/cm² | 16 dots/cm² |
| Protection | GOB | none |
| Price | $31.99 | $36.99 |

Same pixel count, packed 1.6 times denser into half the area. Sharper, but physically
smaller. Full comparison in [08-apollo-m1-comparison.md](08-apollo-m1-comparison.md).
