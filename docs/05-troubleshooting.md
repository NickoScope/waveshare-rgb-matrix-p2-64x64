# Troubleshooting: symptom → cause → fix

Assembled from issue #134 of ESP32-HUB75-MatrixPanel-DMA (the maintainer's own catalogue of
common failures), the esp-hub75 troubleshooting guide, and the ESPHome component docs.

## Main table

| Symptom | Likely cause | What to do |
|---|---|---|
| Black screen | wrong shift driver | Check power and ribbon first. Then try `FM6126A`: it is verified working on Waveshare P2.5 64x64 panels by a third party, and seven of Waveshare's ten Arduino examples set it, against a user guide that says GENERIC — see contradiction #4 in [07-sources.md](07-sources.md) |
| Black screen on a 64-row panel | pin E not configured | 1/32 scan requires E; on this board it is GPIO9 |
| Ghosting, duplicates offset horizontally | panel cannot keep up with the library's speed | `latch_blanking` up to 4, clock down to 10 or 8 MHz, brightness down to 128, shorter ribbon |
| Pixels off by one, x=0 column missing | clock phase | `clkphase = false` (`clock_phase` in ESPHome) |
| **Rightmost column or right-edge corner missing** | clock phase, the specific symptom on Waveshare FM6126A panels | `clkphase = false`. Verified on Waveshare P2.5 64x64 by the AnimatedPixelClock author. If instead the **first** column doubles or the image shifts, set it back to true |
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
| Boot loop: `assert failed: do_core_init startup.c:328 (flash_ret == ESP_OK)` right after `Octal Flash Mode Enabled` | the image was built for quad flash, and the module's flash is octal (`qio_opi` on a WROOM-2) | `board_build.arduino.memory_type = opi_opi`. Hit on our board on 2026-09-14 |
| Upload fails with "No serial data received" while the board boot-loops | the USB port drops with every reboot | `esptool.py --port <port> --after no_reset --connect-attempts 15 chip_id` catches it in the bootloader, then upload; or hold BOOT while plugging in |
| Colours washed out, pastel | an advanced HUB75 option was changed | reset to factory settings |
| **The panel vanishes from the network for minutes and comes back** | **look at `resetReason` before blaming anything else.** `1` is `ESP_RST_POWERON` - power was removed and restored, and nothing in the firmware did it. `3` is a software reset, which is what an OTA does. A crash would leave a `lastCrash` whose `thisBoot` and `sameFirmware` are both true; the one sitting in `/api/info` on 2026-09-22 was from an older image and a previous day, so it was not this. | Follow the number. It is right often enough to be trusted: on 2026-09-22 the panel was absent 09:13-09:19 and came back with `uptime 19 s` and `resetReason 1`. I had begun writing up a fault - and the owner said "that was me, I switched the power". The reading was correct and there was nothing to fix. **A reset reason of 1 with no other symptom usually means a person, a socket or a switch, not a defect.** |

## Reading a disappearance honestly

Three things look identical from a laptop - a panel that has lost power, one
whose Wi-Fi dropped, and one that crashed - and they need different fixes.
A fourth looks identical too and is the most common: **somebody unplugged it.**
Ask before writing an incident report; on 2026-09-22 the answer to a six-minute
disappearance was "that was me". The cheap way to tell them apart, in order:

1. **Is it really gone, or is your own resolver ill?** On 2026-09-22
   `nickol.local` stopped resolving from the Mac mid-session while everything
   was fine. Check from a second machine and by IP. `ip neigh` showing `FAILED`
   for the address, plus a ping sweep of the subnet that does not turn up the
   MAC, is a real absence.
2. **When it answers again, read `uptime` first.** Small and climbing means it
   rebooted; large means it only lost the link. This one number separates half
   the possibilities and it is free.
3. **Then `resetReason`, then `lastCrash` with `thisBoot` and `sameFirmware`.**
   A stale crash record from an older image is the most misleading thing on the
   panel: it is right there in `/api/info` and it belongs to a different day.

And one trap that is ours: mDNS advertisements outlive the device. `avahi` will
hand you a name, an address and a version from its cache for a panel that is no
longer there - the version comes from the TXT record, not from the panel. Only
an answer to `/api/info` is evidence. `discover.py` confirms every
advertisement for exactly this reason and marks the rest "advertised but not
answering"; its `--json` says `reachable: false`.

## Debug order for a panel that will not start

From the esp-hub75 guide, work the list:

1. A 5 V supply is connected to the panel with adequate current (3–5 A per 64x64 panel)
2. ESP32 ground is tied to supply ground
3. The correct board preset is selected, or all pins are set manually
4. Panel dimensions in the config match the physical panel, including scan type
5. The firmware actually flashed
6. The serial monitor shows successful driver initialisation

Recommended strategy: start with `GENERIC` and `STANDARD`, get *any* image even with wrong
colours, and only then start changing driver and scan settings. On Waveshare 64x64 panels
specifically, `FM6126A` is the likelier setting, so if GENERIC gives nothing at all, change
that before suspecting the wiring.

**Isolate the chain before blaming the driver.** With two panels a blank screen is
undiagnosable: it could be either panel, the ribbon, the driver init, or the wiring. Set the
chain length to 1, reflash, and drive only the panel wired to the controller. Once that
single panel lights, restore the chain and use a seam test (left half red, right half blue)
to validate the JOUT to JIN order. This is the recovery procedure from the AnimatedPixelClock
bring-up sketch, and it is the fastest way out of a dead-black screen.

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
