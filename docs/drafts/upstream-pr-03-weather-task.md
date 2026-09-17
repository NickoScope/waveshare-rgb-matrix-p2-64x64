# Draft: upstream PR 3 to Keralots/AnimatedPixelClock, the weather fetch in a task that deletes itself

**Status: POSTED 2026-09-17 18:17** on the owner's "да": https://github.com/Keralots/AnimatedPixelClock/pull/6 - head `NickoScope:fix/weather-fetch-task` at `7a76883` onto upstream main `bbb861c`. Audit APPROVED 17:44, six LOW findings taken before posting. Not bench-tested on the panel, by the owner's choice. Written 2026-09-17 at the owner's "давай следующий", the next item in
Rafał's order (issue #3: "the weather task lifetime ... the one I am waiting for next",
https://github.com/Keralots/AnimatedPixelClock/issues/3#issuecomment-5716011106). Waiting for the
owner's "отправляй".

## What he agreed to, and what he did not

From his first answer on #3 (docs/09, item 2): **yes to the task half** - a task per fetch with
`vTaskDelete`, instead of the 8 KB task kept forever at `weather.cpp:160`; **no to on-screen
gating** - his looser `weatherOnScreen()` prefetches on purpose, and a cycle slot can be 5 s. So
this PR changes when the task lives and nothing about when a fetch happens.

## What is ready

- Branch `fix/weather-fetch-task` (pushed to the fork, not proposed), from `upstream/main` at
  `bbb861c` - which already contains PR #5, merged 2026-09-17 15:30 UTC.
- One commit, `7a76883`: `perf(weather): run each fetch in a task that deletes itself`.
- Files: `src/weather/weather.cpp`, `src/weather/weather.h`, `src/main.cpp`, `src/web/web.cpp`
  (a comment). +55 -32.
- Worktree: `/Users/apple/AnimatedPixelClock-weather-task`.

**Not carried over from the fork's `6e91d54`:** the stricter on-screen gating (he said no), the
network lock and `netLockBusy()` (not in his tree), the largest-free-block check before creating
the task, priority 0 (his is 1), and the deadline comparison `(long)(now - nextFetchMs) < 0` - a
signed difference against a deadline, the same class of bug the IR audit found on 2026-09-16. The
PR compares elapsed time instead. **The fork itself still has that comparison: a debt to fix there.**

## His rules, checked

| Rule | This PR |
|---|---|
| One PR per change, off `main` | one change, branch from `upstream/main` bbb861c |
| Conventional Commits | `perf(weather): ...` |
| No `FIRMWARE_VERSION` bump or release notes | none |
| Keep the existing formatting | his header comment style, `#define` constants, 2-space indent |
| README only if user setup is needed | no setup, README untouched |
| All three envs build | `matrix-s3`, `matrix-s3-wroom`, `matrix-waveshare`: SUCCESS |
| `matrix-s3` size in the description | yes, before and after |
| No build flag, on by default | no flag |

## Figures used, and where they come from

| Figure | Source |
|---|---|
| The task at `weather.cpp:160`, 8192 bytes, priority 1, core 0, created in `setup()` at `main.cpp:294` before the 5 s IP screen | upstream `bbb861c` |
| Unchanged: 10 min after success, 1 min after failure, 5 s check, settings change ends the wait | `WEATHER_FETCH_INTERVAL_MS`, `WEATHER_RETRY_INTERVAL_MS`, `WEATHER_IDLE_POLL_MS`, `xTaskNotifyGive` in upstream `bbb861c` |
| Eight scenarios; every wait, compared one by one, ends 0-8 ms later than the old task's (within one 16 ms loop() pass) and never earlier; a wait cut short by a settings change ends within one pass of it. Absolute drift adds up: 32 ms over four 10-minute waits, 1,176 ms over 148 5-second checks | `docs/drafts/upstream-pr-03-weather-sched-model.py`, criterion tightened after the audit, run 2026-09-17 |
| The model caught two mistakes in the first version: fetches drifting up to 5 s later each cycle (21.7 s after 40 min), and the conditions re-checked on every loop() pass after a settings change while nothing showed the weather | the same model, first run |
| Builds | `pio run` on bbb861c and 7a76883 in the same directory, 2026-09-17, espressif32@6.12.0. The audit found sizes shift by up to 16 bytes with the build directory (its clean copy gave matrix-waveshare 1,627,349 before, this worktree 1,627,333) |
| Fork: free internal heap a minute after boot ~30 KB before, 38.5 KB after a task per fetch | fork commit `6e91d54`, Waveshare panel, 2026-09-14 |
| Indoor temperature and humidity on the weather clock | fork `src/clocks/weather_layout.h` (design B "outside | inside": temperature to one decimal, humidity in whole percent), docs/21; preview render `tools/climate/preview/b_split_live.png` on `feature/market-climate-audio` |

## English (to post)

Title:

```text
perf(weather): run each fetch in a task that deletes itself
```

Body:

```text
This is the weather task half from #3, without the on-screen gating.

What it does: the weather task was created once in setup() and kept its 8KB stack in internal SRAM for good, sleeping ten minutes between fetches. Now loop() calls weatherLoop(), which starts a task for one fetch when a fetch is due, and the task deletes itself when it's done. startWeatherTask() is gone; weatherSettingsChanged() keeps its name and what it does.

What stays the same: everything that decides when to fetch. weatherConfigured(), your weatherOnScreen() and the Wi-Fi check are untouched, and so are the 10 minutes after a successful fetch, the 1 minute after a failed one, the 5 second check while nothing can show the weather, and a settings change ending the wait. The stack size, the core and the priority are the same too.

A few differences you should know about. The waits are measured as elapsed millis() instead of FreeRTOS timeouts, written so the millis() rollover doesn't matter. If the task can't be created, it prints that and tries again a minute later; before, a failed create meant no weather until reboot. The old task started in setup(), before the 5 second IP screen, so the first fetch could begin during that delay; now the first check happens on the first loop() pass, after it. And the check now runs in loop(), so if loop() is stuck for a while, a fetch that is due waits until loop() moves again. The old task didn't depend on loop().

How I checked the timing: I wrote a small model of both schedulers and ran eight scenarios through it - always on screen, off and on again, a settings change during the wait, during a fetch and while nothing shows the weather, two failed fetches in a row, and the millis() rollover. Every wait ends at most one loop() pass later than the old task's, never earlier. Over many waits that adds up a little: about a second over twelve minutes of 5 second checks. The model caught two mistakes in my first version, both fixed before this commit.

Builds, espressif32@6.12.0, upstream main bbb861c before, this branch after:

matrix-s3: Flash 1,624,529 -> 1,624,729 bytes (+200), 82.6% of 1,966,080 before and after. RAM 89,220 -> 89,228 bytes (+8).
matrix-s3-wroom: Flash 1,639,405 -> 1,639,617 bytes (+212), 25.0%. RAM 89,352 -> 89,360 bytes (+8).
matrix-waveshare: Flash 1,627,333 -> 1,627,533 bytes (+200), 34.5%. RAM 89,484 -> 89,492 bytes (+8).

Before and after were built in the same directory; built somewhere else, the same commit can come out up to 16 bytes different. The RAM line is static data only. The 8KB stack is taken from the heap at run time, so these numbers don't show it.

How it was tested: on this branch, only the three builds and the model. I haven't flashed this branch to any board. The same idea, a task per fetch that deletes itself, has been running in my fork on the Waveshare board since 14 September. There, free internal heap a minute after boot went from about 30KB to 38.5KB. My fork runs a lot more than yours, so take that as the size of the effect, not a number for your builds. Not tested: any of your three boards, and a weather fetch on this tree.

One more thing, just so you know, nothing to send: in my fork the weather clock now also shows the indoor temperature and humidity from the board's own SHTC3, next to the outdoor weather. It looks really nice, and the onboard sensor finally does something. A preview render of the screen:
https://github.com/NickoScope/AnimatedPixelClock/blob/feature/market-climate-audio/tools/climate/preview/b_split_live.png

Nikolay
```

## Русский (для чтения, не публикуется)

```text
Заголовок: perf(weather): каждый запрос погоды — в задаче, которая удаляет себя сама

Это та половина про задачу погоды из #3, без логики «видно ли на экране».

Что делает: задача погоды создавалась один раз в setup() и навсегда держала свой стек 8 КБ во внутренней памяти, между запросами просто спала по десять минут. Теперь loop() вызывает weatherLoop(), которая запускает задачу на один запрос, когда пора, а задача, закончив, удаляет себя. startWeatherTask() больше нет; weatherSettingsChanged() осталась с тем же именем и тем же смыслом.

Что не меняется: всё, что решает, когда запрашивать. weatherConfigured(), твоя weatherOnScreen() и проверка Wi-Fi не тронуты, как и 10 минут после удачного запроса, 1 минута после неудачного, проверка раз в 5 секунд, пока погоду негде показать, и то, что смена настроек обрывает ожидание. Размер стека, ядро и приоритет тоже прежние.

Несколько отличий, о которых стоит знать. Ожидание считается как прошедшее время по millis(), а не таймаутами FreeRTOS, и написано так, что переполнение millis() не мешает. Если задачу не удалось создать, это печатается в порт, и через минуту будет новая попытка; раньше неудачное создание означало «погоды нет до перезагрузки». Старая задача стартовала в setup(), до 5-секундного экрана с IP, так что первый запрос мог начаться во время этой паузы; теперь первая проверка — на первом проходе loop(), уже после неё. И проверка теперь живёт в loop(), так что если loop() на время завис, назревший запрос ждёт, пока он пойдёт дальше. Старая задача от loop() не зависела.

Как я проверил время запросов: написал небольшую модель обоих планировщиков и прогнал через неё восемь сценариев — погода всё время на экране, пропала и вернулась, смена настроек во время ожидания, во время запроса и когда погоду негде показать, два неудачных запроса подряд и переполнение millis(). Каждое ожидание заканчивается не больше чем на один проход loop() позже, чем у старой задачи, и никогда не раньше. На многих ожиданиях это немного накапливается: примерно секунда за двенадцать минут 5-секундных проверок. Модель поймала две ошибки в моей первой версии, обе исправлены до этого коммита.

Сборки, espressif32@6.12.0, до — upstream main bbb861c, после — эта ветка:

matrix-s3: флеш 1 624 529 -> 1 624 729 байт (+200), 82,6 % от 1 966 080 до и после. RAM 89 220 -> 89 228 байт (+8).
matrix-s3-wroom: флеш 1 639 405 -> 1 639 617 байт (+212), 25,0 %. RAM 89 352 -> 89 360 байт (+8).
matrix-waveshare: флеш 1 627 333 -> 1 627 533 байта (+200), 34,5 %. RAM 89 484 -> 89 492 байта (+8).

«До» и «после» собраны в одном каталоге; в другом каталоге тот же коммит может выйти на 16 байт иным. Строка RAM — только статические данные. Стек 8 КБ берётся из кучи во время работы, поэтому в этих цифрах его не видно.

Как проверено: на этой ветке — только три сборки и модель. Эту ветку я ни на одну плату не прошивал. Та же идея, задача на один запрос, которая удаляет себя, работает в моём форке на плате Waveshare с 14 сентября. Там свободная внутренняя куча через минуту после загрузки выросла примерно с 30 КБ до 38,5 КБ. Мой форк делает куда больше твоего, так что это порядок эффекта, а не цифра для твоих сборок. Не проверено: ни одна из твоих трёх плат и запрос погоды на этом дереве.

И ещё, просто чтобы ты знал, ничего не предлагаю: в моём форке часы с погодой теперь показывают ещё и температуру и влажность в комнате с бортового SHTC3, рядом с уличной погодой. Выглядит очень приятно, и бортовой датчик наконец при деле. Превью экрана:
https://github.com/NickoScope/AnimatedPixelClock/blob/feature/market-climate-audio/tools/climate/preview/b_split_live.png

Николай
```
