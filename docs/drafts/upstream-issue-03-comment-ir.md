# Draft: comment on Keralots/AnimatedPixelClock issue #3, the infrared remote

**Status: POSTED 2026-09-16 22:02 CEST** on the owner's "публикуй":
https://github.com/Keralots/AnimatedPixelClock/issues/3#issuecomment-5703737437
Written at his "не хочешь рассказать о наших наработках разработчику?". Posted
as drafted, 3,323 characters, verified against the posted body.

- **Where:** a comment on https://github.com/Keralots/AnimatedPixelClock/issues/3 — the
  same thread where Rafał set the PR order.
- **Voice:** the owner's. Plain, correct English, no salesmanship, numbers where
  a claim needs one.
- **State of play, checked 2026-09-16 21:55:** Rafał answered on 2026-09-15 14:55
  UTC; our microphone comment went up at 20:22 UTC and **has had no reply in
  24 hours**. PR #4 (TLS buffers in PSRAM) is merged; no PR is open. By his own
  order the next one from us is #2, the weather task half.
- **The fact that shapes the whole letter:** `src/` upstream has no encoder and
  no buttons — `gh api repos/Keralots/AnimatedPixelClock/contents/src` lists
  ambient, clocks, config, display, metrics, network, notify, viz, weather, web,
  and a code search for "encoder" and for "button" returns 0. So a remote is not
  a replacement for a knob for him. It is **the first way to control his panel
  without a phone**, and the letter says it that way round.
- **No PR is offered.** He asked for optional modules to stay in the fork, and
  this is one. The letter tells him it exists, gives him the numbers, and stops.
- **The pull-up paragraph is the part that helps him even if he never takes the
  module** — any of his users soldering a receiver to a Waveshare board hits it.

## Figures used, and where they come from

| Figure | Source |
|---|---|
| 10,832 B of flash, 280 B of static RAM | built both ways on the same commit e3b5f65: `matrix-waveshare-rgb` 2,270,397 B / 103,328 B against the same env with `build_unflags = -DIR_ENABLED` 2,259,565 B / 103,048 B |
| ~1 KB of internal heap with the receiver | `IRrecv(pin, 256, 15, true)` — two `uint16` buffers of 256 samples, read in IRremoteESP8266 2.9.0's constructor |
| The library's default 1024 would cost ~4 KB | same constructor, 2 × 1024 × 2 B |
| 0 library symbols in the image with the flag off | `xtensa-esp32s3-elf-nm` on `firmware.elf`, run by the auditor on its own build |
| A held NEC key repeats in a 108 ms slot; 38 kHz carrier | Vishay application note 80071 rev 2.3, "Data Formats for IR Remote Control", read in full |
| Receiver OUT is open collector with a 30 kΩ pull-up inside; Vs 2.0–5.5 V | Vishay datasheet 82459 rev 2.4, block diagram and parameter table, read in full |
| The board pulls IO45/IO46 down with 10 kΩ (R59, R60) | Waveshare schematic |
| 0.83 V idle against the 2.48 V the S3 needs; 2.74 V with an external 2.2 kΩ | arithmetic from those two, **calculated, not measured** — and the letter says so |
| IO45 selects VDD_SPI's voltage; safe here only because VDD_SPI_FORCE is blown | ESP32-S3 datasheet; the fuse read off this board 2026-09-14 |
| 164 host checks | `python3 tools/ir/check_ir.py` |
| Tested on the panel through the serial console | run 2026-09-16 21:33: the encoder's own counters moved — cw 0→4, ccw 0→2, click 0→1, long 0→1 |

## English (to post)

```text
Hi Rafał,

another update, no PR attached.

I noticed there is no physical control in your firmware at all - no encoder, no buttons. On my board I had added a rotary encoder, and this week I moved it to an infrared remote, so I thought it might interest you: for your users it wouldn't be a replacement for a knob, it would be the first way to change the page from the sofa without reaching for a phone.

The part I think is worth stealing, if anything is, is the shape rather than the code. The module doesn't add a second control scheme. It produces exactly what a rotary encoder produces - detents and a button level - and hands them to the encoder's state machine, so a click, a long press and browsing keep one implementation instead of two that drift apart over a year. In my firmware the whole join is two lines inside the sampling task.

Codes are not hard-coded. Any remote is learned on the device, from a card in the portal or from the serial console, and the codes live in their own NVS namespace, so they survive a reflash and a new remote is taught rather than compiled. Eight slots: turn left, turn right, press, and five reserved.

It is also testable with no hardware, which matters because I have no receiver soldered yet. The simulator injects a slot at exactly the level a decoded frame reaches, so typing "ir cw 3" on the serial port walks the pages for real. That is how I tested it: the encoder's own counters moved, not just a log line.

Cost on my board, measured both ways on the same commit: 10,832 bytes of flash and 280 bytes of static RAM, with the receiver itself behind a second flag that is off. With the receiver it adds the IRremoteESP8266 library and about 1KB of internal heap - I set the capture buffer to 256 samples instead of the library's 1024, which would have cost about 4KB, and you know how tight internal heap is on these boards. With the flag off the linker keeps nothing of the library: 0 symbols in the image.

One thing that is useful to you whether or not you ever touch any of this, because anyone soldering a receiver to a Waveshare board will hit it. There is no free GPIO: the expansion header is IO45 and IO46 and nothing else is brought out. Both are strapping pins, and the board pulls them down with 10k. A Vishay receiver's output is an open collector with a 30k pull-up inside the package, so those two divide the supply and the idle line sits at about 0.83V, where the S3 wants 2.48V to read a one - the receiver would look permanently busy. An external 2.2k to 3V3 fixes it on paper (2.74V idle, 1.6mA when it pulls down). That is arithmetic from the datasheet and the schematic, not a measurement - I will report the real numbers when I solder one. And IO45 selects VDD_SPI's voltage, so pulling it up is only safe on modules where that is fixed by an eFuse, which it is on the N32R16V.

It is in my fork behind -DIR_ENABLED, with -DIR_RX_ENABLED for the receiver. Optional modules stay in the fork, as you asked, so I am not proposing anything - but if a remote sounds useful for the Waveshare env, say so and I will cut it down to the smallest version that makes sense for you.

Next PR from me is still yours to set: by your order it is the weather task lifetime. And the one-line settings fix I mentioned last time is still there if you want it.

Nikolay
```

## Русский (для чтения, не публикуется)

```text
Привет, Рафал,

ещё одна новость, без PR.

Я заметил, что в твоей прошивке нет физического управления вообще - ни энкодера, ни кнопок. У себя я сначала поставил энкодер, а на этой неделе перевёл управление на ИК-пульт, и подумал, что это может тебя заинтересовать: для твоих пользователей это будет не замена ручки, а вообще первый способ переключить страницу с дивана, не беря телефон.

Что тут стоит перенять, если вообще стоит, - это не код, а устройство. Модуль не заводит второй способ управления. Он выдаёт ровно то же, что даёт энкодер - щелчки и уровень кнопки - и отдаёт их автомату энкодера, так что клик, долгое нажатие и листание остаются одной реализацией, а не двумя, которые за год разъедутся. У меня весь стык - две строки внутри задачи опроса.

Коды не зашиты. Любой пульт обучается на приборе - из карточки в портале или из сериальной консоли, - и коды лежат в своей области NVS, поэтому переживают перепрошивку: новый пульт обучаем, а не пересобираем прошивку. Восемь слотов: влево, вправо, нажатие и пять про запас.

И это проверяемо без железа, что важно, потому что приёмник у меня ещё не подпаян. Симулятор вбрасывает слот ровно на том уровне, куда приходит декодированный кадр, так что "ir cw 3" в сериальном порту по-настоящему листает страницы. Так я и проверял: сдвинулись собственные счётчики энкодера, а не строчка в логе.

Цена на моей плате, замерено сборкой в обе стороны на одном коммите: 10 832 байта флеша и 280 байт статической памяти, сам приёмник за вторым флагом, который выключен. С приёмником добавляется библиотека IRremoteESP8266 и около 1 КБ внутренней кучи - я поставил буфер захвата 256 отсчётов вместо 1024 по умолчанию, те стоили бы около 4 КБ, а ты знаешь, как на этих платах тесно с внутренней памятью. С выключенным флагом линкер не берёт из библиотеки ничего: ноль символов в образе.

Одна вещь, полезная тебе в любом случае, потому что на неё наткнётся каждый, кто припаяет приёмник к плате Waveshare. Свободных выводов нет: на разъём выведены только IO45 и IO46. Оба - strapping-пины, и плата тянет их к земле через 10 кОм. У приёмника Vishay выход с открытым коллектором и внутренней подтяжкой 30 кОм, эти два резистора делят питание, и в покое на линии получается около 0,83 В при пороге 2,48 В - приёмник будет выглядеть вечно занятым. Внешние 2,2 кОм на 3V3 это чинят по расчёту (2,74 В в покое, 1,6 мА при притяжке). Это арифметика из даташита и схемы, а не измерение, - настоящие числа сообщу, когда припаяю. И IO45 выбирает напряжение VDD_SPI, так что подтягивать его безопасно только там, где оно зафиксировано фьюзом, как на N32R16V.

Всё в моём форке за -DIR_ENABLED, приёмник за -DIR_RX_ENABLED. Опциональные модули остаются в форке, как ты просил, так что я ничего не предлагаю, - но если пульт покажется полезным для платы Waveshare, скажи, и я вырежу самый маленький вариант, который тебе подойдёт.

Следующий PR от меня по-прежнему за тобой: по твоему порядку это время жизни задачи погоды. И тот однострочный фикс настроек, о котором я писал, тоже в силе, если он нужен.

Николай
```
