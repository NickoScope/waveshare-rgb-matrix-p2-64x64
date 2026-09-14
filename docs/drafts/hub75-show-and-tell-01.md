# Draft: use case post for the HUB75 library, "Show and tell"

**Status: DRAFT, not posted.** Posted only when the owner says "отправляй", from
NickoScope via `gh`. Written 2026-09-15 in the owner's own voice, plain text.

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
| Portal `/`: 1.8 s → 0.14 s; ~80 KB/s | panel 2026-09-14/15, [03](../03-firmware.md) |

## English (to post)

Title:

```text
Waveshare ESP32-S3-RGB-Matrix + 2x 64x64 FM6126A, clock firmware with WiFi/TLS/OTA next to DMA: notes
```

Body:

```text
Sharing a use case and some notes, maybe useful for others with this board.

Hardware: Waveshare ESP32-S3-RGB-Matrix driver board (ESP32-S3-WROOM-2 N32R16V, octal flash + octal PSRAM), two Waveshare 64x64 P2.5 HUB75E panels chained as 128x64, FM6126A. Library 3.0.14, arduino-esp32 2.0.17.
Firmware: my fork of Keralots AnimatedPixelClock with extra pages (world clock, flight and rail boards, AIS radar, Lua effects, media page). WiFi, TLS, MQTT, web portal and OTA all run next to the DMA refresh.

What I found:

1. Pins are this library default ESP32-S3 map, only E is on GPIO9. With FM6126A I needed clkphase = false, otherwise the rightmost column was dropped (related to #785).

2. The module needs board_build.arduino.memory_type = opi_opi. With qio_opi the image flashes but never boots.

3. I tried SPIRAM_DMA_BUFFER on this board. It freed ~130KB of internal heap, but every page got stripes and flicker, and TLS certificate verification started failing (-9984) while the DMA was reading from PSRAM. Didnt find the root cause, reverted. With the buffers in internal SRAM (double buffer, 8 bit, 128x64) the display takes ~148KB of internal heap and refresh is reported 84Hz. Internal heap is the tight resource on this board, not PSRAM.

4. WiFi works fine next to the DMA refresh on this board, web UI, NTP, TLS fetches and OTA all ok.

5. If you render from loop() and serve pages with the Arduino WebServer, a big page transfer blocks loop() for its whole length (around 80KB/s from the board) and the picture freezes. Gzipping the portal took the main page from 1.8s to 0.14s.

Env and code: https://github.com/NickoScope/AnimatedPixelClock branch board/waveshare-esp32-s3-rgb-matrix

Thanks for the library, it carries all of this.
```

## Русский (для чтения, не публикуется)

```text
Заголовок: Waveshare ESP32-S3-RGB-Matrix + 2 панели 64x64 FM6126A, прошивка часов с WiFi/TLS/OTA рядом с DMA: заметки

Делюсь применением и несколькими заметками, может пригодится другим с этой платой.

Железо: драйверная плата Waveshare ESP32-S3-RGB-Matrix (ESP32-S3-WROOM-2 N32R16V, octal flash + octal PSRAM), две панели Waveshare 64x64 P2.5 HUB75E цепочкой как 128x64, FM6126A. Библиотека 3.0.14, arduino-esp32 2.0.17.
Прошивка: мой форк AnimatedPixelClock от Keralots с дополнительными страницами (мировое время, табло аэропорта и поездов, AIS радар, Lua эффекты, страница медиаплеера). WiFi, TLS, MQTT, веб портал и OTA работают рядом с обновлением DMA.

Что я нашёл:

1. Пины это стандартная раскладка этой библиотеки для ESP32-S3, только E на GPIO9. С FM6126A понадобился clkphase = false, иначе пропадал крайний правый столбец (связано с #785).

2. Модулю нужен board_build.arduino.memory_type = opi_opi. С qio_opi прошивка заливается, но не стартует.

3. Пробовал SPIRAM_DMA_BUFFER на этой плате. Освободилось ~130КБ внутренней памяти, но на всех страницах пошли полосы и мерцание, и проверка TLS сертификатов начала падать (-9984), пока DMA читал из PSRAM. Причину не нашёл, откатил. С буферами во внутренней SRAM (двойной буфер, 8 бит, 128x64) дисплей занимает ~148КБ внутренней памяти, частота обновления по данным библиотеки 84Гц. Узкое место на этой плате внутренняя память, а не PSRAM.

4. WiFi нормально работает рядом с обновлением DMA на этой плате, веб интерфейс, NTP, TLS запросы и OTA всё в порядке.

5. Если рисовать из loop() и отдавать страницы через Arduino WebServer, передача большой страницы блокирует loop() на всё время (около 80КБ/с с платы) и картинка замирает. Сжатие портала gzip сократило главную страницу с 1,8с до 0,14с.

Окружение и код: https://github.com/NickoScope/AnimatedPixelClock ветка board/waveshare-esp32-s3-rgb-matrix

Спасибо за библиотеку, всё это держится на ней.
```
