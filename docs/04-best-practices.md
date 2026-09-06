# Best practices

Read before first power-on. Most of these were paid for with somebody else's burnt panel.

## Power — the source of most problems

**Rule one: the panel is fed from its own supply, never from the ESP32 board's 5 V pin.**
Both the ESPHome documentation and the DMA library README say this outright.

| Item | Value |
|---|---|
| Our panel, datasheet | 5 V / 3 A, ≤15 W |
| Our panel, Waveshare's recommendation | a 5 V **4 A** supply |
| Formula from the ESPHome docs | (width x height / 2) x 0.06 A at full white |
| For 64x64 by that formula | 2048 x 0.06 = **~1.9 A** |

The formula lands at roughly half the datasheet figure. The gap makes sense: the formula
assumes only two rows are lit at any instant at 1/32 scan, while the datasheet quotes the
worst case. **Design to the datasheet, not the formula.**

Non-negotiables:

- Supply ground and ESP32 ground **must be tied together**. Separate grounds produce flicker.
- Never exceed 5 V. The panel will not survive it.
- Measure the terminal adapter polarity before the first connection. Minus five volts means
  a reversed connector — do not attach the panel.
- Fit a 1000–2000 µF capacitor across the panel's power input. The DMA library states this
  as a strong recommendation: without it, rapid changes in bright content cause supply
  droop and visible flashing.

## Brightness: do not max it out

Every library defaults to 128 of 255, i.e. 50 percent. That is deliberate and sufficient
for most purposes.

FYI, from secondary sources: a sensible everyday range is 80–120; full brightness heats the
panel substantially and shortens LED life. These thresholds are not verified against an LED
datasheet and must not drive decisions, but the direction is sound — heat and degradation
climb faster than perceived brightness.

Separately: Apollo's WLED instructions disable the automatic brightness limiter. That means
no software current ceiling, so the power budget is entirely on you.

## Ghosting and flicker

Order of operations when duplicate pixels appear offset horizontally:

1. **Raise latch blanking.** It controls how many clock pulses the output is blanked via OE
   before and after the LAT transition. Default 1, range 1–4. Above 4 there is no benefit,
   only lost brightness.
2. **Lower the clock.** From 20 MHz down to 10 or 8 MHz.
3. **Lower brightness** to 128 or below.
4. **Shorten the ribbon.** Not a figure of speech — issue #134 of the DMA library names long
   wiring as a direct cause, with video evidence.

The canonical pair from the library documentation:

```cpp
mxconfig.latch_blanking = 4;
mxconfig.i2sspeed = HUB75_I2S_CFG::HZ_10M;
```

If pixels are offset by exactly one coordinate, or the x=0 column is invisible, that is
clock phase rather than ghosting. Fix with `mxconfig.clkphase = false`. Some panels latch
data on the falling edge, others on the rising edge.

## Signal levels

HUB75 panels are designed for 5 V logic; the ESP32 drives 3.3 V. Strictly speaking it works
by luck — the shift registers' input thresholds usually sit below 3.3 V.

**This board is fortunate:** it carries an SN74HC245 buffer, so the level problem is solved
in hardware. On a bare ESP32 with a long ribbon this is a leading cause of flicker, and
people add an external 74AHCT245 there.

If rows fail to light for no apparent reason, the documentation suggests metering a GPIO in
its HIGH state — it should read 3.3 V. Less than that means a defective ESP32.

## Wi-Fi and electromagnetic interference

A known ESP32-S3 issue: the high-frequency DMA output couples into the sensitive radio when
the PCB is not laid out to minimise EMF. The DMA library README names the Adafruit
MatrixPortal S3 specifically as problematic with Wi-Fi.

No such reports were found for this board, but if Wi-Fi starts dropping while the panel is
active, this is the likely cause rather than your router.

## Memory and bit depth

- More bits per colour means better colour and a lower refresh rate. The default of 8 is a
  reasonable balance.
- Double buffering removes tearing but doubles DMA buffer memory. Disable it when using LVGL.
- The library raises `lsbMsbTransitionBit` on its own if it cannot hit the configured
  `min_refresh_rate`, and that silently reduces perceived colour depth. Demanding 120 Hz on
  a long chain therefore costs colour without telling you.

## Thermal

FYI: a panel in a sealed enclosure at full brightness reaches 50–60 °C. If you build a case,
provide ventilation. The specific numbers are not verified by measurement, but the
requirement itself is not in doubt.

## Strapping pins

Not directly relevant here — the routing is already done for us. It matters if you hang
something off the GPIO header. The awkward ones on ESP32: GPIO0 (boot mode select), GPIO2,
GPIO5, GPIO12 (flash voltage), GPIO15.

## Commissioning order

1. Meter the power terminal polarity.
2. Assemble on the bench, short ribbon, panel face up.
3. Flash the smoke test or WLED, brightness no higher than 128.
4. Confirm all 64 x 64 pixels light and the colours are correct.
5. Only then build the enclosure and hang it on a wall.

A diagnostic tip from the library README: the `PIO_TestPatterns` example draws plain colours,
lines and gradients across the whole matrix, which makes ghosting and flicker easy to spot.
