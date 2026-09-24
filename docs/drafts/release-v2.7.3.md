# GitHub Release v2.7.3 (NickoScope/AnimatedPixelClock)

Status: PUBLISHED 2026-09-24 on the owner's "публикуй": https://github.com/NickoScope/AnimatedPixelClock/releases/tag/v2.7.3 (tag at aa553a7). The flasher serves v2.7.3. Links to the presentation pages added to the body at 21:48 on the owner's question.

Checked before this draft:
- The release OTA image (release/v2.7.3/OTA_ONLY_firmware-v2.7.3-waveshare.bin, SHA-256 266f5d297a0a2bf8...) is on the owner's panel.
- Self-test with effects: PASS.
- Gate audits of every firmware change since 2.7.0: APPROVED (four rounds).
- Parity firmware/simulator: 104/104 identical.
- On the panel:
  - OCEANARIUM: 14.9-15.2 fps.
  - The knob and the remote's OK reach the effect.
  - A raw POST to the upload routes is refused and the panel stays up.

## Body (English, as it would be posted)

This release is for the Waveshare ESP32-S3-RGB-Matrix board driving a 128x64 HUB75 panel, the only board I have tested it on.

- Lua effects can use sprites now. px.grab cuts a piece of the canvas out, with black as transparent. px.blit stamps it back in one call, mirrored if you want, dimmed, and mixed toward a colour. An animal drawn once in each pose and stamped after that costs one call a frame instead of forty. The aquarium went from 52-54 to about 40 ms a frame on the panel.
- Effects have a button. On an effect's page, the click of the knob and the OK of the IR remote go to the effect as px.button(). POST /api/lua {"click":true} does the same, which is handy from Home Assistant.
- A crash is fixed. A POST to any upload route (scripts, animations, clips, firmware) that was not a multipart file made the panel crash and reboot. Anything on the network could do it, and it had been there in every version. Such a request is refused now. A firmware upload that is cut off is not answered "OK" any more.

There is a new screen in the gallery, OCEANARIUM: a window into a big public aquarium.
- Over a hundred kinds of sea life live their own lives in it, from reef fish to a whale shark, jellies, an octopus and seahorses.
- The light follows the time of day.
- The curious fish come to the glass where you stand, if you have the presence radar.
- One press of the knob or the remote switches the tank lights. Two run a whole day in five minutes. Three bring it back to the real time.
- It needs this firmware for the button, and 2.7.1 or later for the rest.
- How it works, with the tank running and the numbers from the panel: https://nickoscope.github.io/AnimatedPixelClock/oceanarium/en.html (English), https://nickoscope.github.io/AnimatedPixelClock/oceanarium/ (Russian).

Install:
- For a new board, use the web flasher at https://nickoscope.github.io/AnimatedPixelClock/ or write firmware-v2.7.3-waveshare.bin at 0x0.
- For a board that is already running, upload OTA_ONLY_firmware-v2.7.3-waveshare.bin on the portal's firmware update page, or let the tools in tools/agent do it. Do not upload the full image as an update.
- The Windows PC stats companion is pc_stats_monitor_v4.exe. SHA256SUMS.txt has the checksums.

## Русский перевод (для владельца, не публикуется)

Этот релиз для платы Waveshare ESP32-S3-RGB-Matrix с панелью HUB75 128x64, другие платы я не проверял.

- В Lua-эффектах теперь есть штампы. px.grab вырезает кусок холста, чёрное становится прозрачным. px.blit ставит его обратно одним вызовом: можно зеркально, темнее и с подмешанным цветом. Животное, нарисованное один раз в каждой позе и дальше штампуемое, стоит один вызов за кадр вместо сорока. Аквариум на панели ускорился с 52–54 до примерно 40 мс на кадр.
- У эффектов появилась кнопка. На странице эффекта клик энкодера и OK ИК-пульта приходят в эффект как px.button(). То же делает POST /api/lua {"click":true}, это удобно из Home Assistant.
- Исправлено падение. POST на любой адрес загрузки (скрипты, анимации, клипы, прошивка) не в виде формы с файлом ронял панель и перезагружал её. Это мог сделать кто угодно в сети, и так было во всех версиях. Теперь такой запрос получает отказ. Оборванная загрузка прошивки больше не получает ответ «OK».

В галерее новый экран OCEANARIUM: окно в большой океанариум.
- В нём своей жизнью живёт больше сотни видов морских обитателей, от рифовых рыб до китовой акулы, медуз, осьминога и морских коньков.
- Свет меняется по времени суток.
- Если есть радар присутствия, любопытные рыбы подплывают к стеклу туда, где вы стоите.
- Одно нажатие энкодера или пульта включает и выключает подсветку. Два прогоняют сутки за пять минут. Три возвращают к текущему времени.
- Для кнопки нужна эта прошивка, для остального 2.7.1 или новее.
- Как это устроено, с живым аквариумом и цифрами с панели: https://nickoscope.github.io/AnimatedPixelClock/oceanarium/ (по-русски), https://nickoscope.github.io/AnimatedPixelClock/oceanarium/en.html (по-английски).

Установка:
- Для новой платы — веб-прошивальщик https://nickoscope.github.io/AnimatedPixelClock/ или запись firmware-v2.7.3-waveshare.bin по адресу 0x0.
- Для уже работающей — загрузить OTA_ONLY_firmware-v2.7.3-waveshare.bin на странице обновления прошивки в портале или через инструменты из tools/agent. Полный образ как обновление не загружать.
- Компаньон для Windows — pc_stats_monitor_v4.exe. Контрольные суммы в SHA256SUMS.txt.
