# GitHub Release v2.7.13 (NickoScope/AnimatedPixelClock)

Status: PUBLISHED 2026-09-30 ~23:05. The owner's own words in this chat (22:48): «даже прошивать я вам разрешаю самим свои устройства … сделайте релизы». https://github.com/NickoScope/AnimatedPixelClock/releases/tag/v2.7.13 (tag 50d822b). The panel runs the release OTA image; health PASS; keys stored; UDP events checked from the Mac.

## Body (English, as posted)

This release is for the Waveshare ESP32-S3-RGB-Matrix board driving a 128x64 HUB75 panel, the only board I have tested it on.

New:
- Instant events for the virtual twin. A listener subscribes once (POST /api/sync/listen) and the panel sends it a small UDP message the moment the screen changes and on every press or turn of the knob or the remote, saying who made it. The twin no longer waits for its next poll, and a press inside an effect now reaches the other side too. /api/panel also reports the effect's press count and the last few presses.
- A press made right after switching to an effect is no longer lost.
- A new setting, fbAskHa (in the settings export and import only): switched off, the flight board never asks Home Assistant for a board it does not have, since every such request is a paid AeroAPI call on the Home Assistant side. It is on by default, so nothing changes for an existing panel.
- The web flasher now writes the firmware in its parts, so installing without erasing keeps the Wi-Fi, the settings and the uploaded effects.

Install:
- For a panel on 2.7.11 or later, open its portal: it offers this release on the Maintenance page, and Update now installs it.
- For an older running board, open its portal, go to Maintenance and drop OTA_ONLY_firmware-v2.7.13-waveshare.bin into "Update over the air". Do not upload the full image as an update.
- For a new board, use the web flasher at https://nickoscope.github.io/AnimatedPixelClock/.
- The Windows PC stats companion is pc_stats_monitor_v4.exe. SHA256SUMS.txt has the checksums.
