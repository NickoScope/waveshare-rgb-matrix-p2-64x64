# GitHub Release v2.7.11 (NickoScope/AnimatedPixelClock)

Status: PUBLISHED 2026-09-30 ~21:44 on the owner's «выпускай 2.7.11»: https://github.com/NickoScope/AnimatedPixelClock/releases/tag/v2.7.11 (tag abf7f35). The panel runs the release OTA image (f65e0705...); health PASS; LADY WITH DOG kept. First release with OTA_ONLY on the flasher's Pages, so the portal's Update now works from the release after it.

## Body (English, as posted)

This release is for the Waveshare ESP32-S3-RGB-Matrix board driving a 128x64 HUB75 panel, the only board I have tested it on.

New: the portal tells you when a newer firmware is out. Open the panel's portal and, if there is a new release, you will see a badge next to the version at the top and a New firmware card on the Maintenance page. Update now downloads the firmware from GitHub and installs it over the air after you confirm; What's new opens the release notes. Settings and keys stay. The check is made by your browser, not by the panel, and sends nothing about your network to GitHub.

This works from this release on: the first update it will offer is the one after 2.7.11.

Install:
- For a board that is already running, open its portal, go to Maintenance and drop OTA_ONLY_firmware-v2.7.11-waveshare.bin into "Update over the air". Do not upload the full image as an update.
- For a new board, use the web flasher at https://nickoscope.github.io/AnimatedPixelClock/ or write firmware-v2.7.11-waveshare.bin at 0x0.
- The Windows PC stats companion is pc_stats_monitor_v4.exe. SHA256SUMS.txt has the checksums.
