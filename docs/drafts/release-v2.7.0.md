# GitHub Release v2.7.0 (NickoScope/AnimatedPixelClock)

Status: PUBLISHED 2026-09-24 on the owner's "Отправляй": https://github.com/NickoScope/AnimatedPixelClock/releases/tag/v2.7.0 (tag at 4205882). The flasher serves v2.7.0.

Checked before this draft:
- The release OTA image (release/v2.7.0/OTA_ONLY_firmware-v2.7.0-waveshare.bin,
  SHA-256 a9c728836e66c7ce...) is on the owner's panel.
- Self-test with effects: PASS.
- Golf Pestovo on it: 13.8-14.4 fps.
- Gate audits of every firmware change: APPROVED.
- Parity firmware/simulator: 92/92 identical.

## Body (English, as it would be posted)

This release is for the Waveshare ESP32-S3-RGB-Matrix board driving a 128x64 HUB75 panel, the only board I have tested it on.

The main thing is that Lua effects can now show real 3D on the panel itself, not only in the simulator on a computer.

- px.terrain draws ground that goes into the distance in one call: a height map seen from a camera, lit by the sun, with a pattern for each kind of ground, water that shows the sky, and haze. It runs in the firmware, many times faster than the same thing written in Lua, so the camera can fly over a landscape at the frame rate.
- px.save and px.restore keep a copy of the picture and put it back. A still scene is drawn once, and after that each frame only draws what moves. The first effect that uses both went from 6-12 to about 14 frames a second.
- A script can now be as big as it needs, up to 512 KB, limited only by the free space on the panel. It used to be 50 KB.
- The letter Й was drawn so that it read as А in both fonts. It reads as Й now.
- The native helpers count their work against the frame's time budget, so a broken script cannot hang the panel.

There are two new screens in the gallery that need this firmware: golf in 3D on two real courses, the Old Course at Cannes-Mandelieu and the Pestovo golf club near Moscow. Two players play all eighteen holes in four minutes, with a flyover of every hole, the tee shot from behind the player with the ball's tracer, the play from above with a plan of the hole in the corner, and the last putt with the crowd. The Old Course is built from OpenStreetMap data, so its holes, bunkers, water and woods are where they really are.

Install: for a new board, use the web flasher at https://nickoscope.github.io/AnimatedPixelClock/ or write firmware-v2.7.0-waveshare.bin at 0x0. For a board that is already running, upload OTA_ONLY_firmware-v2.7.0-waveshare.bin on the portal's firmware update page, or let the tools in tools/agent do it. Do not upload the full image as an update. The Windows PC stats companion is pc_stats_monitor_v4.exe. SHA256SUMS.txt has the checksums.

## Русский перевод (для владельца, не публикуется)

Этот релиз для платы Waveshare ESP32-S3-RGB-Matrix с панелью HUB75 128x64, другие платы я не проверял.

Главное: Lua-эффекты теперь могут показывать настоящее 3D на самой панели, а не только в симуляторе на компьютере.

- px.terrain одним вызовом рисует уходящую вдаль землю: карту высот, увиденную из камеры, с солнцем, своим рисунком для каждого типа поверхности, водой, в которой видно небо, и дымкой. Это работает в прошивке, во много раз быстрее, чем то же самое на Lua, поэтому камера может пролетать над местностью с нормальной частотой кадров.
- px.save и px.restore сохраняют копию картинки и возвращают её. Неподвижная сцена рисуется один раз, а дальше каждый кадр дорисовывает только то, что движется. Первый эффект, который использует оба, вырос с 6–12 до примерно 14 кадров в секунду.
- Скрипт теперь может быть такого размера, какой ему нужен, до 512 КБ, ограничение только свободное место на панели. Раньше было 50 КБ.
- Буква Й в обоих шрифтах выглядела как А. Теперь читается как Й.
- Встроенные помощники учитывают свою работу в бюджете времени кадра, так что сломанный скрипт не может подвесить панель.

В галерее два новых экрана, которым нужна эта прошивка: гольф в 3D на двух настоящих полях, Old Course в Канн-Манделье и гольф-клуб Пестово под Москвой. Двое игроков проходят все восемнадцать лунок за четыре минуты: облёт каждой лунки, удар с ти из-за спины игрока с трассером мяча, розыгрыш сверху с планом лунки в углу и последний патт со зрителями. Old Course построен по данным OpenStreetMap, поэтому лунки, бункеры, вода и лес там, где они есть на самом деле.

Установка: для новой платы — веб-прошивальщик https://nickoscope.github.io/AnimatedPixelClock/ или запись firmware-v2.7.0-waveshare.bin по адресу 0x0. Для уже работающей — загрузить OTA_ONLY_firmware-v2.7.0-waveshare.bin на странице обновления прошивки в портале или через инструменты из tools/agent. Полный образ как обновление не загружать. Компаньон для Windows — pc_stats_monitor_v4.exe. Контрольные суммы в SHA256SUMS.txt.
