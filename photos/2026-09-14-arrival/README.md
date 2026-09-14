# Photos — 2026-09-14, the day the hardware arrived

Taken by the owner on the bench. Re-encoded for this repository: turned upright,
all metadata removed (the originals carried no location), JPEG quality 85.

| Photo | What it shows | Used for |
|---|---|---|
| [controller-front.jpg](controller-front.jpg) | ESP32-S3-RGB-Matrix, component side. The module is marked `MCN32R16V`; two USB-C sockets are silkscreened **USB** and **POWER**; posts marked 5V and GND; BOOT and RESET buttons; the GPIO header reads GND, 3V3, IO46, IO45 | phase 1: module identity, header order, the second USB-C |
| [controller-back.jpg](controller-back.jpg) | The other side: two TI `HC245` buffers beside the 2×8 HUB75 header | the level shifters on the schematic |
| [panels-back-chained.jpg](panels-back-chained.jpg) | Two `RGB-Matrix-P2-64x64-B` panels, PCB `DCHY-P2-6464-1515-VP`, chained OUT → IN with the ribbon, power harness on both | batch record for phase 0; wiring for phase 3 |
| [panel-chips-mw245bc-fm6124hj.jpg](panel-chips-mw245bc-fm6124hj.jpg) | Next to HUB-75E IN: input buffers `MW245BC` (U1, U2) and a column driver `FM6124HJ` (GU2) | question 1, the driver chip |
| [panel-chips-fm6124hj-ruc7258g.jpg](panel-chips-fm6124hj-ruc7258g.jpg) | Column drivers `FM6124HJ` on the green, red and blue channels (GU4, RU4, BU4), and 16-pin `RUC7258G` parts (UT5–UT7), not identified | question 1 |

Two of the four panels are in these photos; the other two are still to be
checked against the same markings.
