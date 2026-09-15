# Draft: upstream PR 1 to Keralots/AnimatedPixelClock, mbedTLS buffers in PSRAM

**Status: DRAFT, not posted. Revised after the audit gate (2026-09-15 18:25): the security paragraph now says the switch is global, WPA3-SAE included, and flash encryption is off.** Nothing is pushed. The branch exists only locally.

Written 2026-09-15 in the owner's voice: correct, natural English, plain paragraphs.
Rafał asked for this one first in his answer on issue #3
(https://github.com/Keralots/AnimatedPixelClock/issues/3#issuecomment-5682483397, item 3).
Plan behind it: [09-upstream-contributions.md](../09-upstream-contributions.md).

## What is ready

- Branch `feat/tls-buffers-psram`, made from `upstream/main` at `9e37721` (v2.3.1).
- One commit, `e329a49`: `feat(net): allocate mbedTLS buffers in PSRAM`.
- Files: `src/network/tls_psram.h` (new, 15 lines), `src/network/tls_psram.cpp` (new, 36 lines), `src/main.cpp` (+4 lines).
- To open the PR, the owner pushes the branch to the NickoScope fork and opens it against `Keralots:main`. That happens only on "отправляй".

## His rules, checked

| Rule | This PR |
|---|---|
| One PR per change, off `main` | one change, branch from `upstream/main` 9e37721 |
| Conventional Commits | `feat(net): ...` |
| No `FIRMWARE_VERSION` bump or release notes | none |
| Keep the existing formatting | upstream header comment, include guard, 2-space indent |
| README only if user setup is needed | no setup, README untouched |
| All three envs build | `matrix-s3`, `matrix-s3-wroom`, `matrix-waveshare`: SUCCESS |
| `matrix-s3` size in the description | yes, before and after |
| No build flag, on by default | no flag; a run-time `psramFound()` check only |

## Figures used, and where they come from

| Figure | Source |
|---|---|
| `CONFIG_MBEDTLS_INTERNAL_MEM_ALLOC`, `CONFIG_MBEDTLS_SSL_MAX_CONTENT_LEN 16384` | `sdkconfig.h` of all six esp32s3 memory variants (dio_opi, dio_qspi, opi_opi, opi_qspi, qio_opi, qio_qspi), no asymmetric override in framework-arduinoespressif32 3.20017 (arduino-esp32 2.0.17) |
| `MBEDTLS_PLATFORM_MEMORY` without the CALLOC/FREE macros | the framework's `mbedtls/port/include/mbedtls/esp_config.h` lines 98-105; the same lines in ESP-IDF v4.4.7 on GitHub |
| `mbedtls_platform_set_calloc_free()` declared and exported | the framework's `mbedtls/platform.h` line 165; `nm` on `libmbedcrypto.a` shows `T mbedtls_platform_set_calloc_free` |
| Default free is `heap_caps_free()` | `components/mbedtls/port/esp_mem.c` at ESP-IDF v4.4.7 |
| Security note on external memory | help text of `MBEDTLS_MEM_ALLOC_MODE` in `components/mbedtls/Kconfig` at ESP-IDF v4.4.7 |
| Heap before/after (68.7 -> 16.5-20.8 KB, 11.2 KB, 7.7 KB; 56.7 KB, 51.2 KB, PSRAM -42.7 KB) | fork commit `ed201cf`, [12-bringup.md](../12-bringup.md) question 7, measured on the Waveshare panel 2026-09-14 |
| Build sizes | `pio run` on 9e37721 and on the branch, 2026-09-15, espressif32@6.12.0 |

## English (to post)

Title:

```text
feat(net): allocate mbedTLS buffers in PSRAM
```

Body:

```text
This is item 3 from #3, the one you asked for first.

What it does: a new src/network/tls_psram.cpp with one function, tlsUsePsram(), called first thing in setup(). It calls mbedtls_platform_set_calloc_free() with an allocator that takes memory from PSRAM and falls back to internal SRAM if a PSRAM allocation fails. If there is no PSRAM, or a PSRAM allocation fails, the memory comes from internal SRAM exactly as before. No build flag, no setting, no README change.

Why: the precompiled arduino-esp32 2.0.17 libraries are built with CONFIG_MBEDTLS_INTERNAL_MEM_ALLOC, and as you pointed out, CONFIG_MBEDTLS_SSL_MAX_CONTENT_LEN is 16384 in every memory variant. So each TLS session takes a 16KB input buffer and a 16KB output buffer, plus the handshake, from internal heap. Today that session is the weather fetch.

How it works: the libraries' mbedtls/esp_config.h defines MBEDTLS_PLATFORM_MEMORY without the CALLOC/FREE macros. In that configuration mbedtls/platform.h declares mbedtls_platform_set_calloc_free(), and libmbedcrypto.a exports it. This is what the mbedTLS Kconfig help calls the custom allocation mode, chosen at run time instead of when the libraries are built, and unlike CONFIG_MBEDTLS_EXTERNAL_MEM_ALLOC it keeps internal SRAM as a fallback. The default free in esp_mem.c is heap_caps_free(), which accepts a pointer from any heap, and the new free is the same call, so anything allocated before the switch is still freed correctly. I checked this against the headers and libraries in framework-arduinoespressif32 3.20017 and against esp_mem.c and the mbedTLS Kconfig in ESP-IDF v4.4.7.

One trade you should know about. The switch is global: every mbedTLS allocation goes to PSRAM, not only the weather session. That includes the Wi-Fi supplicant's WPA3-SAE math, which works on values derived from the Wi-Fi password. The Kconfig help for the mbedTLS allocation mode recommends internal memory for security, and calls PSRAM on the S3 a safe choice only when flash encryption is enabled. None of the three envs enable it, so these values sit in PSRAM unencrypted. For context, the same flash already stores the Wi-Fi password and the settings unencrypted, and the weather fetch uses setInsecure(). I think it is a good trade, but it is your call.

Builds, espressif32@6.12.0, upstream main 9e37721 before, this branch after:

matrix-s3: Flash 1,624,273 -> 1,624,481 bytes (about +200; builds of the same commit differ by up to 16 bytes), 82.6% of 1,966,080 before and after. RAM 89,220 bytes, unchanged.
matrix-s3-wroom: Flash 1,639,153 -> 1,639,345 bytes (about +200), 25.0%. RAM 89,352 bytes, unchanged.
matrix-waveshare: Flash 1,627,145 -> 1,627,353 bytes (about +200), 34.5%. RAM 89,484 bytes, unchanged.

How it was tested: on this branch, only the three builds above. I haven't flashed this branch to any board. The same allocator has been running in my fork on the Waveshare board (16MB octal PSRAM) since 14 September, and I measured it there. I polled free heap every 3 seconds over several display cycles while a TLS websocket was open for 15 seconds at a time. Before the change, free internal heap dropped from 68.7KB to 16.5-20.8KB while the session was open, the low-water mark was 11.2KB and the largest free block was 7.7KB. After the change, the low-water mark was 56.7KB, the largest free block never went under 51.2KB, and PSRAM dropped by 42.7KB during the session instead. No reboot in either run. That session was a TLS websocket, and my fork runs a lot more than yours, so the absolute numbers won't match your builds. The part that comes from the two record buffers should carry over to the weather fetch; the rest depends on the server and its certificate chain.

Not tested: a weather fetch on this tree, and any of your three boards. I haven't timed a handshake on the 2MB quad PSRAM of the matrix-s3 board. freeInternalHeap and largestHeapBlock in /api/info should show the difference during a weather fetch.

Nikolay
```

## Русский (для чтения, не публикуется)

```text
Заголовок: feat(net): буферы mbedTLS в PSRAM

Это пункт 3 из #3, тот, который вы попросили прислать первым.

Что делает: новый файл src/network/tls_psram.cpp с одной функцией tlsUsePsram(), она вызывается первой строкой в setup(). Функция вызывает mbedtls_platform_set_calloc_free() с аллокатором, который берёт память из PSRAM, а если выделить в PSRAM не удалось, берёт из внутренней SRAM. Если PSRAM нет или выделить в ней не удалось, память берётся из внутренней SRAM ровно как раньше. Без флага сборки, без настройки, без изменений в README.

Зачем: готовые библиотеки arduino-esp32 2.0.17 собраны с CONFIG_MBEDTLS_INTERNAL_MEM_ALLOC, и, как вы заметили, CONFIG_MBEDTLS_SSL_MAX_CONTENT_LEN равен 16384 во всех вариантах памяти. Поэтому каждая TLS-сессия берёт из внутренней памяти входной буфер 16КБ и выходной 16КБ, плюс рукопожатие. Сейчас такая сессия у вас одна, это запрос погоды.

Как работает: mbedtls/esp_config.h в этих библиотеках определяет MBEDTLS_PLATFORM_MEMORY без макросов CALLOC/FREE. В такой конфигурации mbedtls/platform.h объявляет mbedtls_platform_set_calloc_free(), а libmbedcrypto.a её экспортирует. В справке Kconfig mbedTLS это называется пользовательским режимом выделения памяти; он выбирается при запуске, а не при сборке библиотек, и в отличие от CONFIG_MBEDTLS_EXTERNAL_MEM_ALLOC оставляет внутреннюю SRAM запасным путём. Стандартное освобождение в esp_mem.c это heap_caps_free(), она принимает указатель из любой кучи, и новое освобождение вызывает то же самое, так что всё, что было выделено до переключения, освобождается правильно. Я сверил это с заголовками и библиотеками framework-arduinoespressif32 3.20017 и с esp_mem.c и Kconfig mbedTLS в ESP-IDF v4.4.7.

Один компромисс, о котором стоит знать. Переключение глобальное: в PSRAM уходят все выделения mbedTLS, а не только сессия погоды. В том числе вычисления WPA3-SAE в Wi-Fi supplicant, которые работают со значениями, полученными из пароля Wi-Fi. Справка Kconfig к режиму выделения памяти mbedTLS рекомендует внутреннюю память с точки зрения безопасности и считает PSRAM на S3 безопасной только при включённом шифровании флеша. Ни в одной из трёх сборок оно не включено, так что эти значения лежат в PSRAM незашифрованными. Для сравнения: тот же флеш уже хранит пароль Wi-Fi и настройки незашифрованными, а запрос погоды использует setInsecure(). Я считаю это хорошим обменом, но решать вам.

Сборки, espressif32@6.12.0, до: upstream main 9e37721, после: эта ветка:

matrix-s3: Flash 1 624 273 -> 1 624 481 байт (около +200; сборки одного коммита расходятся до 16 байт), 82,6% из 1 966 080 до и после. RAM 89 220 байт, без изменений.
matrix-s3-wroom: Flash 1 639 153 -> 1 639 345 байт (около +200), 25,0%. RAM 89 352 байта, без изменений.
matrix-waveshare: Flash 1 627 145 -> 1 627 353 байта (около +200), 34,5%. RAM 89 484 байта, без изменений.

Как проверено: на этой ветке только три сборки выше. Эту ветку я ни на одну плату не прошивал. Тот же аллокатор работает в моём форке на плате Waveshare (16МБ octal PSRAM) с 14 сентября, и там я его мерил. Я опрашивал свободную память каждые 3 секунды на протяжении нескольких циклов экранов, пока TLS-вебсокет был открыт по 15 секунд за раз. До изменения свободная внутренняя память падала с 68,7КБ до 16,5-20,8КБ, пока сессия была открыта, минимум был 11,2КБ, а самый большой свободный блок 7,7КБ. После изменения минимум был 56,7КБ, самый большой свободный блок ни разу не опускался ниже 51,2КБ, а во время сессии вместо этого на 42,7КБ проседала PSRAM. Ни одной перезагрузки ни в одном прогоне. Та сессия была TLS-вебсокетом, а в моём форке работает намного больше, чем у вас, так что абсолютные цифры с вашими сборками не совпадут. Часть экономии от двух буферов записей должна перенестись на запрос погоды; остальное зависит от сервера и цепочки его сертификатов.

Не проверено: запрос погоды на этом дереве и ни одна из ваших трёх плат. Я не замерял время рукопожатия на 2МБ quad PSRAM платы matrix-s3. freeInternalHeap и largestHeapBlock в /api/info должны показать разницу во время запроса погоды.

Николай
```
