# Draft: note to Keralots, the Waveshare board's GPIO header is free

**Status: NOT POSTED.** Written 2026-09-17 at the owner's "напиши об этом хорошую новость Рафалю".
Goes on issue #3, the running thread, only on his "отправляй".

## Why it is news for him

He ships the Waveshare ESP32-S3-RGB-Matrix as one of his three targets since v2.3.1, and on
2026-09-16 he asked for the measured IO45 idle level if we ever solder a receiver
(issue #3, comment 5716011106). What we can tell him now is better than one voltage: **the header
is not blocked at all**, and the two things anyone hanging a part on it needs to know are already
paid for by our evening of debugging.

## The facts, and where each comes from

| Fact | Source |
|---|---|
| Header U8 is GND, 3V3, IO46, IO45 | board silkscreen, `photos/2026-09-14-arrival/controller-front.jpg` |
| Four resistor positions sit next to the connector: **two fitted, two empty** | the same photo, marked up in `photos/2026-09-14-arrival/controller-gpio-pull-resistors.png` |
| **The pull-up positions are open on our board, and IO45-GND and IO46-GND both read 10 kΩ** | the owner's meter, 2026-09-17 23:05 and 23:13 |
| The fitted pair are 10 kΩ pull-downs (R59, R60); the empty pair are the pull-up positions (R57, R58) | `reference-drawings/controller/ESP32-S3-RGB-Matrix-Schematics.pdf`, and [11](../11-control-and-pins.md) |
| A knob wired common-to-GND reads zero on both lines at rest and gives no steps; common to 3V3 and active-high reading works | our bench, 2026-09-14 ([11](../11-control-and-pins.md)) |
| GPIO45 does not select VDD_SPI on this module: the N32R16V carries an ESP32-S3R16V whose VDD_SPI is set by eFuse | ESP32-S3-WROOM-2 datasheet §1.2, §8; ESP32-S3 hardware design guidelines. **Documented, not read off our own board** - `espefuse.py summary` is still to be run |
| GPIO46 gates ROM logging and, with GPIO0, the download mode | esptool, *Boot Mode Selection* |
| 2.2 kΩ into an empty pull-up pad gives ~2.74 V idle against the fitted 10 kΩ, above the 0.75 × VDD the S3 needs, and 1.6 mA sunk while the receiver pulls down, inside the part's 5 mA | Vishay [82459](https://www.vishay.com/docs/82459/tsop48.pdf) rev 2.4 and the divider; **arithmetic, not measured** ([24](../24-ir-remote.md)) |

## English (to post as a comment on issue #3)

```text
Some good news about the Waveshare board, since it is one of your three targets now.

Its four-pin header (GND, 3V3, IO46, IO45) is genuinely free. Nothing on the board claims those two GPIOs, and both strapping roles are harmless here. GPIO45 selects VDD_SPI only on a bare chip - the WROOM-2 module has it set by eFuse, so its level at reset does not matter (module datasheet and the S3 hardware design guidelines; I have not read the eFuse off my own board yet). GPIO46 gates the ROM log and, with GPIO0, the download mode, so the single rule is: do not hold it high at reset, or "hold BOOT through reset" stops working.

Two practical things, both visible on the board right next to that connector. There is a block of four resistor positions there: the two pull-downs are fitted and the two pull-up positions are empty. Measured on my board, not just read off the drawing: 10k from IO45 to GND and from IO46 to GND, and the pull-up pads open.

1. A rotary encoder needs no extra parts, but its common goes to 3V3, not to GND, and the firmware has to read A and B active high. Wired common-to-GND it reads zero on both lines at rest and gives no steps. That cost me an evening before I read the schematic.

2. An IR receiver's output is an open collector with a 30k pull-up inside the package, and against a fitted 10k pull-down that idles at 0.8 V - the decoder would see one endless burst. It needs a pull-up, and the empty pad is exactly where it goes, no flying resistor: 2.2k there gives about 2.7 V idle, above the 0.75 x VDD the S3 wants for a one, and 1.6 mA sunk while the receiver pulls down, inside its 5 mA rating. That part is arithmetic from the Vishay datasheet - I still have not soldered a receiver, so it is not measured.

So if anyone asks whether that board can take a knob or a remote: both, on the header, with nothing more than one resistor in a pad that is already there.

A photo of that resistor block, marked up:
https://github.com/NickoScope/waveshare-rgb-matrix-p2-64x64/blob/main/photos/2026-09-14-arrival/controller-gpio-pull-resistors.png

Nikolay
```

## Русский (для чтения, не публикуется)

```text
Хорошая новость про плату Waveshare, раз она теперь одна из твоих трёх целей.

Её четырёхпиновый разъём (GND, 3V3, IO46, IO45) действительно свободен. На плате эти две ноги ничем не заняты, и обе роли strapping здесь безобидны. GPIO45 выбирает напряжение VDD_SPI только у голого чипа — у модуля WROOM-2 оно прошито в eFuse, так что уровень на этой ноге при сбросе не имеет значения (даташит модуля и руководство Espressif по схемотехнике S3; на своей плате eFuse я пока не читал). GPIO46 управляет выводом ROM-лога и вместе с GPIO0 выбором режима загрузки, поэтому правило одно: не держать его в единице при сбросе, иначе перестанет работать вход в загрузчик удержанием BOOT.

Две практические вещи, и обе видно на плате прямо у разъёма. Там стоит блок из четырёх мест под резисторы: две подтяжки вниз запаяны, два места под подтяжки вверх пустые. Измерено на моей плате, а не только прочитано по схеме: 10 кОм с IO45 на землю и с IO46 на землю, площадки подтяжек вверх — обрыв.

1. Энкодер работает без единой лишней детали, но его общий провод идёт на 3,3 В, а не на землю, и прошивка читает A и B активными в единице. С общим на земле обе линии в покое читаются нулём и шагов нет вообще. Мне это стоило вечера, пока не открыл схему.

2. У ИК-приёмника выход — открытый коллектор с подтяжкой 30 кОм внутри корпуса, и против запаянных 10 кОм вниз линия в покое стоит на 0,8 В — декодер увидит один бесконечный импульс. Ему нужна подтяжка вверх, и пустая площадка — ровно то место, куда она ставится, без висящего в воздухе резистора: 2,2 кОм дают около 2,7 В в покое, выше 0,75 × VDD, которые S3 считает единицей, и 1,6 мА, которые приёмник тянет вниз, при допустимых 5 мА. Это арифметика из даташита Vishay — приёмник я так и не припаял, так что не измерено.

Так что если кто-то спросит, можно ли повесить на эту плату ручку или пульт: и то и другое, на разъём, и всей обвязки — один резистор в площадку, которая уже есть.

Фото этого блока резисторов с подписями:
https://github.com/NickoScope/waveshare-rgb-matrix-p2-64x64/blob/main/photos/2026-09-14-arrival/controller-gpio-pull-resistors.png

Николай
```
