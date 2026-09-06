# Troubleshooting: symptom → cause → fix

Assembled from issue #134 of ESP32-HUB75-MatrixPanel-DMA (the maintainer's own catalogue of
common failures), the esp-hub75 troubleshooting guide, and the ESPHome component docs.

## Main table

| Symptom | Likely cause | What to do |
|---|---|---|
| Black screen | wrong shift driver | Check power and ribbon first. Then try `FM6126A`: Waveshare's guide says GENERIC, but seven of their ten Arduino examples set FM6126A — see contradiction #4 in [07-sources.md](07-sources.md) |
| Black screen on a 64-row panel | pin E not configured | 1/32 scan requires E; on this board it is GPIO9 |
| Ghosting, duplicates offset horizontally | panel cannot keep up with the library's speed | `latch_blanking` up to 4, clock down to 10 or 8 MHz, brightness down to 128, shorter ribbon |
| Pixels off by one, x=0 column missing | clock phase | `clkphase = false` (`clock_phase` in ESPHome) |
| Blurred image | clock phase, the other way | `clkphase = true` |
| Flicker, garbage on screen | weak or unstable supply | adequate supply, exactly 5 V, 1000 µF across the panel's power input |
| Flicker with a good supply | separate grounds | tie supply ground to board ground |
| Half the screen coloured, half dark | panel size configured as 32x32 instead of 64x64 | fix the configuration |
| Interlaced bands, doubled image | a quarter-scan variant selected | return to Standard / half scan |
| Wrong colours | RGB lines swapped | check R1/G1/B1 and R2/G2/B2. Some panel batches ship with a factory error in the R2/G2 wiring |
| Some rows dark | GPIO not reaching 3.3 V | meter it; below spec means a defective board |
| Screen went black after changing HUB75 settings | that is how WLED behaves | reboot, this is expected |
| Garbage on exactly half of one panel | defective panel | return it, there is no software fix |
| Wi-Fi degrades while the panel runs | DMA interference into the radio | known ESP32-S3 class issue, see 04-best-practices |
| Port not detected when flashing | board not in download mode | hold BOOT, plug in USB, release BOOT, press RESET after upload |
| Colours washed out, pastel | an advanced HUB75 option was changed | reset to factory settings |

## Debug order for a panel that will not start

From the esp-hub75 guide, work the list:

1. A 5 V supply is connected to the panel with adequate current (3–5 A per 64x64 panel)
2. ESP32 ground is tied to supply ground
3. The correct board preset is selected, or all pins are set manually
4. Panel dimensions in the config match the physical panel, including scan type
5. The firmware actually flashed
6. The serial monitor shows successful driver initialisation

Recommended strategy: start with `GENERIC` and `STANDARD`, get *any* image even with wrong
colours, and only then start changing driver and scan settings.

## Panel height versus scan rate

| Panel height | Scan rate |
|---|---|
| 16 px | 1/8 |
| 32 px | 1/16 |
| **64 px** | **1/32** |

Our panel is 64 rows, 1/32, and pin E is mandatory.

## What to collect before asking for help

From the esp-hub75 issue template:

- ESP32 variant (S3 here)
- board model (ESP32-S3-RGB-Matrix)
- panel size and model (RGB-Matrix-P2-64x64-B)
- number of panels
- board preset or pin map
- panel settings: dimensions, scan wiring, bit depth
- layout if using multiple panels
- shift driver setting
