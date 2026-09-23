# GitHub Release v2.6.0 (NickoScope/AnimatedPixelClock)

Status: PUBLISHED 2026-09-23 on the owner's "да, делай с 36 местами": https://github.com/NickoScope/AnimatedPixelClock/releases/tag/v2.6.0 (tag at 1f80b84). The release OTA image (SHA-256 e08c47892039c2d7...) is on the owner's panel, self-test --effects PASS, 18 effects.

## Body (English, as posted)

This release is for the Waveshare ESP32-S3-RGB-Matrix board driving a 128x64 HUB75 panel, the only board I have tested it on. It changes where Lua effects come from, so please read the second paragraph before you update.

No Lua effect is compiled into the firmware any more. The seven that used to be (the football, snooker, snake and Tetris clocks, Minecraft, the room radar and La Gioconda) now live in the gallery with all the others, and a panel holds up to 36 effects instead of 12 plus the built-in ones. The firmware is about 135 KB smaller, and every effect on a panel is one you chose.

What that means when you update: the seven former built-in effects disappear from your panel until you add them back. Open the portal, go to Effects & clips, and use Add from the gallery; each one takes a second and needs no reboot. Effects you uploaded yourself stay as they are, and so do the switches that keep an effect in or out of the carousel. A freshly flashed board starts with no effects at all and gets them the same way.

Install: for a new board, use the web flasher at https://nickoscope.github.io/AnimatedPixelClock/ or write firmware-v2.6.0-waveshare.bin at 0x0. For a board that is already running, upload OTA_ONLY_firmware-v2.6.0-waveshare.bin on the portal's firmware update page, or let the tools in tools/agent do it. Do not upload the full image as an update. The Windows PC stats companion is pc_stats_monitor_v4.exe. SHA256SUMS.txt has the checksums.
