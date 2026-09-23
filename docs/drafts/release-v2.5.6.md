# GitHub Release v2.5.6 (NickoScope/AnimatedPixelClock): draft

Status: DRAFT, not published. Waiting for the owner's "отправляй". Source: branch
feat/state-in-psram (dad3de2), not yet merged to main. Before publishing: merge to
main, run release.py (all three boards), tag.

Title: AnimatedPixelClock v2.5.6

## Body (English, as it would be posted)

This release is for the Waveshare ESP32-S3-RGB-Matrix board driving a 128x64 HUB75 panel, the only board I have tested it on. It has one change, and it is about the network.

On 2.5.5 the panel could still drop off the network in ordinary use, with nobody touching it. The Wi-Fi driver takes its 1,626 byte receive buffers from a small pool of internal memory that can be used for DMA. On 2.5.5 that pool had 13 to 15 KB free and at times went down to 172 bytes. When a buffer could not be had, the panel stopped answering for about three minutes, until the link watchdog restarted Wi-Fi.

Most of that memory was held by the pages and effects themselves: the world clock's colour map, the frames of a custom animation, the clock games, the star fields, the flight, train and yacht boards. They don't need fast internal memory, so in 2.5.6 all of it, about 35 KB, lives in the board's 16 MB of PSRAM. The panel's own frame buffers stay where they were. Double buffering and colour depth are unchanged, so the picture is exactly what it was.

What I measured on my panel. After the change the pool has 47 to 50 KB free and has not gone below 23 KB, including on the yacht radar page with its live data stream open. The self test passed at a normal pace and at two page changes a second, with no failed allocations. On 2.5.5 the same normal-pace test gave warnings twice. I also showed every clock style and every page in turn: the panel did not restart once. Then I left it running on the carousel for two hours and twenty minutes, with the pool read every 30 seconds: 279 readings out of 279 answered, 30 to 50 KB free, 21.5 KB at the lowest, no failed allocations, no network recovery and no restart. The self test at the end passed as well.

Install: for a new board, use the web flasher at https://nickoscope.github.io/AnimatedPixelClock/ or write firmware-v2.5.6-waveshare.bin at 0x0. For a board that is already running, upload OTA_ONLY_firmware-v2.5.6-waveshare.bin on the portal's firmware update page, and do not upload the full image as an update. The panel can also be updated from the tools in tools/agent. The Windows PC stats companion is pc_stats_monitor_v4.exe. SHA256SUMS.txt has the checksums.

## Русский перевод (для владельца, не публикуется)

Этот релиз для платы Waveshare ESP32-S3-RGB-Matrix с панелью HUB75 128x64, единственной, на которой я его проверял. В нём одно изменение, и оно про сеть.

На 2.5.5 панель всё ещё могла выпасть из сети в обычной работе, когда её никто не трогал. Wi-Fi берёт приёмные буферы по 1 626 байт из небольшого пула внутренней памяти, пригодной для DMA. На 2.5.5 в этом пуле было свободно 13–15 КБ, а временами оставалось 172 байта. Когда буфер взять было негде, панель переставала отвечать минуты на три, пока сторожевой таймер связи не перезапускал Wi-Fi.

Большую часть этой памяти занимали сами страницы и эффекты: карта цветов мировых часов, кадры своей анимации, игры-часы, звёздные поля, табло рейсов, поездов и яхт. Быстрая внутренняя память им не нужна, поэтому в 2.5.6 всё это, около 35 КБ, живёт в 16 МБ PSRAM платы. Собственные кадровые буферы панели остались на месте. Двойная буферизация и глубина цвета не менялись, картинка ровно та же.

Что я намерил на своей панели. После изменения в пуле свободно 47–50 КБ, и ниже 23 КБ он не опускался, в том числе на странице яхтенного радара с открытым потоком данных. Самотест прошёл и в обычном темпе, и при двух сменах страниц в секунду, без единого сбоя выделения памяти. На 2.5.5 тот же тест в обычном темпе дважды дал предупреждения. Ещё я по очереди показал все стили часов и все страницы: панель ни разу не перезагрузилась. Потом панель два часа двадцать минут работала на карусели, пул считывался каждые 30 секунд: ответ пришёл на все 279 опросов, свободно 30–50 КБ, минимум 21,5 КБ, ни одного сбоя выделения, ни одного восстановления сети, ни одной перезагрузки. Самотест в конце тоже прошёл.

Установка: новую плату прошить через веб-флешер https://nickoscope.github.io/AnimatedPixelClock/ или записать firmware-v2.5.6-waveshare.bin по адресу 0x0. Уже работающую обновить загрузкой OTA_ONLY_firmware-v2.5.6-waveshare.bin на странице обновления прошивки в портале; полный образ как обновление не загружать. Панель можно обновить и инструментами из tools/agent. Компаньон статистики ПК для Windows: pc_stats_monitor_v4.exe. Контрольные суммы в SHA256SUMS.txt.
