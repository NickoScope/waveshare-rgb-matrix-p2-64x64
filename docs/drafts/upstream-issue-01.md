# Draft: first issue to Keralots/AnimatedPixelClock

**Status: DRAFT, not sent.** Posted only when the owner says so. Written
2026-09-14, rewritten 2026-09-15 in the owner's own voice at his request:
plain text, no formatting. Plan behind it:
[09-upstream-contributions.md](../09-upstream-contributions.md).

Figures used in the text, and where they come from:

| Figure | Source |
|---|---|
| matrix-s3 at 82% flash | measured at `74f964b`, [09](../09-upstream-contributions.md) |
| Internal heap ~30 → ~38 KB | panel, 2026-09-14, fork commit `6e91d54` |
| ~80 KB/s page transfers | panel, 2026-09-14, [03](../03-firmware.md) |
| Upstream settings page ~77 KB | length of `PAGE_HTML` in `upstream/main`. The one-second freeze is size times rate, not measured on their build, and the text says so |
| OTA rollback test | panel, 2026-09-14, fork commit `8ec3045` |

Copy the text from inside the blocks; it is meant to be posted as is.

## English (to post)

Title:

```text
Waveshare ESP32-S3-RGB-Matrix support + some fixes from my fork, how do you want them?
```

Body:

```text
Hi, first thanks for AnimatedPixelClock, really nice project to build on.

I run it on Waveshare ESP32-S3-RGB-Matrix board (ESP32-S3-WROOM-2 N32R16V, octal flash + octal PSRAM) with two 64x64 panels chained, FM6126A. My fork grew quite a lot since then, so before I open any PRs I want to ask how you prefer to get them.
Fork: https://github.com/NickoScope/AnimatedPixelClock branch board/waveshare-esp32-s3-rgb-matrix

I know the matrix-s3 4MB build is tight, it was 82% flash when I measured on 74f964b. So everything that adds noticable flash would go behind a build flag and be off by default there, and I will put the matrix-s3 size in every PR.

Small general things, one PR each:

1. Waveshare ESP32-S3-RGB-Matrix board support. One env in platformio.ini and the pin set, its basically the default ESP32-S3 HUB75 map from the library with E on GPIO9. The module needs board_build.arduino.memory_type = opi_opi, with qio_opi the image flashes ok but every boot dies in do_core_init. Tested on real hardware.

2. Weather task only for the fetch. Now the weather task keeps its 8KB stack in internal SRAM all 10 minutes between fetches. I start a task per fetch and fetch only when the weather clock is really on screen, free internal heap one minute after boot went from ~30KB to ~38KB on my build.

3. TLS buffers in PSRAM on boards that have PSRAM. The precompiled libs are built with CONFIG_MBEDTLS_INTERNAL_MEM_ALLOC, one call to mbedtls_platform_set_calloc_free() at startup moves TLS allocations to PSRAM. Without PSRAM it does nothing.

4. OTA rollback that really rolls back + crash report. Rollback is enabled in the SDK but arduino-esp32 2.0.17 marks every image valid in initArduino(), so a new image that boots and then crashes never rolls back. I override verifyRollbackLater() and confirm the image after one minute of running with WiFi up. Tested via /update, an image that aborts at 20s was replaced with the previous one on next boot. Also at boot the core dump summary (task, cause, PC, backtrace, image SHA) goes to /api/info and the dump is erased.

5. Loop diagnostics in /api/info: longest loop() pass in the last 10s and which part of loop it was spent in. Thats how I found point 6.

6. Lighter portal. Pages are sent from inside loop() and the board sends around 80KB/s, so the display freezes while a page is transfering. Your settings page is ~77KB, so it should be about 1s freeze on every portal open. Didnt measure it on your build, its just size x speed. Gzip for the static files helps. To gzip the settings page too, the values need to come as JSON instead of template tokens. Thats a bigger change in web.cpp/web_pages.h, so only if you like the idea.

Optional modules, if you want them upstream at all: rotary encoder control (pages, clock styles, page carousel), MQTT bus with Home Assistant cards (pages and notifications pushed from HA), world clock page (day/night map, timezones, home city), Lua effects (sandboxed Lua 5.4 runtime with a host simulator and scenes like snooker, football, tetris and snake clocks, this one is the big one), clip gallery played from TF card. All of them are compile time options now. Totally understand if you prefer to keep them in the fork.

Also in progress on this board, not ready yet: IR remote control (receiver on a free GPIO), audio reactive effects from the onboard mics through the ES8311 codec, the QMI8658 accelerometer (orientation, tap/shake), a presence sensor to wake or dim the panel when nobody is in the room, and sound through the codec + onboard speaker amp (chimes, effects sounds). Same rule for those, behind flags.

Also data boards and radars I built. They need users own API keys (kept in NVS, never compiled in), so optional modules or they stay in the fork, your call:
flight board for any airport in the world, arrivals and departures in the airport local time, tracked flights pinned as top row with status, data from FlightAware AeroAPI (paid per call, so hard caps: 15 min between list calls, 30 calls per day, 900 per month) or from Home Assistant over MQTT;
UK rail board for any National Rail station, looks like the real station screen, departures and arrivals, trains due in the next N minutes in green, data from Realtime Trains API;
AIS yacht radar, live vessels in a bay from aisstream.io, sweeping beam flashes the boat and its row in the list, list sorted by length, centre and bounding box are constants and the coastline basemap is generated by a script so other area is easy;
room radar, targets of a 24GHz mmWave presence sensor drawn like a radar screen, for now a Lua scene with simulated targets, real feed comes together with the presence sensor.
All of them fetch only while their page is on screen, no background traffic.
The Home Assistant media remote is too specific to my HA setup, that one stays in the fork.

Questions:
1. Are PRs welcome and what from the list is interesting for you?
2. One PR per change branched from main is ok? Any rules I should follow, formatting, version bump, release notes?
3. Optional modules behind build flags in your repo, or better they stay in the fork?

Thanks!
Nikolay
```

## Русский (для чтения, не отправляется)

```text
Заголовок: Поддержка Waveshare ESP32-S3-RGB-Matrix + несколько исправлений из моего форка, как вам удобнее их получить?

Привет, во-первых спасибо за AnimatedPixelClock, очень приятный проект чтобы на нём строить.

Я запускаю его на плате Waveshare ESP32-S3-RGB-Matrix (ESP32-S3-WROOM-2 N32R16V, octal flash + octal PSRAM) с двумя панелями 64x64 цепочкой, FM6126A. Мой форк с тех пор сильно разросся, поэтому прежде чем открывать PR хочу спросить, как вам удобнее их получать.
Форк: https://github.com/NickoScope/AnimatedPixelClock ветка board/waveshare-esp32-s3-rgb-matrix

Я знаю, что сборка matrix-s3 на 4МБ почти забита, было 82% flash когда я мерил на 74f964b. Поэтому всё, что заметно добавляет к прошивке, пойдёт за флагом сборки и по умолчанию будет там выключено, и в каждом PR я укажу размер для matrix-s3.

Небольшие общие вещи, по PR на каждую:

1. Поддержка платы Waveshare ESP32-S3-RGB-Matrix. Одно окружение в platformio.ini и набор пинов, по сути стандартная раскладка HUB75 для ESP32-S3 из библиотеки, только E на GPIO9. Модулю нужен board_build.arduino.memory_type = opi_opi, с qio_opi прошивка заливается нормально, но каждый старт падает в do_core_init. Проверено на реальном железе.

2. Задача погоды только на время запроса. Сейчас задача погоды держит свой стек 8КБ во внутренней SRAM все 10 минут между запросами. Я запускаю задачу на каждый запрос и запрашиваю только когда погодные часы реально на экране, свободная внутренняя память через минуту после старта выросла у меня с ~30КБ до ~38КБ.

3. Буферы TLS в PSRAM на платах, где PSRAM есть. Готовые библиотеки собраны с CONFIG_MBEDTLS_INTERNAL_MEM_ALLOC, один вызов mbedtls_platform_set_calloc_free() при старте переносит память TLS в PSRAM. Без PSRAM ничего не делает.

4. Откат OTA, который реально откатывает, + отчёт о падении. Откат в SDK включён, но arduino-esp32 2.0.17 помечает каждую прошивку рабочей в initArduino(), поэтому новая прошивка, которая загрузилась и потом падает, никогда не откатывается. Я переопределяю verifyRollbackLater() и подтверждаю прошивку после минуты работы с поднятым WiFi. Проверено через /update, прошивка, которая падает на 20с, при следующей загрузке заменилась предыдущей. Ещё при старте сводка дампа падения (задача, причина, PC, цепочка вызовов, SHA прошивки) идёт в /api/info, а дамп стирается.

5. Диагностика цикла в /api/info: самый долгий проход loop() за последние 10с и на какую часть loop он пришёлся. Так я и нашёл пункт 6.

6. Портал полегче. Страницы отдаются изнутри loop(), а плата передаёт около 80КБ/с, поэтому экран замирает, пока страница передаётся. Ваша страница настроек ~77КБ, так что это примерно 1с заморозки при каждом открытии портала. На вашей сборке не мерил, это просто размер x скорость. Gzip для статических файлов помогает. Чтобы сжать и страницу настроек, значения должны приходить JSON вместо подстановки в шаблон. Это изменение побольше в web.cpp/web_pages.h, так что только если идея нравится.

Необязательные модули, если они вообще нужны в основном репо: управление энкодером (страницы, стили часов, карусель страниц), MQTT шина с карточками Home Assistant (страницы и уведомления из HA), страница мирового времени (карта дня и ночи, часовые пояса, домашний город), Lua эффекты (изолированная среда Lua 5.4 с симулятором на компьютере и сценами типа снукер, футбол, часы тетрис и змейка, это самый большой кусок), галерея клипов с TF карты. Сейчас всё это опции при сборке. Полностью пойму, если предпочтёте оставить их в форке.

Ещё в работе на этой плате, пока не готово: управление с IR пульта (приёмник на свободном GPIO), аудиореактивные эффекты от встроенных микрофонов через кодек ES8311, акселерометр QMI8658 (ориентация, тап/встряхивание), датчик присутствия, чтобы будить или гасить панель, когда в комнате никого, и звук через кодек + встроенный усилитель на динамик (сигналы, звуки эффектов). Для них то же правило, за флагами.

Ещё я сделал табло с данными и радары. Им нужны собственные ключи API пользователя (хранятся в NVS, в прошивку не вшиваются), так что это необязательные модули или остаются в форке, как решите:
табло аэропорта для любого аэропорта мира, прилёты и вылеты по местному времени аэропорта, отслеживаемые рейсы закреплены верхней строкой со статусом, данные из FlightAware AeroAPI (платно за запрос, поэтому жёсткие лимиты: 15 мин между запросами списка, 30 запросов в день, 900 в месяц) или из Home Assistant по MQTT;
британское ЖД табло для любой станции National Rail, выглядит как настоящее табло на вокзале, отправления и прибытия, поезда в ближайшие N минут зелёным, данные из Realtime Trains API;
AIS радар яхт, живые суда в бухте с aisstream.io, сканирующий луч подсвечивает лодку и её строку в списке, список по длине, центр и границы заданы константами, а карта берега генерируется скриптом, так что другой район сделать легко;
радар комнаты, цели 24ГГц mmWave датчика присутствия на экране как у радара, пока Lua сцена с имитацией целей, реальные данные придут вместе с датчиком присутствия.
Все они запрашивают данные только пока их страница на экране, без фонового трафика.
Пульт медиаплеера Home Assistant слишком завязан на мой HA, он остаётся в форке.

Вопросы:
1. Принимаете PR и что из списка вам интересно?
2. Один PR на одно изменение, ветка от main, ок? Есть правила, которых держаться, форматирование, номер версии, заметки к релизу?
3. Необязательные модули за флагами сборки у вас в репо, или лучше пусть остаются в форке?

Спасибо!
Николай
```
