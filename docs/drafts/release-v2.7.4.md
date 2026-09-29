# GitHub Release v2.7.4 (NickoScope/AnimatedPixelClock)

Status: PUBLISHED 2026-09-29 on the owner's "вноси конечно в галерею и выкатывай релиз": https://github.com/NickoScope/AnimatedPixelClock/releases/tag/v2.7.4 (tag at 5aa0622). The flasher serves v2.7.4. The release OTA image (SHA-256 db942441...) is on the owner's panel. Before publishing:
- final gate audit APPROVED (4025bd6);
- stack probes on the panel;
- health.py --effects: PASS;
- all 27 effects on the panel run under the new sandbox.

What was checked before this draft:
- **Gate audits (senior-code-audit):** APPROVED, every round:
  - stage 1 (7fcc3cb, 35860b8, f74a358);
  - stage 2 (31bf272..5f275f7);
  - hardening (e0a31c8, 07c6512);
  - stack (51518f0, a88fe38).
- **Parity firmware/simulator:** fx_parity 128/128 identical.
- **Measured on the owner's panel**, 2.7.4, Wi-Fi on, 30 s per bench:

  | | 2.7.3 | 2.7.4 |
  |---|---|---|
  | px.blend | 14.9 us | 7.2 us |
  | px.glow r10 | 6.1 ms | 0.25 ms |
  | px.fade, whole canvas | — | 2.2 ms |
  | px.blur, whole canvas | — | 5.0 ms |
  | px.show | — | 1.4 ms |
  | CANNES | 8.2 fps, 119 ms | 15.2 fps, 24 ms |
  | LASER CLOCK | — | 15.2 fps, 28-29 ms |

  A/B against 2.7.3 at the same hour: OCEANARIUM, ROOM RADAR and KINETIC show no regression.
- **px.weather() and px.city() on the panel:** 24.6 C and GUILDFORD.

## Body (English, as it would be posted)

This release is for the Waveshare ESP32-S3-RGB-Matrix board driving a 128x64 HUB75 panel, the only board I have tested it on. It is mostly about what Lua effects can do, and how fast.

New for effects:
- `px.fade` and `px.blur`. `px.fade` pulls the whole screen, or a part of it, toward a colour in one call: trails, smoke, a fading sky. `px.blur` spreads light to the neighbours, the way FastLED's blur2d does. A fade of the whole screen takes about 2 ms. Before, it took over 100 ms of `px.blend` calls.
- `px.mode("add")`. Lines, circles, rectangles, pixels and text add their light to what is already there, so light that overlaps gets brighter, as lasers and sparks do.
- Palettes and layers:
  - `px.palette` makes a 256-colour palette from colour stops or from Inigo Quilez's cosine formula;
  - `px.layer` holds one byte a pixel;
  - `px.show` paints a layer through a palette, so stepping the offset each frame is the old palette cycling;
  - `px.scroll` and `px.mirror` move or fold the whole screen in one call.
- `px.weather()` and `px.city()` give an effect the weather clock's data and the world clock's home city.
- `px.blend` and `px.glow` now run in integers. The board's FPU has no double precision, so they used to run in software: `px.blend` is twice as fast now and `px.glow` about 24 times. Pixels can differ from before by a level or two out of 255.

Safer:
- An uploaded script could hang the effect task in three ways, and all three are closed:
  - a line to a coordinate like `math.mininteger`;
  - library calls that call back into Lua nested deep enough to run past the task's stack;
  - a `__gc` finalizer, which Lua runs outside the instruction budget.
- Such calls now nest at most 2 deep, and a metatable with `__gc` is refused with a clear message. No script in the gallery does either.

New and faster in the gallery:
- LASER CLOCK: a laser projector on the pavement writes on the wall of a house. Every 5 s it shows the time, the day of the week, the date, the temperature outside, and Cannes.
  - Each text is written stroke by stroke with the beam dark between strokes, then scanned like a real projector does.
  - The RGB laser changes colour with each screen, and the button changes it too.
  - The day of the week and Cannes are in Russian.
- CANNES now fades its sky with `px.fade`: 15 fps instead of 8 on the panel.

Install:
- For a new board, use the web flasher at https://nickoscope.github.io/AnimatedPixelClock/ or write firmware-v2.7.4-waveshare.bin at 0x0.
- For a board that is already running, upload OTA_ONLY_firmware-v2.7.4-waveshare.bin on the portal's firmware update page, or let the tools in tools/agent do it. Do not upload the full image as an update.
- The Windows PC stats companion is pc_stats_monitor_v4.exe. SHA256SUMS.txt has the checksums.

## Русский перевод (для владельца, не публикуется)

Этот релиз для платы Waveshare ESP32-S3-RGB-Matrix с панелью HUB75 128x64, другие платы я не проверял. Он в основном о том, что умеют Lua-эффекты и как быстро.

Новое для эффектов:
- `px.fade` и `px.blur`. `px.fade` одним вызовом тянет весь экран или его часть к цвету: следы, дым, гаснущее небо. `px.blur` разносит свет на соседей, как blur2d в FastLED. Затухание всего экрана — около 2 мс. Раньше на это уходило больше 100 мс вызовов `px.blend`.
- `px.mode("add")`. Линии, круги, прямоугольники, точки и текст прибавляют свет к тому, что уже есть, и пересечения становятся ярче, как у лазеров и искр.
- Палитры и слои:
  - `px.palette` строит палитру на 256 цветов по опорным цветам или по косинусной формуле Иниго Килеса;
  - `px.layer` хранит по байту на пиксель;
  - `px.show` выводит слой через палитру, и сдвиг смещения каждый кадр — это классический перелив палитры;
  - `px.scroll` и `px.mirror` двигают или складывают весь экран одним вызовом.
- `px.weather()` и `px.city()` дают эффекту данные часов с погодой и домашний город мирового времени.
- `px.blend` и `px.glow` теперь считают в целых числах. FPU платы не умеет двойную точность, поэтому раньше они считались программно: `px.blend` стал вдвое быстрее, `px.glow` — примерно в 24 раза. Пиксели могут отличаться от прежних на один-два уровня из 255.

Надёжнее:
- Загруженный скрипт мог подвесить задачу эффектов тремя способами, все три закрыты:
  - линия к координате вроде `math.mininteger`;
  - библиотечные вызовы, которые вызывают Lua обратно, вложенные так глубоко, что выходили за стек задачи;
  - финализатор `__gc`, который Lua выполняет вне бюджета инструкций.
- Теперь такие вызовы вкладываются не глубже 2 уровней, а метатаблица с `__gc` отклоняется с понятным сообщением. Ни один скрипт галереи этого не делает.

Новое и быстрее в галерее:
- LASER CLOCK: лазерный проектор на тротуаре пишет на стене дома. Каждые 5 секунд он показывает время, день недели, дату, температуру на улице и Канны.
  - Каждая надпись пишется штрих за штрихом, между штрихами луч гаснет, затем проектор сканирует её, как настоящий.
  - RGB-лазер меняет цвет с каждым экраном, кнопка тоже меняет цвет.
  - День недели и Канны — по-русски.
- CANNES теперь гасит небо через `px.fade`: на панели 15 кадров/с вместо 8.

Установка:
- Для новой платы — веб-прошивальщик https://nickoscope.github.io/AnimatedPixelClock/ или запись firmware-v2.7.4-waveshare.bin по адресу 0x0.
- Для уже работающей — загрузить OTA_ONLY_firmware-v2.7.4-waveshare.bin на странице обновления прошивки в портале или через инструменты из tools/agent. Полный образ как обновление не загружать.
- Компаньон для Windows — pc_stats_monitor_v4.exe. Контрольные суммы в SHA256SUMS.txt.
