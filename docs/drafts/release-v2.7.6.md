# GitHub Release v2.7.6 (NickoScope/AnimatedPixelClock)

Status: PUBLISHED 2026-09-29 on the owner's "да, вноси в галерею, делай релиз и начинай этап 9": https://github.com/NickoScope/AnimatedPixelClock/releases/tag/v2.7.6 (tag at 0852b96). The flasher serves v2.7.6, and the release OTA image (SHA-256 12aacfc3...) is on the owner's panel.

What was checked before this draft:
- **Gate audits (senior-code-audit):** APPROVED for every commit of stages 7 and 8. Both needed changes first:
  - px.reaction's seed loop could run forever on the panel;
  - px.mesh's projection could overflow.
- **Parity firmware/simulator:** fx_parity 172/172.
- **health.py --effects on 2.7.6:** PASS.
- **All 32 effects on the panel** run under it.
- **Measured on the owner's panel**, Wi-Fi on:

  | Call | Time |
  |---|---|
  | fire | 1.4 ms a step |
  | life | 2.8 ms a step |
  | wave | 2 ms a step |
  | reaction | 9.9 ms a step |
  | a full-height px.aline | 88 us |
  | px.tri | 1.25 us a box pixel |
  | an icosahedron in "both" | 5.4 ms |

  | Effect | fps | Frame |
  |---|---|---|
  | REACTION | 15.2 | 33 ms |
  | SOLIDS | 15.2 | 6 ms |

## Body (English, as it would be posted)

This release is for the Waveshare ESP32-S3-RGB-Matrix board driving a 128x64 HUB75 panel, the only board I have tested it on. It adds two more families of calls for Lua effects.

New for effects:
- **Simulations, a step a frame.**
  - `px.step` runs one step of fire, of Conway's Life (with trails behind the dead) or of ripples on water over a layer.
  - `px.reaction` is Gray-Scott reaction-diffusion over the whole screen. It grows spots that divide like cells, then coral, mazes and worms.
  - Fire takes 1.4 ms a step on the panel, Life 2.8 ms, a wave 2 ms, a reaction step about 10 ms.
- **Smooth lines and 3D.**
  - `px.aline` and `px.dot` draw at fractions of a pixel, so slow motion glides instead of stepping. `px.tri` fills a triangle.
  - `px.model` describes a 3D body once. `px.mesh` then turns it, puts it in perspective and draws it every frame in one call: as a wireframe dimmer with depth, as lit faces sorted by depth, or as both.
  - An icosahedron with faces and edges takes about 5 ms.

As before, all of it is integers, so the simulator (tools/luasim) draws exactly what the panel does. AGENTS.md lists what every call costs on the panel, and the SDK's effect_api gives an agent the same.

Also fixed on the way: a seed placed near the largest integer could lock the effect task in px.reaction, and a vertex right at the eye could overflow px.mesh. Neither was in a release.

New in the gallery:
- REACTION: living patterns that grow, split and turn from spots into coral and mazes, never the same twice.
- SOLIDS: the Platonic solids turning among gliding stars, each reshaping itself into the next.

Both need this firmware.

Install:
- For a new board, use the web flasher at https://nickoscope.github.io/AnimatedPixelClock/ or write firmware-v2.7.6-waveshare.bin at 0x0.
- For a board that is already running, upload OTA_ONLY_firmware-v2.7.6-waveshare.bin on the portal's firmware update page, or let the tools in tools/agent do it. Do not upload the full image as an update.
- The Windows PC stats companion is pc_stats_monitor_v4.exe. SHA256SUMS.txt has the checksums.

## Русский перевод (для владельца, не публикуется)

Этот релиз для платы Waveshare ESP32-S3-RGB-Matrix с панелью HUB75 128x64, другие платы я не проверял. Он добавляет Lua-эффектам ещё два семейства вызовов.

Новое для эффектов:
- **Симуляции, по шагу за кадр.**
  - `px.step` делает на слое один шаг огня, «Жизни» Конвея (с тающими следами умерших клеток) или кругов на воде.
  - `px.reaction` — реакция-диффузия Грея-Скотта на весь экран. Из неё растут пятна, которые делятся как клетки, потом кораллы, лабиринты и черви.
  - На панели огонь занимает 1.4 мс за шаг, «Жизнь» 2.8 мс, волны 2 мс, шаг реакции около 10 мс.
- **Плавные линии и 3D.**
  - `px.aline` и `px.dot` рисуют с дробными координатами, поэтому медленное движение идёт плавно, без ступенек. `px.tri` заливает треугольник.
  - `px.model` описывает 3D-тело один раз. Затем `px.mesh` одним вызовом каждый кадр поворачивает его, ставит в перспективу и рисует: каркасом, тускнеющим с глубиной, освещёнными гранями по глубине или тем и другим.
  - Икосаэдр с гранями и рёбрами — около 5 мс.

Как и раньше, всё в целых числах, поэтому симулятор (tools/luasim) рисует ровно то же, что панель. Сколько стоит каждый вызов на панели — в AGENTS.md, агент получает то же из effect_api в SDK.

Попутно исправлено: семя, поставленное около самого большого целого числа, могло запереть задачу эффекта в `px.reaction`, а вершина прямо у глаза могла переполнить `px.mesh`. Ни то, ни другое не попадало в релиз.

Новое в галерее:
- REACTION: живые узоры, которые растут, делятся и переходят от пятен к кораллам и лабиринтам, ни разу не повторяясь.
- SOLIDS: правильные многогранники вращаются среди плывущих звёзд, и каждый перестраивается в следующий.

Обоим нужна эта прошивка.

Установка:
- Для новой платы — веб-прошивальщик https://nickoscope.github.io/AnimatedPixelClock/ или запись firmware-v2.7.6-waveshare.bin по адресу 0x0.
- Для уже работающей — загрузить OTA_ONLY_firmware-v2.7.6-waveshare.bin на странице обновления прошивки в портале или через инструменты из tools/agent. Полный образ как обновление не загружать.
- Компаньон для Windows — pc_stats_monitor_v4.exe. Контрольные суммы в SHA256SUMS.txt.
