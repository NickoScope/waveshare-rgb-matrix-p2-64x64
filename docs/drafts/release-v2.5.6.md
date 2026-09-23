# GitHub Release v2.5.6 (NickoScope/AnimatedPixelClock): draft

Status: DRAFT, waiting for the owner's "отправляй". Source: main 00c5af2 (release images built by
release.py: release/v2.5.6/, SHA256 of the OTA image d44458255c5573b2...). The panel runs this exact
OTA image: confirmed valid, self-test PASS. On "отправляй": commit docs/firmware/latest + release/,
push, tag v2.5.6, publish the GitHub Release with the assets.

Title: AnimatedPixelClock v2.5.6

## Body (English, as it would be posted)

This release is for the Waveshare ESP32-S3-RGB-Matrix board driving a 128x64 HUB75 panel, the only board I have tested it on. Three things changed: the panel stays on the network, it writes Russian on every screen, and it stops doing work for screens nobody is looking at.

The network. On 2.5.5 the panel could still drop off the network in ordinary use. The Wi-Fi driver takes its 1,626 byte receive buffers from a small pool of internal memory. On 2.5.5 that pool had 13 to 15 KB free, and at times it went down to 172 bytes. When a buffer could not be had, the panel stopped answering for about three minutes, until the link watchdog restarted Wi-Fi. Most of that memory was held by the pages and effects themselves, so in 2.5.6 about 36 KB of their state lives in the board's 16 MB of PSRAM instead. The frame buffers stay where they were, so double buffering and colour depth are unchanged. On my panel the pool now has 30 to 50 KB free. Over a two hour run it never went below 21.5 KB and no allocation failed.

Russian on every screen. Text on the panel is now UTF-8 in both of its fonts, capitals and lowercase. That covers notifications, cards, media titles, the flight and rail boards, city and airport names, the original clock screens and Lua effects. Up to now Cyrillic worked only in Lua effects and on the world clock, and a notification in Russian came out as garbage. The Cyrillic letters come from the public-domain X11 misc-fixed fonts, sized to stand next to the Latin ones. Letters that look like Latin ones use exactly the same pixels. Anything the fonts cannot draw shows as a solid block. A Lua effect can pick the font: px.text(x, y, s, r, g, b, "5x7") or "pico"; without that it draws as before. The portal accepts Cyrillic city and airport names. It no longer turns Й into И or Ё into Е.

Work only for what is on screen. The room radar feed from the presence sensor is now received only while a page that shows it is on screen, the room radar or the aquarium. The board's temperature sensor is read only while the weather clock shows it, or when Home Assistant uses it as a room sensor. Before, both ran all the time.

Smaller things: the portal's list of pages no longer shows empty rows for unused effect slots. Lua effects and market pages are grouped under one switch each, since that is how the panel turns them on and off. The weather location and the world clock's home now follow what you set, not a guess from the internet address. For people using the tools in tools/agent, the health self-test now checks the new behaviour.

Install: for a new board, use the web flasher at https://nickoscope.github.io/AnimatedPixelClock/ or write firmware-v2.5.6-waveshare.bin at 0x0. For a board that is already running, upload OTA_ONLY_firmware-v2.5.6-waveshare.bin on the portal's firmware update page, or let the tools in tools/agent do it. Do not upload the full image as an update. The Windows PC stats companion is pc_stats_monitor_v4.exe. SHA256SUMS.txt has the checksums.

## Русский перевод (для владельца, не публикуется)

Этот релиз для платы Waveshare ESP32-S3-RGB-Matrix с панелью HUB75 128x64, единственной, на которой я его проверял. Изменились три вещи: панель держится в сети, пишет по-русски на любом экране и перестала работать на экраны, которые никто не смотрит.

Сеть. На 2.5.5 панель всё ещё могла выпасть из сети в обычной работе. Wi-Fi берёт приёмные буферы по 1 626 байт из небольшого пула внутренней памяти. На 2.5.5 в нём было свободно 13–15 КБ, а временами оставалось 172 байта. Когда буфер взять было негде, панель переставала отвечать минуты на три, пока сторожевой таймер не перезапускал Wi-Fi. Большую часть этой памяти занимали сами страницы и эффекты, поэтому в 2.5.6 около 36 КБ их данных живут в 16 МБ PSRAM платы. Кадровые буферы остались на месте: двойная буферизация и глубина цвета не менялись. На моей панели в пуле теперь свободно 30–50 КБ. За двухчасовой прогон ниже 21,5 КБ он не опускался, и ни одно выделение памяти не сорвалось.

Русский на любом экране. Текст на панели теперь UTF-8 в обоих её шрифтах, заглавные и строчные. Это касается уведомлений, карточек, названий песен, табло рейсов и поездов, названий городов и аэропортов, авторских часов и Lua-эффектов. До этого кириллица работала только в Lua-эффектах и на мировых часах, а уведомление по-русски выходило мусором. Буквы взяты из общедоступных шрифтов X11 misc-fixed и подогнаны по размеру к латинице. Похожие на латинские буквы нарисованы теми же пикселями. Всё, чего в шрифтах нет, показывается сплошным прямоугольником. Lua-эффект может выбрать шрифт: px.text(x, y, s, r, g, b, "5x7") или "pico"; без этого рисует как раньше. Портал принимает кириллические названия городов и аэропортов и больше не превращает Й в И, а Ё в Е.

Работа только для того, что на экране. Данные с датчика присутствия теперь принимаются только пока на экране страница, которая их показывает, — радар комнаты или аквариум. Датчик температуры на плате опрашивается только пока его показывают часы с погодой или когда Home Assistant берёт его как датчик комнаты. Раньше и то и другое работало всё время.

Мелочи: в списке страниц портала больше нет пустых строк от незанятых слотов эффектов. Lua-эффекты и страницы рынков собраны под одним переключателем на группу — панель и включает их так. Место для погоды и домашний город мировых часов теперь берутся из ваших настроек, а не угадываются по интернет-адресу. Для инструментов в tools/agent самотест теперь проверяет новое поведение.

Установка: новую плату прошить через веб-флешер https://nickoscope.github.io/AnimatedPixelClock/ или записать firmware-v2.5.6-waveshare.bin по адресу 0x0. Уже работающую обновить загрузкой OTA_ONLY_firmware-v2.5.6-waveshare.bin на странице обновления прошивки в портале или инструментами из tools/agent. Полный образ как обновление не загружать. Компаньон статистики ПК для Windows: pc_stats_monitor_v4.exe. Контрольные суммы в SHA256SUMS.txt.
