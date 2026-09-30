# GitHub Release v2.7.8 (NickoScope/AnimatedPixelClock)

Status: PUBLISHED 2026-09-30 on the owner's "да, выпускай 2.7.8": https://github.com/NickoScope/AnimatedPixelClock/releases/tag/v2.7.8 (tag at 9a2fe81). The flasher serves v2.7.8, and the release OTA image (SHA-256 e1004d46...) is on the owner's panel; health.py PASS after it.

What was checked before this draft:
- **Gate audit (senior-code-audit, the simulation session):** APPROVED after fixes. Builds matrix-waveshare-rgb, matrix-s3, matrix-s3-wroom OK; cppcheck 0; gitleaks clean.
- **Twin:** 2.7.8 boots; imported styles 5 and 4 become 0.
- **On the owner's panel:**
  - style 5 stored on 2.7.7 read 0 after 2.7.8;
  - import 4 → 0; 3 and 1 kept;
  - the portal lists four screensavers;
  - screensavers 0, 1, 3 and 6 shown, no errors;
  - health.py PASS.
- **Flash:** 2,327,568 → 2,190,129 bytes.

## Body (English, as it would be posted)

This release is for the Waveshare ESP32-S3-RGB-Matrix board driving a 128x64 HUB75 panel, the only board I have tested it on.

Changed:
- **Two screensavers are gone: Aquarium and Burning room ("This is fine").**
  - The screensavers left are Space Invaders, Pac-Man chase, Starfield and your own uploaded animation.
  - If a panel was set to one of the two removed ones, it switches to Space Invaders by itself after the update. A saved configuration that names them is imported the same way.
  - The firmware is 137 KB smaller.
- The Lua effect AQUARIUM in the gallery is a different thing and stays.

Install:
- For a new board, use the web flasher at https://nickoscope.github.io/AnimatedPixelClock/ or write firmware-v2.7.8-waveshare.bin at 0x0.
- For a board that is already running, upload OTA_ONLY_firmware-v2.7.8-waveshare.bin on the portal's firmware update page, or let the tools in tools/agent do it. Do not upload the full image as an update.
- The Windows PC stats companion is pc_stats_monitor_v4.exe. SHA256SUMS.txt has the checksums.

## Русский перевод (для владельца, не публикуется)

Этот релиз для платы Waveshare ESP32-S3-RGB-Matrix с панелью HUB75 128x64, другие платы я не проверял.

Изменено:
- **Убраны две заставки: Aquarium и Burning room («This is fine»).**
  - Остались Space Invaders, Pac-Man, Starfield и своя загруженная анимация.
  - Если на панели была выбрана одна из убранных, после обновления она сама переключится на Space Invaders. Сохранённые настройки, где они указаны, импортируются так же.
  - Прошивка стала меньше на 137 КБ.
- Lua-эффект AQUARIUM в галерее — это другое, он остаётся.

Установка:
- Для новой платы — веб-прошивальщик https://nickoscope.github.io/AnimatedPixelClock/ или запись firmware-v2.7.8-waveshare.bin по адресу 0x0.
- Для уже работающей — загрузить OTA_ONLY_firmware-v2.7.8-waveshare.bin на странице обновления прошивки в портале или через инструменты из tools/agent. Полный образ как обновление не загружать.
- Компаньон для Windows — pc_stats_monitor_v4.exe. Контрольные суммы в SHA256SUMS.txt.
