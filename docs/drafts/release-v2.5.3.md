# GitHub Release v2.5.3 (NickoScope/AnimatedPixelClock): draft

Status: PUBLISHED 2026-09-23 00:13 on the owner's "делай как автор, публикуй релиз": https://github.com/NickoScope/AnimatedPixelClock/releases/tag/v2.5.3 (tag at 9e9ee88). An earlier choice of "no release page" was reversed after he saw upstream publishes them.

Title: AnimatedPixelClock v2.5.3

## Body (English, as posted)

This is the first release from my fork. It follows upstream v2.3.1, and it is built for one board only: the Waveshare ESP32-S3-RGB-Matrix (32 MB flash, 16 MB PSRAM) driving a 128x64 HUB75 panel. That is the board I have flashed from the web flasher and watched boot, so it is the only one I am offering.

The fix that made me cut this release: opening the web portal could take the panel off the network. The panel kept running and the clock stayed on the screen, but it stopped answering until it was reset. I traced it over USB. The Wi-Fi driver allocates its 1,626 byte receive buffers from the DMA-capable part of internal RAM, and one visit to the portal fired 48 requests, many of them at the same time. Every request waiting its turn held some of those buffers, the largest free DMA block fell from 11,252 to 1,396 bytes, and the radio could not get a buffer. The portal's own memory check was reading the wrong pool, which still showed 7,668 bytes free. In 2.5.3 the portal sends its requests one at a time, the memory check also looks at the DMA pool, and the link watchdog restarts Wi-Fi when it cannot even send a probe twice in a row, instead of waiting fifteen minutes. With all of that in place I clicked through every page, saved settings six times, reloaded the page and had two browsers open at once: 109 pings out of 109 answered and the radio did not fail a single allocation.

Since upstream v2.3.1 the panel has also gained:
Lua effects uploaded over the air, twelve slots of up to 50 KB each, so a new screen no longer needs a firmware flash.
Its own web flasher at https://nickoscope.github.io/AnimatedPixelClock/ with Wi-Fi setup in the browser.
A shared network broker, so the weather, flight board, rail board and other network screens take turns instead of each starting its own task.
A flight board fed directly from FlightAware AeroAPI, a Realtime Trains rail board, a world clock with your own cities, a yacht radar from AIS, a media player screen and a market screen, the last two through Home Assistant.
A presence radar screen that draws real targets from an mmWave sensor over MQTT.
No MQTT broker is assumed any more: the panel only connects to one after you give it an address.

Install: for a new board, use the web flasher above or write firmware-v2.5.3-waveshare.bin at 0x0. For a board that is already running, upload OTA_ONLY_firmware-v2.5.3-waveshare.bin on the portal's firmware update page, and do not upload the full image as an update. The Windows PC stats companion is pc_stats_monitor_v4.exe. SHA256SUMS.txt has the checksums.

## Русский перевод (для владельца, не публикуется)

Это первый релиз моего форка. Он идёт после v2.3.1 из оригинала и собран только под одну плату: Waveshare ESP32-S3-RGB-Matrix (32 МБ флеш, 16 МБ PSRAM) с панелью HUB75 128x64. Именно её я прошивал с веб-флешера и видел, как она загружается, поэтому предлагаю только её.

Исправление, ради которого я выпускаю релиз: открытие веб-портала могло выкинуть панель из сети. Панель продолжала работать, часы на экране шли, но она переставала отвечать до сброса. Я разобрал это по USB. Драйвер Wi-Fi берёт буферы приёма по 1 626 байт из DMA-части внутренней памяти, а один заход на портал давал 48 запросов, многие одновременно. Каждый ждущий запрос держал часть этих буферов, наибольший свободный DMA-блок падал с 11 252 до 1 396 байт, и радио не могло получить буфер. Собственная проверка памяти портала смотрела не на тот пул, где ещё было 7 668 байт. В 2.5.3 портал отправляет запросы по одному, проверка памяти смотрит и на DMA-пул, а сторож связи перезапускает Wi-Fi, если дважды подряд не может даже отправить пробный пакет, вместо ожидания пятнадцати минут. После этого я прошёл по всем страницам, шесть раз сохранил настройки, перезагружал страницу и открывал два браузера сразу: ответили 109 пингов из 109, и радио ни разу не получило отказ в памяти.

С v2.3.1 из оригинала в панели также появились:
Lua-эффекты, загружаемые по сети, двенадцать слотов до 50 КБ, так что новый экран больше не требует перепрошивки.
Свой веб-флешер по адресу https://nickoscope.github.io/AnimatedPixelClock/ с настройкой Wi-Fi прямо в браузере.
Общий сетевой брокер: погода, табло рейсов, табло поездов и другие сетевые экраны ходят в сеть по очереди, а не каждый своей задачей.
Табло рейсов напрямую из FlightAware AeroAPI, табло поездов Realtime Trains, мировые часы со своими городами, яхтенный радар по AIS, экран медиаплеера и экран рынков, последние два через Home Assistant.
Экран радара присутствия, рисующий реальные цели с mmWave-датчика через MQTT.
MQTT-брокер больше не подразумевается: панель подключается к нему, только когда ей дали адрес.

Установка: новую плату прошить через веб-флешер выше или записать firmware-v2.5.3-waveshare.bin по адресу 0x0. Уже работающую обновить загрузкой OTA_ONLY_firmware-v2.5.3-waveshare.bin на странице обновления прошивки в портале; полный образ как обновление не загружать. Компаньон статистики ПК для Windows: pc_stats_monitor_v4.exe. Контрольные суммы в SHA256SUMS.txt.
