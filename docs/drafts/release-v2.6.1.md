# GitHub Release v2.6.1 (NickoScope/AnimatedPixelClock)

Status: PUBLISHED 2026-09-24 on the owner's "выпускай 2.6.1": https://github.com/NickoScope/AnimatedPixelClock/releases/tag/v2.6.1 (tag at 152861d). The release OTA image (SHA-256 fd7221dbb90d6a3e...) is on the owner's panel, self-test PASS.

## Body (English, as posted)

This release is for the Waveshare ESP32-S3-RGB-Matrix board driving a 128x64 HUB75 panel, the only board I have tested it on. One small change.

The status marks in the corners, the A or M for the carousel, the Wi-Fi icon and the red dot while the remote is heard, now show only for five seconds after you use the remote and then disappear. They were getting in the way of the pictures. Every press shows them again for another five seconds, so they are there when you are actually changing something and gone when you are just looking.

Install: for a new board, use the web flasher at https://nickoscope.github.io/AnimatedPixelClock/ or write firmware-v2.6.1-waveshare.bin at 0x0. For a board that is already running, upload OTA_ONLY_firmware-v2.6.1-waveshare.bin on the portal's firmware update page, or let the tools in tools/agent do it. Do not upload the full image as an update. The Windows PC stats companion is pc_stats_monitor_v4.exe. SHA256SUMS.txt has the checksums.
