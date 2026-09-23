# GitHub Release v2.5.9 (NickoScope/AnimatedPixelClock)

Status: PUBLISHED 2026-09-23 22:38 on the owner's "выпускай 2.5.9": https://github.com/NickoScope/AnimatedPixelClock/releases/tag/v2.5.9 (tag at 2c6d186). The release OTA image (SHA-256 4510fd4d09f48e55...) is on the owner's panel, self-test --effects PASS.

## Body (English, as posted)

This release is for the Waveshare ESP32-S3-RGB-Matrix board driving a 128x64 HUB75 panel, the only board I have tested it on. It does two things.

The panel now refuses a Lua effect that would not run. Until now an uploaded script was checked for its syntax and size and then stored, so a script that looked fine in the simulator but was too heavy for the panel's processor got in and showed nothing but an error. Now the panel runs every upload once before it keeps it, off screen and without touching what is showing: the load and four frames, under the same limits it runs effects with. If the script fails, or a frame takes more than 500 ms, the upload is refused with the measured frame times and nothing is stored. An accepted upload reports what it cost. The limits, and what each drawing call costs on this panel as measured through that trial, are written down in AGENTS.md, so whoever writes an effect, a person or an AI agent, can see in advance what will fit.

The world clock can now change its home city from the knob or the remote. Press to go into the page, then left and right step through the cities you set up in the portal, and the choice is kept.

Install: for a new board, use the web flasher at https://nickoscope.github.io/AnimatedPixelClock/ or write firmware-v2.5.9-waveshare.bin at 0x0. For a board that is already running, upload OTA_ONLY_firmware-v2.5.9-waveshare.bin on the portal's firmware update page, or let the tools in tools/agent do it. Do not upload the full image as an update. The Windows PC stats companion is pc_stats_monitor_v4.exe. SHA256SUMS.txt has the checksums.
