# GitHub Release v2.7.5 (NickoScope/AnimatedPixelClock)

Status: PUBLISHED 2026-09-29 on the owner's "да, вноси в галерею, делай релиз и начинай этап 7": https://github.com/NickoScope/AnimatedPixelClock/releases/tag/v2.7.5 (tag at c4ddd3a). The flasher serves v2.7.5, and the release OTA image (SHA-256 d79fd06d...) is on the owner's panel.

What was checked before this draft:
- **Gate audits (senior-code-audit):** APPROVED for every commit of stages 3-6. Stages 5 and 6 needed changes first: the noise was too slow, and px.particles had two int32 overflows.
- **Parity firmware/simulator:** fx_parity 156/156.
- **health.py --effects on 2.7.5:** PASS.
- **All 30 effects on the panel** run under it.
- **Measured on the owner's panel**, Wi-Fi on, 30 s a bench:

  | Call | Time |
  |---|---|
  | px.mix | 3.0 ms |
  | px.feedback | 6.5 ms |
  | px.field | a sin term 3.7 ms, a ring or ray 11 ms, 3 octaves of noise 18 ms |
  | px.noise | 12.6 us |
  | 800 particles | a step ~1 ms, ~11 ms in a flow field; a draw ~1.5 ms |

  | Effect | fps | Frame |
  |---|---|---|
  | VORTEX | 15.2 | 8.6 ms |
  | NEBULA | 15.2 | 31 ms |
  | FLOW | 15.2 | 6.6 ms |
  | KALEIDOSCOPE | 15.2 | 7.4 ms |
  | LASER CLOCK | 15.2 | 41 ms |

## Body (English, as it would be posted)

This release is for the Waveshare ESP32-S3-RGB-Matrix board driving a 128x64 HUB75 panel, the only board I have tested it on. Like 2.7.4 it is about Lua effects: four more things they can hand to the firmware instead of looping over 8,192 pixels in Lua.

New for effects:
- **Scenes that flow into each other.** `px.save` and `px.restore` now keep four snapshots instead of one, and `px.mix` lays a snapshot over the canvas by any share. To make one scene flow into the next instead of cutting, keep the old one and mix it out while the new one comes in. A whole-screen mix takes 3 ms.
- **`px.feedback`.** The picture on the screen is zoomed, turned, moved and faded a little each frame before the new drawing goes on top. It is the MilkDrop trick: whirlpools, tunnels and spirals from a few dots. One call takes 6.5 ms.
- **`px.noise` and `px.field`.** `px.noise` is Perlin noise, for anything that should wander smoothly. `px.field` fills a layer with a sum of waves, rings, rays and fractal noise in one call, and `px.show` colours it through a palette: plasma, clouds or a nebula over the whole screen. Noise is sampled on a grid and interpolated, so three octaves take 18 ms.
- **`px.particles`.** A particle system in the firmware, up to 4096 particles:
  - they come from a point or a box with jittered speed, direction, life and colour;
  - gravity, drag and a flow field made from noise move them, and they bounce, wrap or leave at the edges;
  - they are drawn fading out with their life.

  800 particles step in about 1 ms and draw in 1.5 ms.

Everything new is in integers, so an effect draws exactly the same in the simulator (tools/luasim) as on the panel. What each call costs on the panel is in AGENTS.md, and an agent gets the same from the SDK's effect_api.

New in the gallery:
- VORTEX: shapes at a wandering centre stream outward into a whirlpool that never repeats.
- NEBULA: a cloud of gas and stars that boils slowly, in four moods.
- FLOW: hundreds of motes on currents that never repeat, a fountain of sparks, and snow.
- KALEIDOSCOPE and LASER CLOCK now flow from one scene into the next.

Each of these needs this firmware. On older firmware KALEIDOSCOPE and LASER CLOCK still work, only without the flow.

Install:
- For a new board, use the web flasher at https://nickoscope.github.io/AnimatedPixelClock/ or write firmware-v2.7.5-waveshare.bin at 0x0.
- For a board that is already running, upload OTA_ONLY_firmware-v2.7.5-waveshare.bin on the portal's firmware update page, or let the tools in tools/agent do it. Do not upload the full image as an update.
- The Windows PC stats companion is pc_stats_monitor_v4.exe. SHA256SUMS.txt has the checksums.

## Русский перевод (для владельца, не публикуется)

Этот релиз для платы Waveshare ESP32-S3-RGB-Matrix с панелью HUB75 128x64, другие платы я не проверял. Как и 2.7.4, он про Lua-эффекты: ещё четыре вещи, которые эффект может отдать прошивке вместо цикла Lua по 8192 пикселям.

Новое для эффектов:
- **Сцены, перетекающие друг в друга.** `px.save` и `px.restore` теперь хранят четыре снимка вместо одного, а `px.mix` накладывает снимок на холст в любой доле. Чтобы сцена не обрывалась, а перетекала в следующую, старая сохраняется и растворяется, пока приходит новая. Смешивание всего экрана — 3 мс.
- **`px.feedback`.** Картинка на экране каждый кадр немного увеличивается, поворачивается, сдвигается и тускнеет, а поверх рисуется новое. Это приём MilkDrop: воронки, туннели и спирали из нескольких точек. Один вызов — 6.5 мс.
- **`px.noise` и `px.field`.** `px.noise` — шум Перлина, для всего, что должно плавно блуждать. `px.field` одним вызовом заполняет слой суммой волн, колец, лучей и фрактального шума, а `px.show` раскрашивает его палитрой: плазма, облака или туманность на весь экран. Шум считается на сетке и интерполируется, поэтому три октавы занимают 18 мс.
- **`px.particles`.** Система частиц в прошивке, до 4096 частиц:
  - они вылетают из точки или области с разбросом скорости, направления, жизни и цвета;
  - их двигают гравитация, сопротивление и поле течений из шума, на краях они отскакивают, переходят на другую сторону или исчезают;
  - рисуются, угасая к концу жизни.

  800 частиц делают шаг примерно за 1 мс и рисуются за 1.5 мс.

Всё новое считается в целых числах, поэтому эффект рисует в симуляторе (tools/luasim) ровно то же, что на панели. Сколько стоит каждый вызов на панели — в AGENTS.md, агент получает то же из effect_api в SDK.

Новое в галерее:
- VORTEX: фигуры в блуждающем центре уносятся в вихрь, который не повторяется.
- NEBULA: облако газа и звёзд, медленно клубится, четыре настроения.
- FLOW: сотни частиц на течениях, которые не повторяются, фонтан искр и снег.
- KALEIDOSCOPE и LASER CLOCK теперь перетекают из сцены в сцену.

Каждому из них нужна эта прошивка. На старой KALEIDOSCOPE и LASER CLOCK работают, только без перетекания.

Установка:
- Для новой платы — веб-прошивальщик https://nickoscope.github.io/AnimatedPixelClock/ или запись firmware-v2.7.5-waveshare.bin по адресу 0x0.
- Для уже работающей — загрузить OTA_ONLY_firmware-v2.7.5-waveshare.bin на странице обновления прошивки в портале или через инструменты из tools/agent. Полный образ как обновление не загружать.
- Компаньон для Windows — pc_stats_monitor_v4.exe. Контрольные суммы в SHA256SUMS.txt.
