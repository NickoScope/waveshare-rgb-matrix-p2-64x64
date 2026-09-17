# Draft: upstream PR 2 to Keralots/AnimatedPixelClock, skip removing settings keys that do not exist

**Status: NOT POSTED.** Written 2026-09-17 at the owner's "готовь", after Rafał asked for this one
on issue #3 ("The settings bug is different, this one please send",
https://github.com/Keralots/AnimatedPixelClock/issues/3#issuecomment-5716011106). Goes nowhere until
the owner says "отправляй".

## What is ready

- Branch `fix/settings-skip-absent-keys` (pushed to the fork, not proposed),, made from `upstream/main` at `a091505` (PR #4 merged).
- One commit on it, `02138de`: `fix(settings): skip removing label and name keys that do not exist`.
- One file, `src/config/settings.cpp`: the two `else` branches that removed empty metric labels
  and names become `else if (preferences.isKey(key.c_str()))`. Nothing else.
- Worktree: `/Users/apple/AnimatedPixelClock-settings-fix`.

## His rules, checked

| Rule | This PR |
|---|---|
| One PR per change, off `main` | one change, branch from `upstream/main` a091505 |
| Conventional Commits | `fix(settings): ...` |
| No `FIRMWARE_VERSION` bump or release notes | none |
| Keep the existing formatting | his `else` / comment kept; 4-space indent inside the loop as in the file |
| README only if user setup is needed | no setup, README untouched |
| All three envs build | `matrix-s3`, `matrix-s3-wroom`, `matrix-waveshare`: SUCCESS, sizes below |
| `matrix-s3` size in the description | yes, before and after |
| No build flag, on by default | no flag |

## Figures used, and where they come from

| Figure | Source |
|---|---|
| The two calls at `settings.cpp:889` and `:899`, `MAX_METRICS 20` | upstream `a091505`, `src/config/settings.cpp` 883-901 and `src/config/config.h:19`; Rafał confirmed the same lines himself |
| `[E][Preferences.cpp:96] remove(): nvs_erase_key fail: label0 NOT_FOUND` | panel serial log 2026-09-15 21:50:06, `~/panel-backups/2026-09-15-monitor/serial.log` (private, not in git) |
| 40 failed erases per save, `label0..19` and `name0..19`, 26-27 ms apart, 1,047 ms first to last | the same log, the 40 error lines before "Settings saved (v2.0) in 1109 ms" |
| 13 saves at 1,107-1,109 ms before, 54 saves after: 51 at 47-54 ms, 3 at 144-150 ms | every "Settings saved (v2.0) in N ms" line in the same log. **The timing line exists only in the fork's build**; upstream prints "Settings saved (v2.0)!" |
| The same fix in the fork | fork commit `f79fe99` (written as `if (isKey) remove` inside the `else`), on the Waveshare panel since 2026-09-15 |
| Build sizes | `pio run` on a091505 and on the branch, 2026-09-17, espressif32@6.12.0 |

## English (to post)

Title:

```text
fix(settings): skip removing label and name keys that do not exist
```

Body:

```text
This is the settings bug from #3.

What it does: in saveSettings(), the loops for the metric labels and names removed the key whenever the label or name was empty. Now they check preferences.isKey() first, so only a key that exists is removed. Two lines in src/config/settings.cpp, the ones you found at 889 and 899. Nothing else changes: a set label is still written with putString(), and an empty label whose key exists is still removed as before. No flag, no setting.

Why: with MAX_METRICS at 20, every save tried to erase label0..19 and name0..19 whenever they were empty, which on a config without custom labels is all 40. Each missing key is a failed nvs_erase_key and an error line on serial:

[E][Preferences.cpp:96] remove(): nvs_erase_key fail: label0 NOT_FOUND

What it cost on my board: on the Waveshare panel those 40 failed erases came 26-27 ms apart, 1,047 ms from the first to the last, and loop() waits for the whole save, so the display froze for about a second every time the portal saved. My fork prints how long saveSettings() takes (your tree doesn't have that line): 13 saves before the change took 1,107-1,109 ms. After it, 51 of 54 saves took 47-54 ms and three took 144-150 ms; I haven't looked into those three.

Builds, espressif32@6.12.0, upstream main a091505 before, this branch after:

matrix-s3: Flash 1,624,481 -> 1,624,529 bytes (+48), 82.6% of 1,966,080 before and after. RAM 89,220 bytes, unchanged.
matrix-s3-wroom: Flash 1,639,361 -> 1,639,405 bytes (+44), 25.0%. RAM 89,352 bytes, unchanged.
matrix-waveshare: Flash 1,627,353 -> 1,627,349 bytes (-4), 34.5%. RAM 89,484 bytes, unchanged.

How it was tested: on this branch, only the three builds above. I haven't flashed this branch to any board. The same fix, written as an if inside the else, has been running in my fork on the Waveshare board since 15 September, and the numbers above come from there. Not tested: any of your three boards.

Nikolay
```

## Русский (для чтения, не публикуется)

```text
Заголовок: fix(settings): не удалять ключи подписей и имён, которых нет

Это тот баг с настройками из #3.

Что делает: в saveSettings() циклы для подписей и имён метрик удаляли ключ всякий раз, когда подпись или имя пустые. Теперь они сначала вызывают preferences.isKey(), и удаляется только существующий ключ. Две строки в src/config/settings.cpp — те самые, что ты нашёл на 889 и 899. Больше ничего не меняется: заданная подпись по-прежнему пишется через putString(), а пустая подпись, у которой ключ есть, удаляется как раньше. Ни флага, ни настройки.

Зачем: при MAX_METRICS = 20 каждое сохранение пыталось стереть label0..19 и name0..19, если они пустые, — а в конфигурации без своих подписей это все 40. Каждый отсутствующий ключ — это неудачный nvs_erase_key и строка ошибки в порту:

[E][Preferences.cpp:96] remove(): nvs_erase_key fail: label0 NOT_FOUND

Во что это обходилось на моей плате: на панели Waveshare эти 40 неудачных стираний шли с шагом 26–27 мс, 1047 мс от первого до последнего, а loop() ждёт всё сохранение целиком, так что экран замирал примерно на секунду при каждом сохранении из портала. Мой форк печатает, сколько длится saveSettings() (в твоём дереве этой строки нет): 13 сохранений до правки заняли 1107–1109 мс. После неё 51 из 54 сохранений заняли 47–54 мс, а три — 144–150 мс; эти три я не разбирал.

Сборки, espressif32@6.12.0, до — upstream main a091505, после — эта ветка:

matrix-s3: флеш 1 624 481 -> 1 624 529 байт (+48), 82,6 % от 1 966 080 до и после. RAM 89 220 байт, без изменений.
matrix-s3-wroom: флеш 1 639 361 -> 1 639 405 байт (+44), 25,0 %. RAM 89 352 байта, без изменений.
matrix-waveshare: флеш 1 627 353 -> 1 627 349 байт (−4), 34,5 %. RAM 89 484 байта, без изменений.

Как проверено: на этой ветке — только три сборки выше. Эту ветку я ни на одну плату не прошивал. Та же правка, записанная как if внутри else, работает в моём форке на плате Waveshare с 15 сентября, цифры выше оттуда. Не проверено: ни одна из твоих трёх плат.

Николай
```
