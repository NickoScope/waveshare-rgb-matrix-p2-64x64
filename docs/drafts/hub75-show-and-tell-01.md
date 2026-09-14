# Draft: use case post for the HUB75 library, "Show and tell"

**Status: POSTED 2026-09-15** on the owner's "отправляй", from NickoScope:
https://github.com/mrcodetastic/ESP32-HUB75-MatrixPanel-DMA/discussions/962.

Written 2026-09-15 in the owner's voice: correct, natural English, plain paragraphs (the owner, 00:52: "пиши правильно, по-человечески").

## Where, and why there

**Posting here:** [mrcodetastic/ESP32-HUB75-MatrixPanel-DMA](https://github.com/mrcodetastic/ESP32-HUB75-MatrixPanel-DMA),
Discussions → **Show and tell**.
- That is where people post boards, panels and builds made with the library,
  for example "192x192 Pushing the Limits with ESP32-S3" and "MatrixCOS".
- 1.6k stars.
- No existing discussion covers the Waveshare ESP32-S3-RGB-Matrix board.
- The FM6126A `clkphase` finding below also answers the open question in
  Discussion #785, "Shouldn't selecting a driver like FM6124 also set clkphase?".

**Not posting to Waveshare's own repo** ([waveshareteam/ESP32-S3-RGB-Matrix](https://github.com/waveshareteam/ESP32-S3-RGB-Matrix)).
- It has no Discussions, and its README takes contributions only as pull
  requests to their examples.
- Issues there are for support, and even those are redirected to Gitee.
- A showcase posted as an issue would be out of place.

## Figures used, and where they come from

| Figure | Source |
|---|---|
| Library 3.0.14, arduino-esp32 2.0.17 | fork `platformio.ini`, `.pio/libdeps/.../library.json` |
| E on GPIO9, the rest this library's S3 default map | `src/display/matrix_display.h`, checked against Waveshare's BSP |
| `clkphase=false` fixes the dropped rightmost column on FM6126A | `matrix_display.h`, "verified Phase 1" on the real panels |
| `opi_opi` needed; `qio_opi` never boots | fork commit `e0757f8` |
| PSRAM DMA: +130 KB internal free, stripes, TLS `-9984` | panel 2026-09-14, [03](../03-firmware.md) |
| ~148 KB internal SRAM for the display, 84 Hz | `MEM_TRACE` on the panel, [03](../03-firmware.md) |
| Short-lived network task stacks help | the weather task change, ~30 → ~38 KB free after boot, fork `6e91d54` |
| No existing post about this board | discussion search for "waveshare" in the repo, 2026-09-15 |
| Portal `/`: 1.8 s → 0.14 s; ~80 KB/s | panel 2026-09-14/15, [03](../03-firmware.md) |

## English (to post)

Title:

```text
Notes from a Waveshare ESP32-S3-RGB-Matrix build: two 64x64 FM6126A panels, with Wi-Fi, TLS and OTA alongside DMA
```

Body:

```text
Hi all,

I wanted to share a build on the Waveshare ESP32-S3-RGB-Matrix board, since I couldn't find anything about it here, along with a few things I learned along the way.

The setup is the Waveshare driver board (ESP32-S3-WROOM-2 N32R16V, with octal flash and octal PSRAM) and two Waveshare 64x64 P2.5 HUB75E panels with FM6126A drivers, chained into a 128x64 display. It runs my fork of Keralots' AnimatedPixelClock, which I've extended with a world clock, flight and rail departure boards, an AIS ship radar, Lua effects and a media player page. Wi-Fi, TLS, MQTT, the web portal and OTA updates all run alongside the DMA refresh. The library is 3.0.14, on arduino-esp32 2.0.17.

Getting the board going was easy. It uses this library's default ESP32-S3 pin map, except that E is on GPIO9. With the FM6126A panels I had to set clkphase to false, otherwise the rightmost column was missing, which may be relevant to the question in #785. The module also needs board_build.arduino.memory_type = opi_opi in PlatformIO; with qio_opi the image flashes but never boots.

Memory was the interesting part. I tried SPIRAM_DMA_BUFFER, and it freed about 130 KB of internal heap, but every page showed stripes and flicker, and TLS certificate verification started failing (-9984) while the DMA was reading from PSRAM. I didn't track down the cause and went back to internal SRAM. With the buffers there (double-buffered, 8-bit, 128x64) the display uses about 148 KB of internal heap, and the library reports 84 Hz. On this board internal RAM is the scarce resource, not PSRAM, so it pays to keep network task stacks short-lived.

Wi-Fi has been solid next to the display: the web UI, NTP, TLS fetches and OTA all work without problems.

One thing that caught me out: if you render from loop() and serve pages with the Arduino WebServer, a large page transfer blocks loop() for its whole duration (the board sends at roughly 80 KB/s), and the picture freezes. Serving the portal gzipped brought the main page down from 1.8 s to 0.14 s.

The environment and code are here: https://github.com/NickoScope/AnimatedPixelClock (branch board/waveshare-esp32-s3-rgb-matrix).

Thanks for the library, it does all the heavy lifting here.
```

## Русский (для чтения, не публикуется)

```text
Заголовок: Заметки о сборке на Waveshare ESP32-S3-RGB-Matrix: две панели 64x64 с FM6126A, Wi-Fi, TLS и OTA рядом с DMA

Всем привет,

хочу поделиться сборкой на плате Waveshare ESP32-S3-RGB-Matrix, потому что здесь я о ней ничего не нашёл, и заодно несколькими вещами, которые выяснил по ходу.

Сборка такая: драйверная плата Waveshare (ESP32-S3-WROOM-2 N32R16V, с octal flash и octal PSRAM) и две панели Waveshare 64x64 P2.5 HUB75E с драйверами FM6126A, соединённые в дисплей 128x64. На ней работает мой форк AnimatedPixelClock от Keralots, который я дополнил мировым временем, табло вылетов и поездов, AIS-радаром судов, Lua-эффектами и страницей медиаплеера. Wi-Fi, TLS, MQTT, веб-портал и обновления по воздуху работают параллельно с обновлением экрана через DMA. Библиотека версии 3.0.14, на arduino-esp32 2.0.17.

Запустить плату оказалось просто. Она использует стандартную для этой библиотеки раскладку пинов ESP32-S3, только E на GPIO9. С панелями на FM6126A пришлось выставить clkphase в false, иначе пропадал крайний правый столбец; возможно, это пригодится для вопроса в #785. Модулю также нужен board_build.arduino.memory_type = opi_opi в PlatformIO; с qio_opi прошивка заливается, но не запускается.

Самым интересным оказалась память. Я попробовал SPIRAM_DMA_BUFFER, и это освободило около 130 КБ внутренней памяти, но на всех страницах появились полосы и мерцание, а проверка TLS-сертификатов стала падать (-9984), пока DMA читал из PSRAM. Причину я не нашёл и вернулся к внутренней SRAM. С буферами там (двойной буфер, 8 бит, 128x64) дисплей занимает около 148 КБ внутренней памяти, а библиотека показывает 84 Гц. На этой плате дефицит именно во внутренней памяти, а не в PSRAM, поэтому стоит держать стеки сетевых задач только на время работы.

Wi-Fi рядом с дисплеем работает стабильно: веб-интерфейс, NTP, запросы по TLS и OTA без проблем.

Одна вещь застала меня врасплох: если рисовать из loop() и отдавать страницы через Arduino WebServer, передача большой страницы блокирует loop() на всё время (плата отдаёт примерно 80 КБ/с), и картинка замирает. Отдача портала в gzip сократила загрузку главной страницы с 1,8 с до 0,14 с.

Окружение и код здесь: https://github.com/NickoScope/AnimatedPixelClock (ветка board/waveshare-esp32-s3-rgb-matrix).

Спасибо за библиотеку, вся тяжёлая работа здесь на ней.
```
