# GitHub Release v2.7.9 (NickoScope/AnimatedPixelClock)

Status: DRAFT. The owner said to release (18:13 2026-09-30, «да, выпускай 2.7.9 как только получишь результтаты аудита»). It waits for the panel to be free after the simulation session's functional test, then the security fixes are checked on the panel.

What goes in:
- **The Keys page** (513c027, 292c60d): AeroAPI, Realtime Trains and AIS keys entered on the portal, write-only, taken without a restart.
- **The twin's sync routes** (the simulation session, b7c430e, 4b7037c): GET|HEAD /api/firmware/image behind X-Twin-Sync, and GET /api/lua/source.
- **Web security** (d84c61c..1be7fbc), found by the functional test and the gate audits:
  - /reset is POST with a confirmation;
  - every write refuses another site's page;
  - two irreversible GETs became POSTs;
  - the export and the market are no longer readable by other sites;
  - DNS rebinding is refused on the private reads.
  - Reported upstream as Keralots/AnimatedPixelClock#11.

## Body (English, as it would be posted)

This release is for the Waveshare ESP32-S3-RGB-Matrix board driving a 128x64 HUB75 panel, the only board I have tested it on.

Security. Please update: until now any web page opened in a browser on the same network could reset the clock to factory settings with a single image, flash its own firmware, or change the settings, without anyone clicking anything. Now:
- Factory reset only works from the portal's own button, with a confirmation.
- Everything that changes something (settings, import, rename, uploads, firmware, deletes, keys, notifications) is refused when it comes from another site's page. Home Assistant, curl and scripts are not affected, because they don't send the header a browser does.
- Deleting an uploaded animation and forgetting the remote's learned codes are no longer plain links.
- Other sites can no longer read the settings export (it holds the weather API key) or the market pages' data.

New:
- A Keys page in the portal for the FlightAware AeroAPI key, the Realtime Trains token and the aisstream.io key. The portal only shows whether a key is stored, never the key itself, and the settings export leaves them out. A new key is picked up at the next fetch without a restart.
- Two read-only routes for the virtual twin: /api/firmware/image (the running firmware, only with the X-Twin-Sync: 1 header; the picture holds still for the 6 to 7 seconds it takes) and /api/lua/source (an uploaded effect's script).

Install:
- For a new board, use the web flasher at https://nickoscope.github.io/AnimatedPixelClock/ or write firmware-v2.7.9-waveshare.bin at 0x0.
- For a board that is already running, upload OTA_ONLY_firmware-v2.7.9-waveshare.bin on the portal's firmware update page, or let the tools in tools/agent do it. Do not upload the full image as an update.
- The Windows PC stats companion is pc_stats_monitor_v4.exe. SHA256SUMS.txt has the checksums.

## Русский перевод (для владельца, не публикуется)

Этот релиз для платы Waveshare ESP32-S3-RGB-Matrix с панелью HUB75 128x64, другие платы я не проверял.

Безопасность. Пожалуйста, обновитесь: до сих пор любая веб-страница, открытая в браузере в той же сети, могла одной картинкой сбросить часы к заводским настройкам, залить свою прошивку или поменять настройки, и никому ничего не нужно было нажимать. Теперь:
- Сброс к заводским настройкам работает только с кнопки в самом портале, с подтверждением.
- Всё, что что-то меняет (настройки, импорт, переименование, загрузки, прошивка, удаление, ключи, уведомления), отклоняется, если пришло с чужой страницы. Home Assistant, curl и скрипты не затронуты: они не шлют заголовок, который шлёт браузер.
- Удаление загруженной анимации и забывание выученных кодов пульта больше не простые ссылки.
- Чужие сайты больше не могут прочитать экспорт настроек (там ключ погоды) и данные страниц рынка.

Новое:
- Страница Keys в портале для ключа FlightAware AeroAPI, токена Realtime Trains и ключа aisstream.io. Портал показывает только, задан ли ключ, но никогда сам ключ, и экспорт настроек их не содержит. Новый ключ берётся со следующего запроса без перезагрузки.
- Два маршрута только для чтения для виртуального двойника: /api/firmware/image (работающая прошивка, только с заголовком X-Twin-Sync: 1; картинка стоит 6–7 секунд, пока она отдаётся) и /api/lua/source (текст загруженного эффекта).

Установка:
- Для новой платы — веб-прошивальщик https://nickoscope.github.io/AnimatedPixelClock/ или запись firmware-v2.7.9-waveshare.bin по адресу 0x0.
- Для уже работающей — загрузить OTA_ONLY_firmware-v2.7.9-waveshare.bin на странице обновления прошивки в портале или через инструменты из tools/agent. Полный образ как обновление не загружать.
- Компаньон для Windows — pc_stats_monitor_v4.exe. Контрольные суммы в SHA256SUMS.txt.
