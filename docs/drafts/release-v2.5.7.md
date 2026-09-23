# GitHub Release v2.5.7 (NickoScope/AnimatedPixelClock): draft

Status: DRAFT. It is published on the owner's "отправляй".

- Release commit: 3538de3, local, not pushed. Pushing it updates the web
  flasher.
- The release OTA image (SHA-256 24f1a343966aa1ab…) is on the owner's panel.
  The self-test with --effects passed.

Title: AnimatedPixelClock v2.5.7

## Body (English, as it would be posted)

This release is for the Waveshare ESP32-S3-RGB-Matrix board driving a 128x64 HUB75 panel, the only board I have tested it on. It is about Lua effects: you can now choose which ones play, remove the ones you uploaded, and add new ones from a gallery, all from the portal.

Choosing which effects play. On the portal's Effects & clips page every Lua effect has its own switch. An effect that is switched off is skipped by the knob and by the carousel, but Show still puts it on screen. The panel keeps the switches by effect name across reboots, so uploading or deleting another effect does not move them. Before, the effects could only be switched on and off all together.

Deleting. Effects you uploaded have a Delete button. It takes two presses: the first turns it red and asks "Sure? Delete", the second deletes. There is no pop-up, because some browsers block pop-ups, and there Delete did nothing at all. The other Delete buttons in the portal (clips, world clock cities, airports) now work the same way.

The gallery. "Add from the gallery" lists the effects in this repository's gallery folder, with a preview of each, and puts the one you pick on the panel. Your browser fetches the list and the script from GitHub and sends it to the panel; the panel itself does not go to the internet for it. The gallery has nine screens now: an aquarium that notices people in the room, fireworks over the bay of Cannes, a Starship flight every minute, La Gioconda in characters, a flip-disc clock, an autumn park, the sea at sunset, a city in the evening and a photograph of trees.

An upload whose name would show the same as an effect already on the panel is refused. Before, an upload called "la_gioconda" next to the built-in LA GIOCONDA made two effects with one name.

For people using the tools in tools/agent: the MCP server has effect_walk for the switches, and gallery tools for agents. An agent publishes into a branch on its own machine and never gets write access to GitHub. A person checks each screen and brings it here with tools/agent/gallery.py sync. A photograph goes in only if no person is in it.

Install: for a new board, use the web flasher at https://nickoscope.github.io/AnimatedPixelClock/ or write firmware-v2.5.7-waveshare.bin at 0x0. For a board that is already running, upload OTA_ONLY_firmware-v2.5.7-waveshare.bin on the portal's firmware update page, or let the tools in tools/agent do it. Do not upload the full image as an update. The Windows PC stats companion is pc_stats_monitor_v4.exe. SHA256SUMS.txt has the checksums.

## Русский перевод (для владельца, не публикуется)

Этот релиз для платы Waveshare ESP32-S3-RGB-Matrix с панелью HUB75 128x64, единственной, на которой я его проверял. Он про Lua-эффекты: теперь из портала можно выбрать, какие из них играют, удалить загруженные и добавить новые из галереи.

Выбор эффектов. На странице портала Effects & clips у каждого Lua-эффекта свой переключатель. Выключенный эффект пропускают ручка и карусель, но кнопка Show по-прежнему выводит его на экран. Панель помнит переключатели по имени эффекта и после перезагрузки, так что загрузка или удаление другого эффекта их не сдвигает. Раньше эффекты включались и выключались только все вместе.

Удаление. У загруженных эффектов есть кнопка Delete. Она срабатывает со второго нажатия: первое делает её красной с надписью «Sure? Delete», второе удаляет. Всплывающего окна нет, потому что некоторые браузеры блокируют такие окна, и там Delete не делала ничего. Остальные кнопки Delete в портале (клипы, города мировых часов, аэропорты) теперь работают так же.

Галерея. «Add from the gallery» показывает эффекты из папки gallery этого репозитория, с превью, и ставит выбранный на панель. Список и скрипт с GitHub загружает твой браузер и передаёт панели; сама панель за ними в интернет не ходит. В галерее теперь девять экранов: аквариум, который замечает людей в комнате, фейерверки над бухтой Канн, полёт Starship каждую минуту, Джоконда из символов, часы из переворачивающихся дисков, осенний парк, море на закате, вечерний город и фотография деревьев.

Загрузка эффекта под именем, которое на панели выглядело бы так же, как у уже существующего, отклоняется. Раньше загрузка «la_gioconda» рядом со встроенной LA GIOCONDA давала два эффекта с одним именем.

Для инструментов в tools/agent: в MCP-сервере есть effect_walk для переключателей и инструменты галереи для агентов. Агент публикует в ветку на своей машине и права на запись в GitHub никогда не получает. Человек проверяет каждый экран и переносит его сюда командой tools/agent/gallery.py sync. Фотография попадает в галерею, только если на ней нет людей.

Установка: новую плату прошить через веб-флешер https://nickoscope.github.io/AnimatedPixelClock/ или записать firmware-v2.5.7-waveshare.bin по адресу 0x0. Уже работающую обновить загрузкой OTA_ONLY_firmware-v2.5.7-waveshare.bin на странице обновления прошивки в портале или инструментами из tools/agent. Полный образ как обновление не загружать. Компаньон статистики ПК для Windows: pc_stats_monitor_v4.exe. Контрольные суммы в SHA256SUMS.txt.
