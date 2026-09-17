# Draft: upstream PR 5 to Keralots/AnimatedPixelClock, keep the crash cause name across an update

**Status: POSTED 2026-09-17 20:53** on the owner's "отправляй": https://github.com/Keralots/AnimatedPixelClock/pull/8 - head `NickoScope:fix/crash-cause-name` at `3889b79` onto upstream main `eb43f15`, 1 file, +27 -10. **Merged 19:03 UTC as `517b37d`**, no review comments. The body ends with the Claude Code attribution line.  Audit 20:43: APPROVED**, three LOWs - the `case` indentation taken (`3889b79`), the note about the dropped record already in the text, the `resetReason` tail case parked. Written 2026-09-17 at the owner's "сделай", after PR #7 was
merged (18:27 UTC as `eb43f15`) and the hardware test found what the audit had predicted.

## Why there is a fifth PR

The audit of #7 raised this as a MINOR and it was parked. Then the panel showed it: the module was
put into the fork byte for byte, a build with a deliberate `abort()` crashed, the report read
`abort()` - and after the next build was flashed the same record read `StoreProhibited` at address
0 again. That is the one moment the name matters: you crash, you flash a build with the fix, you
open `/api/info` to see what the old crash was.

The cause: `crashName()` compared `pc` with `panic_abort()` when the JSON was built. That holds
only while the crashed image is the one running; the next build moves the function
(`0x40377ac8` in one build, `0x40377148` in the next, both matrix-s3).

## What is ready

- Branch `fix/crash-cause-name` (pushed to the fork, not proposed), from `upstream/main` at
  `eb43f15`, which is PR #7 merged.
- One commit, `3889b79`: `fix(diagnostics): keep the crash cause name across a firmware update`.
- One file, `src/utils/crash_report.cpp`, +27 -10: `CrashRecord` gains `uint8_t kind`,
  `CRASH_MAGIC` is bumped so a record written by #7 is ignored instead of read wrong,
  `crashKind()` decides once in `crashReportBegin()`, `crashName()` becomes a switch.
- Worktree: `/Users/apple/AnimatedPixelClock-cause-name`.
- The same file, byte for byte, is in the fork (`459c0b7`) and running on the panel.

## His rules, checked

| Rule | This PR |
|---|---|
| One PR per change, off `main` | one change, branch from `upstream/main` eb43f15 |
| Conventional Commits | `fix(diagnostics): ...` |
| No `FIRMWARE_VERSION` bump or release notes | none |
| Keep the existing formatting | the file's own style, unchanged |
| README only if user setup is needed | no setup, README untouched |
| All three envs build | `matrix-s3`, `matrix-s3-wroom`, `matrix-waveshare`: SUCCESS, no warnings |
| `matrix-s3` size in the description | yes, before and after |
| No build flag, on by default | no flag |

## Figures and facts used, and where they come from

| Figure / fact | Source |
|---|---|
| `panic_abort()` moves between builds: 0x40377ac8 and 0x40377148 on matrix-s3 | `xtensa-esp32s3-elf-nm -S firmware.elf` on 7022c15 and 52f1879 |
| Serial line from the real crash: task loopTask, abort(), pc 0x40377886, addr 0, ELF 458f86d0c9eb2166 | panel serial, 2026-09-17 20:33, fork selftest build |
| The five backtrace addresses resolve to `panic_abort` (panic.c:408), `esp_system_abort` (esp_system.c:137), `abort` (abort.c:46), `loop()` (main.cpp:1330), `loopTask` | `xtensa-esp32s3-elf-addr2line -pfiaC` with `~/AnimatedPixelClock-elf/15b5e3e4f4d29b7e-crash-selftest.elf` |
| Before the fix, after flashing the next build: `causeName` StoreProhibited, `sameFirmware` false | panel `/api/info`, 2026-09-17 20:26 |
| After the fix, same situation: `causeName` abort(), `sameFirmware` false, `resetReason` 4, `bootTime` set | panel `/api/info`, 2026-09-17 20:35 |
| Builds | `pio run` on eb43f15 and 3889b79 in the same directory, 2026-09-17, espressif32@6.12.0. The audit's own clean copy differed by ±16 bytes of Flash, RAM to the byte |
| The record grows 124 -> 128 bytes, so an old one is rejected by its length before the magic is even read | audit of 3889b79, measured with the same toolchain |

## English (to post)

Title:

```text
fix(diagnostics): keep the crash cause name across a firmware update
```

Body:

```text
A follow-up to #7, found by running it on a board.

The bug: the cause name was worked out when /api/info was built. That comparison only holds while the crashed image is still the one running, because panic_abort() sits at a different address in the next build. So after an update sameFirmware goes false and an abort() reads as StoreProhibited at address 0 again - exactly the moment it matters. You crash, you flash a build with the fix, you open /api/info to see what the old crash was, and the name is gone.

The fix: decide it once, when the dump is found and panic_abort() is still where the crashed image had it, and keep it in the record as one byte. crashName() is then a switch on that byte. The record's magic is bumped, so a record written by the version you just merged is ignored instead of read wrong: on a board that already holds one crash, that one record is dropped, and nothing else changes.

How I tested it, on hardware this time. The board is a Waveshare ESP32-S3-RGB-Matrix, the same target as your matrix-waveshare env. I put the module from #7 into my fork on that board, this file byte for byte, built an image that calls abort() on purpose in loop(), and let it crash:

Crash report: the last run crashed in task loopTask, abort(), pc 0x40377886, addr 0x00000000, ELF 458f86d0c9eb2166

/api/info then had causeName "abort()", sameFirmware true, resetReason 4 and five backtrace addresses, which addr2line resolved to panic_abort, esp_system_abort, abort, loop() and loopTask - the deliberate abort, four frames down. Then I flashed the next build. Before this fix that same record read StoreProhibited at address 0; with it, it still reads abort(), with sameFirmware false. So the checksum check, the summary, the NVS record, the erase and the naming are all exercised on a real board now, not only in a build.

Builds, espressif32@6.12.0, main eb43f15 before, this branch after, built in the same directory:

matrix-s3: Flash 1,629,513 -> 1,629,569 bytes (+56), 82.9% of 1,966,080 before and after. RAM 89,608 bytes, unchanged.
matrix-s3-wroom: Flash 1,644,421 -> 1,644,481 bytes (+60), 25.1%. RAM 89,732 bytes, unchanged.
matrix-waveshare: Flash 1,632,337 -> 1,632,393 bytes (+56), 34.6%. RAM 89,864 bytes, unchanged.

What I did not test: a build from your tree on any board. The module ran inside my fork's image, which does a lot more than yours; the file itself is identical. And no watchdog timeout, only abort() - the watchdog path names itself from the reset reason and I have not made loop() hang on purpose.

Nikolay
```

## Русский (для чтения, не публикуется)

```text
Заголовок: fix(diagnostics): сохранять имя причины падения после обновления прошивки

Продолжение #7, нашлось при проверке на плате.

Баг: имя причины вычислялось в момент сборки ответа /api/info. Это сравнение верно только пока упавший образ — тот же, что работает сейчас, ведь в следующей сборке panic_abort() лежит по другому адресу. Поэтому после обновления sameFirmware становится false, и abort() снова выглядит как StoreProhibited по адресу 0 — ровно тогда, когда это важно. Упало, прошил сборку с исправлением, открыл /api/info посмотреть, что было, — а имени нет.

Исправление: решать один раз, когда дамп найден и panic_abort() ещё там, где он был у упавшего образа, и хранить результат в записи одним байтом. crashName() после этого — просто switch. Магия записи поднята, поэтому запись, сделанная только что смерженной версией, игнорируется, а не читается неверно: на плате, где уже лежит одно падение, эта запись пропадёт, и больше ничего.

Как проверено, на этот раз на железе. Плата — Waveshare ESP32-S3-RGB-Matrix, та же, что твоё окружение matrix-waveshare. Я положил модуль из #7 в свой форк на этой плате, этот файл побайтово, собрал образ, который нарочно вызывает abort() в loop(), и дал ему упасть. В порт пришло:

Crash report: the last run crashed in task loopTask, abort(), pc 0x40377886, addr 0x00000000, ELF 458f86d0c9eb2166

В /api/info было causeName "abort()", sameFirmware true, resetReason 4 и пять адресов трассы, которые addr2line разложил в panic_abort, esp_system_abort, abort, loop() и loopTask — тот самый намеренный abort, четырьмя кадрами ниже. Потом я прошил следующую сборку. До этой правки та же запись читалась как StoreProhibited по адресу 0; с правкой она по-прежнему abort(), при sameFirmware false. То есть проверка контрольной суммы, чтение сводки, запись в NVS, стирание дампа и имя причины теперь проверены на настоящей плате, а не только сборкой.

Сборки, espressif32@6.12.0, до — main eb43f15, после — эта ветка, в одном каталоге:

matrix-s3: флеш 1 629 513 -> 1 629 569 байт (+56), 82,9 % от 1 966 080 до и после. RAM 89 608 байт, без изменений.
matrix-s3-wroom: флеш 1 644 421 -> 1 644 481 байт (+60), 25,1 %. RAM 89 732 байта, без изменений.
matrix-waveshare: флеш 1 632 337 -> 1 632 393 байта (+56), 34,6 %. RAM 89 864 байта, без изменений.

Чего я не проверял: сборку из твоего дерева ни на одной плате. Модуль работал внутри образа моего форка, который делает куда больше твоего; сам файл идентичен. И не проверял сторожевой таймер, только abort(): путь сторожевого таймера называет себя по причине перезагрузки, а зависание loop() я нарочно не устраивал.

Николай
```
