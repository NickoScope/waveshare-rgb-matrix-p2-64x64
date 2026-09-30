# GitHub Release v2.7.14 (NickoScope/AnimatedPixelClock)

Status: PUBLISHED 2026-09-30 ~23:15 under the owner's night instruction in this chat (22:48 / 23:04): https://github.com/NickoScope/AnimatedPixelClock/releases/tag/v2.7.14 (tag 179d803). The panel runs the release OTA image; health PASS; keys stored.

## Body (English, as posted)

This release is for the Waveshare ESP32-S3-RGB-Matrix board driving a 128x64 HUB75 panel, the only board I have tested it on.

Small fixes on top of 2.7.13:
- A press sent with /api/ir/press is now reported to the twin's sync as a request, like /api/ir/do, not as the real remote.
- A write refused because it came from another site's page now answers 403 everywhere, uploads included.
- The portal opened as http://localhost (the twin on this Mac) can save again.
- A simulated remote press is held at most 10 seconds.

Install:
- For a panel on 2.7.11 or later, open its portal: it offers this release on the Maintenance page, and Update now installs it.
- For an older running board, open its portal, go to Maintenance and drop OTA_ONLY_firmware-v2.7.14-waveshare.bin into "Update over the air". Do not upload the full image as an update.
- For a new board, use the web flasher at https://nickoscope.github.io/AnimatedPixelClock/.
- The Windows PC stats companion is pc_stats_monitor_v4.exe. SHA256SUMS.txt has the checksums.
