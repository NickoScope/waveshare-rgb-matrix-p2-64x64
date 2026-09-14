# Draft: first issue to Keralots/AnimatedPixelClock

**Status: DRAFT, not sent.** Posted only when the owner says so. Written
2026-09-14. Plan behind it: [09-upstream-contributions.md](../09-upstream-contributions.md).

Figures used below, and where they come from:

| Figure | Source |
|---|---|
| `matrix-s3` at 82% flash | measured at `74f964b`, [09](../09-upstream-contributions.md) |
| Internal heap ~30 → ~38 KB | panel, 2026-09-14, fork commit `6e91d54` |
| ~80 KB/s page transfers | panel, 2026-09-14, [03](../03-firmware.md) |
| Upstream settings page ~77 KB | length of `PAGE_HTML` in `upstream/main`. The one-second freeze is an estimate from size and rate, not measured on their build |
| OTA rollback test | panel, 2026-09-14, fork commit `8ec3045` |

---

## English (to post)

**Title:** Waveshare ESP32-S3-RGB-Matrix support and a set of fixes from a fork: how would you like them?

Hi! Thanks for AnimatedPixelClock. It has been a joy to build on.

I run it on a **Waveshare ESP32-S3-RGB-Matrix** (ESP32-S3-WROOM-2 N32R16V, octal
flash and octal PSRAM) with two chained 64×64 panels (FM6126A). The fork has
grown quite a bit since, so before opening any pull requests I'd like to ask how
you'd prefer to receive them.

Fork: https://github.com/NickoScope/AnimatedPixelClock, branch
`board/waveshare-esp32-s3-rgb-matrix`.

I know the 4 MB `matrix-s3` build is tight: 82% of flash when I measured `74f964b`.
Anything below that adds noticeable flash would sit behind a build flag, off by
default there, and each PR would state its `matrix-s3` size.

**Small, general changes, one PR each:**

1. **Waveshare ESP32-S3-RGB-Matrix board support.** A `platformio.ini` environment
   and its pin set, which is the HUB75 library's default ESP32-S3 map with E on
   GPIO9. The module needs `board_build.arduino.memory_type = opi_opi`: with
   `qio_opi` the image flashed, but every boot failed in `do_core_init`. Tested on
   the hardware.
2. **Weather: one task per fetch.** The weather task keeps an 8 KB stack in
   internal SRAM for the ten minutes between fetches. With a task started for each
   fetch, and a fetch only while the weather clock is on screen, free internal
   heap a minute after boot went from ~30 KB to ~38 KB on my build.
3. **TLS buffers in PSRAM on boards that have it.** The precompiled libraries use
   `CONFIG_MBEDTLS_INTERNAL_MEM_ALLOC`. One call to
   `mbedtls_platform_set_calloc_free()` at startup moves TLS allocations to PSRAM.
   Without PSRAM it does nothing.
4. **OTA rollback that actually rolls back, plus a crash report.** Rollback is
   enabled in the SDK, but arduino-esp32 2.0.17 marks every image valid in
   `initArduino()`. So a new image that boots and then crashes is never rolled
   back. Overriding `verifyRollbackLater()` and confirming the image after a minute
   of running with Wi-Fi up fixes that. I tested it over `/update`: an image that
   aborts at 20 s was replaced by the previous one on the next boot. At boot, the
   core dump summary (task, cause, PC, backtrace, image SHA) is also read into
   `/api/info`, and the dump is erased.
5. **Loop diagnostics in `/api/info`.** The longest `loop()` pass in the last 10 s,
   and which part of `loop()` it was spent in. This is how I found the issue in 6.
6. **A lighter portal.** Pages are sent from inside `loop()`, and the board sends
   at about 80 KB/s, so the display freezes while a page transfers. By size, your
   ~77 KB settings page should freeze it for about a second each time the portal
   opens (estimated, not measured on your build).
   - **Assets:** gzipping the static files helps.
   - **Settings page:** serving it compressed as well means loading the setting
     values as JSON instead of template tokens. That is a bigger change to
     `web.cpp`/`web_pages.h`, so I'd only do it if you like the idea.

**Optional modules, if you want them upstream at all:**

- rotary encoder control: page and clock style browsing, and a page carousel;
- an MQTT bus with Home Assistant "cards" (pages and notifications pushed from HA);
- a world clock page: day/night map, time zones, home city;
- Lua effects: a sandboxed Lua 5.4 runtime with a host simulator and scenes
  (snooker, football, Tetris and snake clocks). This is the big one;
- a clip gallery played from a TF card.

They are compile-time options today. I'd understand if you'd rather they stayed
in the fork.

**Staying in the fork**, as they are personal or need paid APIs: a flight board
(FlightAware AeroAPI), a UK rail board (Realtime Trains), an AIS yacht radar for
one bay, and a Home Assistant media remote.

**Questions:**

1. Are PRs welcome, and which of the above interest you?
2. One PR per change, branched from `main`: does that suit you? Any conventions
   I should follow (formatting, version bumps, release notes)?
3. The optional modules: behind build flags in this repo, or better left in the
   fork?

Most of this code was written with AI assistance (Claude) and checked on the
hardware. I'm happy to walk through any of it. Thanks!

---

## Русский (для чтения, не отправляется)

**Заголовок:** Поддержка Waveshare ESP32-S3-RGB-Matrix и набор исправлений из форка: в каком виде вам удобнее их получить?

Привет! Спасибо за AnimatedPixelClock, на нём было очень приятно строить.

Я запускаю его на **Waveshare ESP32-S3-RGB-Matrix** (ESP32-S3-WROOM-2 N32R16V,
octal flash и octal PSRAM) с двумя соединёнными панелями 64×64 (FM6126A). С тех
пор форк заметно разросся, поэтому до открытия PR хочу спросить, в каком виде
вам удобнее их получать.

Форк: https://github.com/NickoScope/AnimatedPixelClock, ветка
`board/waveshare-esp32-s3-rgb-matrix`.

Я знаю, что сборка `matrix-s3` на 4 МБ почти заполнена: 82% flash, когда я мерил
`74f964b`. Всё из списка ниже, что заметно добавляет к прошивке, будет за флагом
сборки и по умолчанию выключено на ней, а в каждом PR будет указан размер для
`matrix-s3`.

**Небольшие общие изменения, по PR на каждое:**

1. **Поддержка платы Waveshare ESP32-S3-RGB-Matrix.** Окружение в
   `platformio.ini` и набор пинов: стандартная для ESP32-S3 раскладка HUB75 из
   библиотеки, только E на GPIO9. Модулю нужен
   `board_build.arduino.memory_type = opi_opi`: с `qio_opi` прошивка
   заливалась, но каждый старт падал в `do_core_init`. Проверено на железе.
2. **Погода: отдельная задача на каждый запрос.** Задача погоды держит стек 8 КБ
   во внутренней памяти все десять минут между запросами. Теперь задача
   запускается на каждый запрос, а запрос идёт только когда погодные часы на
   экране. Свободная внутренняя память через минуту после старта выросла у меня
   с ~30 КБ до ~38 КБ.
3. **Буферы TLS в PSRAM на платах, где она есть.** Готовые библиотеки собраны с
   `CONFIG_MBEDTLS_INTERNAL_MEM_ALLOC`. Один вызов
   `mbedtls_platform_set_calloc_free()` при старте переносит память TLS в PSRAM.
   Без PSRAM он ничего не делает.
4. **Откат OTA, который действительно откатывает, и отчёт о падении.** Откат в
   SDK включён, но arduino-esp32 2.0.17 помечает каждую прошивку рабочей в
   `initArduino()`. Поэтому новая прошивка, которая загрузилась и потом упала,
   никогда не откатывается. Переопределение `verifyRollbackLater()` и
   подтверждение прошивки после минуты работы с поднятым Wi-Fi это исправляют.
   Проверено через `/update`: прошивка, падающая на 20-й секунде, при следующей
   загрузке сменилась прежней. Кроме того, при старте сводка дампа падения
   (задача, причина, PC, цепочка вызовов, SHA прошивки) попадает в `/api/info`,
   а сам дамп стирается.
5. **Диагностика цикла в `/api/info`.** Самый долгий проход `loop()` за 10 с и
   участок `loop()`, на который пришлось это время. Так я и нашёл проблему из
   пункта 6.
6. **Лёгкий портал.** Страницы отдаются изнутри `loop()`, а плата передаёт около
   80 КБ/с, так что пока страница передаётся, экран стоит. По размеру ваша
   страница настроек (~77 КБ) должна замораживать экран примерно на секунду при
   каждом открытии портала (оценка, на вашей сборке не мерил).
   - **Файлы:** сжатие gzip для статических файлов помогает.
   - **Страница настроек:** чтобы отдавать сжатой и её, значения настроек нужно
     загружать через JSON вместо подстановки в шаблон. Это более крупное
     изменение `web.cpp`/`web_pages.h`, так что сделаю его, только если вам
     нравится идея.

**Необязательные модули, если они вообще нужны в основном репозитории:**

- управление энкодером: листание страниц и стилей часов, карусель страниц;
- MQTT-шина с «карточками» из Home Assistant (страницы и уведомления из HA);
- страница мирового времени: карта дня и ночи, часовые пояса, домашний город;
- Lua-эффекты: изолированная среда Lua 5.4 с симулятором на компьютере и сценами
  (снукер, футбол, часы-тетрис и змейка). Это самый крупный пункт;
- галерея клипов с TF-карты.

Сейчас всё это включается при сборке. Пойму, если вы предпочтёте оставить их в
форке.

**Остаётся в форке**, потому что это личное или требует платных API: табло
аэропорта (FlightAware AeroAPI), табло британских поездов (Realtime Trains),
AIS-радар яхт в одной бухте и пульт медиаплеера для Home Assistant.

**Вопросы:**

1. Принимаете ли вы PR, и что из списка вам интересно?
2. Один PR на одно изменение, ветка от `main`: вам так удобно? Есть ли правила,
   которых стоит держаться (форматирование, номера версий, заметки к релизу)?
3. Необязательные модули: за флагами сборки у вас или лучше оставить в форке?

Большая часть кода написана с помощью ИИ (Claude) и проверена на железе. Готов
подробно пройтись по любой части. Спасибо!
