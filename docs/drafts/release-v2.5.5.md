# GitHub Release v2.5.5 (NickoScope/AnimatedPixelClock): draft

Status: PUBLISHED 2026-09-23 08:40 on the owner's "отправляй": https://github.com/NickoScope/AnimatedPixelClock/releases/tag/v2.5.5 (tag at 48d3665).

Title: AnimatedPixelClock v2.5.5

## Body (English, as it would be posted)

This release is for the Waveshare ESP32-S3-RGB-Matrix board driving a 128x64 HUB75 panel, the only board I have tested it on. Version 2.5.4 never left my own panel, so everything since 2.5.3 is here.

The panel can now show Russian. The small font has a Cyrillic alphabet next to the Latin one, and any Lua effect can write Cyrillic text as it is, in UTF-8. The letters that look like Latin ones use exactly the same pixels, and anything the font cannot draw shows as a solid block instead of silently turning into a space, so a missing character is visible.

There is an infrared remote. The receiver goes on the BOOT button line, next to the knob, which keeps working as before. The web portal has ten remote buttons: you teach each one by pressing it on the remote, and pick from a list what it does, from turning and pressing like the knob to screen on and off, brightness, going home to the clock, the carousel, the screensaver, a chosen page, play and pause, track and volume, and dismissing a notification. Codes and choices survive a firmware update.

Smaller changes: the router now lists the panel by the name you gave it instead of esp32s3 and three bytes of its MAC address, and setting the brightness over the API and reading it back no longer loses one percent every time.

For people driving the panel from scripts or AI agents, the tools in tools/agent gained a health self test that exercises the panel and keeps the logs, and a way to check for a new release and install it over the air. It asks three times before it sends anything and then reports whether the new version stayed or the panel went back to the previous one on its own.

Install: for a new board, use the web flasher at https://nickoscope.github.io/AnimatedPixelClock/ or write firmware-v2.5.5-waveshare.bin at 0x0. For a board that is already running, upload OTA_ONLY_firmware-v2.5.5-waveshare.bin on the portal's firmware update page, and do not upload the full image as an update. The Windows PC stats companion is pc_stats_monitor_v4.exe. SHA256SUMS.txt has the checksums.

## Русский перевод (для владельца, не публикуется)

Этот релиз для платы Waveshare ESP32-S3-RGB-Matrix с панелью HUB75 128x64, единственной, на которой я его проверял. Версия 2.5.4 не выходила за пределы моей панели, поэтому здесь всё, что появилось после 2.5.3.

Панель теперь умеет показывать русский. В маленьком шрифте рядом с латиницей есть кириллица, и любой Lua-эффект может писать кириллицу как есть, в UTF-8. Буквы, похожие на латинские, нарисованы теми же пикселями, а всё, чего в шрифте нет, показывается сплошным прямоугольником, а не молча превращается в пробел, так что пропущенный символ видно.

Появился ИК-пульт. Приёмник ставится на линию кнопки BOOT, рядом с ручкой, которая работает как прежде. В веб-портале десять кнопок пульта: каждую обучаешь нажатием на пульте и выбираешь из списка, что она делает, от поворота и нажатия, как у ручки, до включения и выключения экрана, яркости, возврата к часам, карусели, заставки, выбранной страницы, паузы и воспроизведения, трека и громкости и закрытия уведомления. Коды и выбор сохраняются при обновлении прошивки.

Изменения поменьше: роутер теперь показывает панель под именем, которое ей дали, а не esp32s3 и три байта MAC-адреса, а яркость, установленная через API и прочитанная обратно, больше не теряет процент каждый раз.

Для тех, кто управляет панелью из скриптов или ИИ-агентов, в tools/agent появились самотест здоровья, который прогоняет панель и сохраняет логи, и способ проверить новый релиз и установить его по воздуху. Он трижды спрашивает, прежде чем что-то отправить, а потом сообщает, осталась ли новая версия или панель сама вернулась на предыдущую.

Установка: новую плату прошить через веб-флешер https://nickoscope.github.io/AnimatedPixelClock/ или записать firmware-v2.5.5-waveshare.bin по адресу 0x0. Уже работающую обновить загрузкой OTA_ONLY_firmware-v2.5.5-waveshare.bin на странице обновления прошивки в портале; полный образ как обновление не загружать. Компаньон статистики ПК для Windows: pc_stats_monitor_v4.exe. Контрольные суммы в SHA256SUMS.txt.
