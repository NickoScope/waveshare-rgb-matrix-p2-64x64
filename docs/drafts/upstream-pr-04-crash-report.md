# Draft: upstream PR 4 to Keralots/AnimatedPixelClock, the last crash in /api/info

**Status: POSTED 2026-09-17 19:52** on the owner's "отправляй": https://github.com/Keralots/AnimatedPixelClock/pull/7 - head `NickoScope:feat/crash-report` at `52f1879` onto upstream main `9fa9ba4`, 4 files, +263 -0, mergeable. The body ends with the Claude Code attribution line, as #4, #5 and #6 did. First audit 19:38: CHANGES-REQUIRED, one MAJOR - abort() and the task watchdog read as StoreProhibited at 0, and the watchdog's task is the interrupted one. Fixed in `52f1879` together with four LOWs. **Re-audit 19:44: APPROVED** (code quality; not tested on hardware). Written 2026-09-17 at the owner's "делаем?", the next item in
Rafał's order (issue #3: "the crash report half of 4",
https://github.com/Keralots/AnimatedPixelClock/issues/3#issuecomment-5682483397). Goes nowhere until
the owner says "отправляй".

## What he agreed to, and what he did not

From his first answer on #3, item 4: **crash report yes, rollback no.** His words: the core dump
summary in `/api/info` "is exactly the tool we lack; serial on the deployed clock is unreliable".
The rollback half he declined: confirming on `WL_CONNECTED` would roll back a healthy image when the
Wi-Fi credentials change, and it does not cover his USB full image. So this PR has no rollback code:
no `verifyRollbackLater()`, no `esp_ota_mark_app_valid_cancel_rollback()`, no `"ota"` object.

## What is ready

- Branch `feat/crash-report` (pushed to the fork, not proposed), from `upstream/main` at `9fa9ba4`,
  which already has PR #5 and PR #6.
- One commit, `52f1879` (amended from `7022c15` after the audit): `feat(diagnostics): report the last crash in /api/info`.
- Files: new `src/utils/crash_report.h` and `src/utils/crash_report.cpp`; `src/main.cpp` (include,
  `crashReportBegin()` after `Serial.begin`, `crashReportLoop()` after `weatherLoop()`);
  `src/web/web.cpp` (include, `crashReportToJson(doc)` after `resetReason`). +263 -0.
- Worktree: `/Users/apple/AnimatedPixelClock-crash-report`.

**Changed from the fork's `8ec3045`:**
- the rollback is gone;
- `esp_core_dump_image_check()` runs before the summary is read, and a damaged dump is erased
  instead of parsed;
- pseudo causes get names, the interrupt watchdog among them;
- up to 16 backtrace addresses instead of 8;
- `bootTime` (when the boot that found the crash started) instead of `seenUtc`;
- an `abort()` and the task watchdog are named as such when the crash came from the running image, and `sameFirmware` says whether it did;
- the dump is erased only after the record is saved to NVS, and kept when the summary cannot be read;
- `isKey()` before reading NVS;
- the NVS namespace is `crash` instead of `health`.

**Fork debts found while porting:**
- the fork reads the summary without the checksum check;
- the fork names an interrupt watchdog "other";
- the fork calls `getBytesLength()` without `isKey()`, which logs an error when the key is missing.

## Left on the backlog, not in this PR

Both from the audits, neither gating:

- **[MINOR] The cause is named when the JSON is built, not when the crash is found.** After an OTA
  or a reflash `sameFirmware` goes false, so a stored `abort()` or `Task watchdog` shows as
  `StoreProhibited` at address 0 again - exactly when the maintainer has just updated to a fix and
  looks at `/api/info`. Fix: classify once in `crashReportBegin()`, keep the result in the record,
  bump `CRASH_MAGIC`. Frozen because the branch is audited and the addresses of an older image
  cannot be decoded with the new ELF anyway, and `sameFirmware` says so.
- **[LOW] `resetReason` belongs to the boot that found the dump.** If the NVS save fails, the dump
  stays and the next boot stores its own reset reason for the same crash, which can turn a
  `Task watchdog` into `abort()`. Tail case.
- **Keeping the full dump** (deduplicate by its CRC instead of erasing) - worth it only if someone
  reads dumps with `espcoredump`, which needs the board on a desk.

**Not tested on hardware.** The auditor asks for a run with a panic, an `abort()` and a `loop()`
hang over 15 s, then `/api/info`. That needs the panel flashed with an upstream build, which is the
owner's call: the panel currently runs the fork.

## His rules, checked

| Rule | This PR |
|---|---|
| One PR per change, off `main` | one change, branch from `upstream/main` 9fa9ba4 |
| Conventional Commits | `feat(diagnostics): ...` |
| No `FIRMWARE_VERSION` bump or release notes | none |
| Keep the existing formatting | his file header comments, `#define` constants, 2-space indent, the 1-space indent inside `handleDeviceInfo()` |
| README only if user setup is needed | no setup, README untouched |
| All three envs build | `matrix-s3`, `matrix-s3-wroom`, `matrix-waveshare`: SUCCESS, no warnings from the new files |
| `matrix-s3` size in the description | yes, before and after |
| No build flag, on by default | no flag |

## Figures and facts used, and where they come from

| Figure / fact | Source |
|---|---|
| Rafał's words on item 4 | issue #3 comment 5682483397 |
| Core dump to flash, ELF, CRC32, check at boot, enabled for all three envs | `CONFIG_ESP_COREDUMP_*` in the SDK's `qio_qspi`, `qio_opi`, `opi_opi` `sdkconfig.h` (arduino-esp32 2.0.17), the memory types of matrix-s3 (default), matrix-s3-wroom and matrix-waveshare in `platformio.ini` |
| A 64K coredump partition in all three tables | `min_spiffs.csv`, `default_16MB.csv`, `large_littlefs_32MB.csv`, the `board_build.partitions` of the three envs |
| `esp_core_dump_get_summary()` parses the ELF without a checksum; `esp_core_dump_image_check()` does the CRC | ESP-IDF v4.4.7 `components/espcoredump/src/core_dump_elf.c` 709-776, `core_dump_flash.c` 361-433 |
| A blank partition makes `esp_core_dump_image_get()` fail with only a debug log, and the SDK log level is 1 | `core_dump_flash.c` 504-507; `CONFIG_LOG_MAXIMUM_LEVEL 1` in the same sdkconfigs |
| `esp_core_dump_image_erase()` erases the partition and writes a blank size | `core_dump_flash.c` 437-470 |
| Cause names | `panic_arch.c` 367-378 (exceptions) and 411-420 (pseudo causes), v4.4.7 |
| A pseudo cause is stored as 64 + `PANIC_RSN_*` | `components/espcoredump/src/port/xtensa/core_dump_port.c` 250-262, `XCHAL_EXCCAUSE_NUM 64` in the SDK's `xtensa/config/core.h`, `PANIC_RSN_*` in `esp_private/panic_reason.h` |
| `abort()` writes to address 0 | `components/esp_system/panic.c` 394-409, `panic_abort()` |
| Reset reasons: 4 panic, 5 interrupt watchdog, 6 task watchdog; the task watchdog sets its hint and aborts | `esp_system.h` enum; `panic.c` 367-380; `task_wdt.c` 175-176; his portal names the same numbers (`web_pages.h`, `var reset`) |
| His task watchdog panics | `esp_task_wdt_init(15, true)`, `main.cpp:281` at 9fa9ba4 |
| The SHA in the dump is the SHA-256 of `firmware.elf` | built matrix-s3 at 9fa9ba4: `shasum -a 256 firmware.elf` equals the 32 bytes at 0xb0 of `firmware.bin`; `--elf-sha256-offset 0xb0` in the espressif32 builder |
| `getBytesLength()` of a missing key logs `log_e`; `isKey()` does not | arduino-esp32 2.0.17 `libraries/Preferences/src/Preferences.cpp` 305-327, 496-507 |
| ArduinoJson 7.4.3 copies `char[]` and `const char*` | `.pio/libdeps/matrix-s3/ArduinoJson/src/ArduinoJson/Strings/Adapters/RamString.hpp` 69-107 |
| His upload checks free space before writing | `web.cpp` 558-572 at 9fa9ba4 |
| The fork's crash report in use since 14 September | fork commit `8ec3045`, 2026-09-14 23:47 |
| The deliberate abort read as `StoreProhibited` at 0 with `pc` in `panic_abort` | docs/03-firmware.md, "Crash reports" (the rollback test image, 2026-09-14) |
| `IntegerDivideByZero` in `lfs_alloc`, called from `lfs_file_write`, when an 87,260-byte record did not fit on a LittleFS with 12,288 bytes free | docs/18-stock-dashboard.md, incident 2026-09-15 16:31-16:53 |
| `panic_abort()` is 26 bytes and its address changes between builds | `xtensa-esp32s3-elf-nm -S firmware.elf`: 0x1a in all three envs; 0x40377ac8 in 7022c15 and 0x40377148 in 52f1879 (matrix-s3) |
| The task watchdog aborts from its interrupt, so the dump's task is the interrupted one | `task_wdt.c` 172-176, v4.4.7; first audit of 7022c15 |
| Builds | `pio run` on 9fa9ba4 and 52f1879 in the same directory, 2026-09-17, espressif32@6.12.0. The matrix-waveshare "before" came out 16 bytes different from the same commit in the PR 3 worktree (1,627,517 here, 1,627,533 there) |

## English (to post)

Title:

```text
feat(diagnostics): report the last crash in /api/info
```

Body:

```text
This is the crash report half of #3, without the rollback.

What it does: on the S3 the SDK already writes a core dump to the coredump partition when the firmware crashes (a panic, an abort(), the task or interrupt watchdog). All three of your partition tables have that partition. Nothing read it back. Now, at boot, crashReportBegin() checks the dump's checksum, reads its summary, keeps it in NVS and erases the dump, so the same crash isn't reported twice. /api/info then has a "lastCrash" object until the next crash replaces it. /api/diagnostics uses the same handler, so the downloaded diagnostics file has it too. If nothing has crashed, there is no "lastCrash" and nothing on serial.

What's in lastCrash:
- task: the task that crashed
- cause and causeName: the exception cause, with the name ESP-IDF 4.4 prints in the panic output. Watchdog and double exception causes get their names too, and so do abort() and the task watchdog, see below.
- pc and addr: the program counter and the address that faulted
- backtrace: up to 16 addresses, plus backtraceCorrupted when the SDK says the backtrace is corrupted
- elfSha256: the first 16 hex digits of the SHA-256 of the firmware.elf that crashed
- sameFirmware: true if that is the firmware running now
- resetReason: esp_reset_reason() of the boot that found the crash, the same numbers as your resetReason
- bootTime: Unix time when that boot started, added once NTP has synced
- thisBoot: true if the crash was found on this boot

To read one: shasum -a 256 .pio/build/<env>/firmware.elf, and the ELF whose hash starts with elfSha256 is the one to use:
xtensa-esp32s3-elf-addr2line -pfiaC -e firmware.elf <pc> <backtrace addresses>
So it's worth keeping the firmware.elf of every release. Without it, a user's report is just addresses.

A few things you should know:
- In IDF 4.4, abort() writes to address 0 on purpose, so the CPU reports an abort() or a failed assert as StoreProhibited at address 0. When pc is inside panic_abort, causeName says "abort()" instead, and the backtrace shows where it was called from. That check needs the same build, since panic_abort moves between builds, so it only applies when sameFirmware is true.
- Your task watchdog panics (esp_task_wdt_init(15, true)), so a stuck loop() also ends in abort(), and causeName says "Task watchdog" (resetReason 6). The watchdog aborts from its interrupt, though, so task and backtrace belong to whatever the interrupt stopped, not to the task that hung. Which task didn't feed the watchdog is only printed on serial.
- The first boot after flashing this can report an old dump that is still in the partition from older firmware. sameFirmware is false for that one.
- If the firmware crashes on every boot before loop() runs, /api/info never comes up, and only the serial line shows the crash.
- A factory reset doesn't clear lastCrash, it's in its own NVS namespace, "crash". Only the next crash replaces it.
- On a normal boot the cost is a few NVS reads and reading 4 bytes of the partition. The checksum check and the erase only run on the boot after a crash, and the dump is only erased once the summary is saved in NVS.
- I left the Diagnostics panel in the portal alone. It's only in the JSON.

How it was tested: on this branch, only the three builds. I haven't flashed this branch to any board. A simpler version of the same reading has been running in my fork on the Waveshare board since 14 September. It doesn't check the checksum before reading the summary, and it has no names for the watchdog and abort() cases. There it read my deliberate abort() test correctly, and on 15 September it caught a real bug: IntegerDivideByZero in lfs_alloc, called from lfs_file_write, when a record in my fork didn't fit on an almost full LittleFS. Your upload checks free space before it writes, so this is only an example of what the report shows, not a bug report for your tree. Not tested: any of your three boards, and a crash on this tree.

Builds, espressif32@6.12.0, upstream main 9fa9ba4 before, this branch after, built in the same directory:

matrix-s3: Flash 1,624,729 -> 1,629,529 bytes (+4,800), 82.6% -> 82.9% of 1,966,080. RAM 89,228 -> 89,608 bytes (+380).
matrix-s3-wroom: Flash 1,639,617 -> 1,644,421 bytes (+4,804), 25.0% -> 25.1%. RAM 89,360 -> 89,732 bytes (+372).
matrix-waveshare: Flash 1,627,517 -> 1,632,353 bytes (+4,836), 34.5% -> 34.6%. RAM 89,492 -> 89,864 bytes (+372).

Nikolay
```

## Русский (для чтения, не публикуется)

```text
Заголовок: feat(diagnostics): последнее падение в /api/info

Это та половина из #3, которая про отчёт о падении, без отката.

Что делает: на S3 SDK и так пишет core dump в раздел coredump, когда прошивка падает (panic, abort(), сторожевой таймер задач или прерываний). Во всех трёх твоих таблицах разделов этот раздел есть. Обратно его никто не читал. Теперь при загрузке crashReportBegin() проверяет контрольную сумму дампа, читает его сводку, сохраняет её в NVS и стирает дамп, чтобы одно и то же падение не попало в отчёт дважды. В /api/info появляется объект "lastCrash", пока его не заменит следующее падение. /api/diagnostics обслуживает тот же обработчик, так что в скачанном файле диагностики он тоже есть. Если ничего не падало, "lastCrash" нет и в порт ничего не пишется.

Что в lastCrash:
- task: задача, которая упала
- cause и causeName: причина исключения с тем названием, которое ESP-IDF 4.4 печатает при панике. Причины от сторожевого таймера и двойного исключения тоже названы, как и abort() и сторожевой таймер задач, см. ниже.
- pc и addr: счётчик команд и адрес, на котором произошёл сбой
- backtrace: до 16 адресов, и backtraceCorrupted, если SDK считает трассу испорченной
- elfSha256: первые 16 шестнадцатеричных цифр SHA-256 того firmware.elf, который упал
- sameFirmware: true, если это та прошивка, что работает сейчас
- resetReason: esp_reset_reason() той загрузки, которая нашла падение, те же номера, что в твоём resetReason
- bootTime: Unix-время начала этой загрузки, добавляется после синхронизации NTP
- thisBoot: true, если падение найдено в этой загрузке

Как прочитать: shasum -a 256 .pio/build/<env>/firmware.elf, нужен тот ELF, чей хеш начинается с elfSha256:
xtensa-esp32s3-elf-addr2line -pfiaC -e firmware.elf <pc> <адреса backtrace>
Поэтому стоит хранить firmware.elf каждого релиза. Без него отчёт пользователя — просто адреса.

Что стоит знать:
- В IDF 4.4 abort() нарочно пишет по адресу 0, поэтому процессор сообщает об abort() или сработавшем assert как о StoreProhibited по адресу 0. Когда pc внутри panic_abort, causeName пишет "abort()", а откуда он вызван, показывает backtrace. Для этой проверки нужна та же сборка, ведь panic_abort от сборки к сборке переезжает, поэтому она работает, только когда sameFirmware равно true.
- Твой сторожевой таймер задач вызывает панику (esp_task_wdt_init(15, true)), так что зависший loop() тоже заканчивается в abort(), и causeName пишет "Task watchdog" (resetReason 6). Но таймер вызывает abort() из своего прерывания, поэтому task и backtrace относятся к тому, что прерывание застало, а не к зависшей задаче. Какая задача не сбросила таймер, печатается только в порт.
- Первая загрузка после прошивки этой версии может показать старый дамп, оставшийся в разделе от прежней прошивки. У него sameFirmware будет false.
- Если прошивка падает при каждой загрузке ещё до loop(), /api/info так и не поднимется, и падение видно только по строке в порту.
- Сброс к заводским настройкам lastCrash не очищает, он лежит в своём пространстве имён NVS, "crash". Заменяет его только следующее падение.
- При обычной загрузке это стоит нескольких чтений NVS и чтения 4 байт раздела. Проверка контрольной суммы и стирание выполняются только в загрузке после падения, и дамп стирается только после того, как сводка сохранена в NVS.
- Панель Diagnostics в портале я не трогал. Отчёт есть только в JSON.

Как проверено: на этой ветке — только три сборки. Эту ветку я ни на одну плату не прошивал. Упрощённая версия того же чтения работает в моём форке на плате Waveshare с 14 сентября. Она не проверяет контрольную сумму перед чтением сводки и не называет случаи сторожевого таймера и abort(). Там оно правильно прочитало мой намеренный тест с abort(), а 15 сентября поймало настоящий баг: IntegerDivideByZero в lfs_alloc, вызванном из lfs_file_write, когда запись в моём форке не поместилась на почти полную LittleFS. Твоя загрузка файлов проверяет свободное место перед записью, так что это только пример того, что показывает отчёт, а не сообщение о баге в твоём дереве. Не проверено: ни одна из твоих трёх плат и падение на этом дереве.

Сборки, espressif32@6.12.0, до — upstream main 9fa9ba4, после — эта ветка, в одном каталоге:

matrix-s3: флеш 1 624 729 -> 1 629 529 байт (+4 800), 82,6 % -> 82,9 % от 1 966 080. RAM 89 228 -> 89 608 байт (+380).
matrix-s3-wroom: флеш 1 639 617 -> 1 644 421 байт (+4 804), 25,0 % -> 25,1 %. RAM 89 360 -> 89 732 байта (+372).
matrix-waveshare: флеш 1 627 517 -> 1 632 353 байта (+4 836), 34,5 % -> 34,6 %. RAM 89 492 -> 89 864 байта (+372).

Николай
```
