# GitHub Release v2.5.8 (NickoScope/AnimatedPixelClock): draft

Status: PUBLISHED 2026-09-23 21:49 on the owner's "отправляй" (text polished to his voice first): https://github.com/NickoScope/AnimatedPixelClock/releases/tag/v2.5.8, tag at 7951336; the flasher serves v2.5.8. The release OTA image (SHA-256 e39edce6549a62b1...) is on the owner's panel, self-test with --effects PASS.

Title: AnimatedPixelClock v2.5.8

## Body (English, as it would be posted)

This release is for the Waveshare ESP32-S3-RGB-Matrix board driving a 128x64 HUB75 panel, the only board I have tested it on. Most of it came out of the first evening with an infrared receiver soldered to my panel, from the small things I missed while actually using it.

The panel now shows its state in two corners on every screen. In the top left there is an A when the carousel changes screens by itself, a dimmer A while it waits after you changed a page by hand, and an M when it is off. While you are inside a page, for example picking a station on the rail board, an arrow takes its place. In the top right there is a Wi-Fi icon coloured by signal strength: green at -67 dBm or better, amber down to -80, red below that, and a red cross when there is no connection. While the remote is being received the icon turns into a blinking red dot, so you can see that the panel hears you. Each mark sits on a small black patch, so it stays readable over any picture.

The remote now moves one step per press for left, right and brightness, however long you hold the button. Before, every repeat a held key sends counted as a new press, and one ordinary press could jump from the clock to page 22. Brightness set with the remote is also kept after a power cut now. It is saved a few seconds after the last press.

The receiver goes on GPIO0, the BOOT line, which the board already pulls up, so no extra resistor is needed. The wiring and the parts are in src/ir/README.md.

Install: for a new board, use the web flasher at https://nickoscope.github.io/AnimatedPixelClock/ or write firmware-v2.5.8-waveshare.bin at 0x0. For a board that is already running, upload OTA_ONLY_firmware-v2.5.8-waveshare.bin on the portal's firmware update page, or let the tools in tools/agent do it. Do not upload the full image as an update. The Windows PC stats companion is pc_stats_monitor_v4.exe. SHA256SUMS.txt has the checksums.

## Русский перевод (для владельца, не публикуется)

Этот релиз для платы Waveshare ESP32-S3-RGB-Matrix с панелью HUB75 128x64, единственной, на которой я его проверял. Он из первого вечера с реально припаянным ИК-приёмником и из того, чего мне не хватило, пока я им пользовался.

Теперь панель показывает своё состояние в двух углах на любом экране. Слева вверху A, когда карусель сама меняет экраны (тусклее, пока она ждёт после ручного переключения), и M, когда она выключена, или стрелка, пока ты внутри страницы и стрелки работают в ней, например выбирают вокзал на табло поездов. Справа вверху значок Wi-Fi, цвет по уровню сигнала: зелёный от −67 dBm и лучше, янтарный до −80, красный ниже, и красный крестик без связи. Пока принимается сигнал пульта, значок превращается в мигающую красную точку, так что видно, что панель тебя слышит. Каждый знак стоит на маленьком чёрном квадрате и читается поверх любой картинки.

Пульт. Влево, вправо и яркость теперь меняются на один шаг за нажатие, сколько ни держи кнопку. Раньше каждый повтор, который пульт шлёт при удержании, считался новым нажатием, и одно обычное нажатие могло перебросить с часов на страницу 22. Яркость, выставленная пультом, теперь сохраняется после отключения питания: запись через несколько секунд после последнего нажатия.

Приёмник подключается к GPIO0, линии BOOT, которую плата уже подтягивает вверх, так что дополнительный резистор не нужен. Схема и детали в заметках по ИК в репозитории.

Установка: новую плату прошить через веб-флешер https://nickoscope.github.io/AnimatedPixelClock/ или записать firmware-v2.5.8-waveshare.bin по адресу 0x0. Уже работающую обновить загрузкой OTA_ONLY_firmware-v2.5.8-waveshare.bin на странице обновления прошивки в портале или инструментами из tools/agent. Полный образ как обновление не загружать. Компаньон статистики ПК для Windows: pc_stats_monitor_v4.exe. Контрольные суммы в SHA256SUMS.txt.
