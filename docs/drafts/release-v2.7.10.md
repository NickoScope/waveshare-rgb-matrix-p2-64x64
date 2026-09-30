# GitHub Release v2.7.10 (NickoScope/AnimatedPixelClock)

Status: PUBLISHED 2026-09-30 ~21:18 on the owner's «да, выпускай 2.7.10»: https://github.com/NickoScope/AnimatedPixelClock/releases/tag/v2.7.10 (tag at 1dbe9a0). The version alone over 2.7.9, so the owner can update the panel from the portal (Maintenance, Update over the air, OTA_ONLY a1d6b1f9...) and the twin's sync can follow. Not flashed by me: the owner updates it himself.

## Body (English, as posted)

This release is for the Waveshare ESP32-S3-RGB-Matrix board driving a 128x64 HUB75 panel, the only board I have tested it on.

Nothing new in the firmware itself: it is 2.7.9 with the version number raised, so a running panel can be updated from its own portal and the update path can be checked end to end. See v2.7.9 for the security fixes and the Keys page.

Install:
- For a board that is already running, open its portal, go to Maintenance and drop OTA_ONLY_firmware-v2.7.10-waveshare.bin into "Update over the air". Do not upload the full image as an update.
- For a new board, use the web flasher at https://nickoscope.github.io/AnimatedPixelClock/ or write firmware-v2.7.10-waveshare.bin at 0x0.
- The Windows PC stats companion is pc_stats_monitor_v4.exe. SHA256SUMS.txt has the checksums.
