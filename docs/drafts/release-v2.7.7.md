# GitHub Release v2.7.7 (NickoScope/AnimatedPixelClock)

Status: PUBLISHED 2026-09-30 on the owner's "да, вноси в галерею, делай релиз и начинай KINETIC": https://github.com/NickoScope/AnimatedPixelClock/releases/tag/v2.7.7 (tag at 608f31c). The flasher serves v2.7.7, and the release OTA image (SHA-256 4bad9afe...) is on the owner's panel; health.py PASS after it.

What was checked before this draft:
- **Gate audits (senior-code-audit):** APPROVED for the code (3939046) and for the charges set from measurements (8cea927). One LOW, fixed: the swirl's `turn` unit (radians) was not named in the docs.
- **Parity firmware/simulator:** fx_parity 180/180.
- **Sanitizers** (UBSan, ASan, integer overflow, shifts) over every map kind with parameters at and past their limits: 0 findings.
- **health.py --effects on 2.7.7:** PASS.
- **All 33 effects on the panel** run under it.
- **Measured on the owner's panel**, Wi-Fi on:

  | Call | Time |
  |---|---|
  | building a map | 12-21 ms by kind |
  | px.remap from a layer | 3.2 ms |
  | px.remap from a snapshot | 2.2 ms |

  | Effect | fps | Frame |
  |---|---|---|
  | WARP | 15.2 | 5.6 ms |

## Body (English, as it would be posted)

This release is for the Waveshare ESP32-S3-RGB-Matrix board driving a 128x64 HUB75 panel, the only board I have tested it on. It adds one more family of calls for Lua effects: a picture seen through a map.

New for effects:
- **Tunnels, globes, floors and whirlpools.**
  - `px.uvmap` builds a map once: for every pixel of the screen, where in a picture its colour comes from and how bright it is. There are ready-made maps for a tunnel, a polar view, a lit globe, a floor going off to the horizon (the old mode 7) and a swirl, and a blank one to fill yourself.
  - `px.remap` then redraws the whole screen through the map in one call a frame, from a layer or from a saved frame. Sliding the picture a little each frame makes the tunnel fly, the globe turn and the floor rush past.
  - Building a map takes 12 to 21 ms on the panel, so it is done once at load. A redraw takes about 3 ms.

As before, all of it is integers, so the simulator (tools/luasim) draws exactly what the panel does. AGENTS.md lists what every call costs on the panel, and the SDK's effect_api gives an agent the same.

New in the gallery:
- WARP: four journeys flowing into one another - down a tunnel of plasma, round a turning planet among the stars, along a neon road toward a striped sunset, into a whirlpool.

It needs this firmware.

Install:
- For a new board, use the web flasher at https://nickoscope.github.io/AnimatedPixelClock/ or write firmware-v2.7.7-waveshare.bin at 0x0.
- For a board that is already running, upload OTA_ONLY_firmware-v2.7.7-waveshare.bin on the portal's firmware update page, or let the tools in tools/agent do it. Do not upload the full image as an update.
- The Windows PC stats companion is pc_stats_monitor_v4.exe. SHA256SUMS.txt has the checksums.

## Русский перевод (для владельца, не публикуется)

Этот релиз для платы Waveshare ESP32-S3-RGB-Matrix с панелью HUB75 128x64, другие платы я не проверял. Он добавляет Lua-эффектам ещё одно семейство вызовов: картинку, увиденную через карту.

Новое для эффектов:
- **Туннели, планеты, полы и водовороты.**
  - `px.uvmap` один раз строит карту: для каждого пикселя экрана — откуда в картинке берётся его цвет и насколько он яркий. Есть готовые карты: туннель, полярная, освещённый шар, пол до горизонта (старый mode 7), водоворот, и пустая, чтобы заполнить самому.
  - Потом `px.remap` одним вызовом за кадр перерисовывает весь экран через карту — из слоя или из сохранённого кадра. Если каждый кадр немного сдвигать картинку, туннель летит, планета вращается, пол несётся навстречу.
  - Построение карты на панели занимает 12–21 мс, поэтому её строят один раз при загрузке. Перерисовка — около 3 мс.

Как и раньше, всё в целых числах, поэтому симулятор (tools/luasim) рисует ровно то же, что панель. Сколько стоит каждый вызов на панели — в AGENTS.md, агент получает то же из effect_api в SDK.

Новое в галерее:
- WARP: четыре путешествия, перетекающие одно в другое: по туннелю из плазмы, вокруг вращающейся планеты среди звёзд, по неоновой дороге к полосатому закату, в водоворот.

Ему нужна эта прошивка.

Установка:
- Для новой платы — веб-прошивальщик https://nickoscope.github.io/AnimatedPixelClock/ или запись firmware-v2.7.7-waveshare.bin по адресу 0x0.
- Для уже работающей — загрузить OTA_ONLY_firmware-v2.7.7-waveshare.bin на странице обновления прошивки в портале или через инструменты из tools/agent. Полный образ как обновление не загружать.
- Компаньон для Windows — pc_stats_monitor_v4.exe. Контрольные суммы в SHA256SUMS.txt.
