# Upstream issue draft: the web flasher wipes the settings even when told not to erase (Keralots/AnimatedPixelClock)

Status: POSTED 2026-09-30 ~22:24 on the owner's «да, отправляй, только аккуратно, по-человечески»: https://github.com/Keralots/AnimatedPixelClock/issues/12 (as NickoScope, no attribution line). The posted body adds a paragraph on the spare-board test (/tmp/issue_flasher.txt text).

Facts checked 2026-09-30 against upstream main:
- docs/flasher.js:54 sets `new_install_prompt_erase: true`.
- docs/flasher.js:63 writes one part: `parts: [{ path: binUrl, offset: 0 }]`, the merged Full.bin.
- release.py:146, merge_segments, fills the gaps between parts with 0xFF.
- platformio.ini:105: the Waveshare env uses large_littlefs_32MB.csv, with nvs at 0x9000, size 0x5000.
- So the gap from the end of the partition table to otadata at 0xE000 covers all of NVS. Our v2.7.12 Full.bin has only 0xFF there.
- Our fix is fork branch feat/flasher-keep-settings (6ee70d6): four parts at 0x0, 0x8000, 0xE000 and 0x10000. The parts rebuild Full.bin byte for byte and do not touch 0x9000-0xE000.
- Tested over USB on a spare Waveshare board (MAC 90:e5:b1:d2:0e:b0), 2026-09-30 22:04-22:21, with the owner clicking in Chrome:
  - Control (the old published flasher, one Full.bin, "don't erase"): the Wi-Fi and the settings were gone (the board booted into the setup AP). NVS read over USB no longer held the device name "sparetest".
  - Fix (the new flasher from localhost, four parts, "don't erase"), on a board running from app1 after an OTA: back on the same IP, with the device name "sparetest", 12-hour clock, clock style 8 and the uploaded effect WARP. It booted the new firmware from app0.
- Published to the web flasher (main 76c5ebd) after that test.

## Title

Web flasher: "don't erase" still wipes the settings and Wi-Fi

## Body (English, as it would be posted; plain, in the owner's voice)

Hi! One more thing I ran into, this time in the web flasher.

When you install, the flasher asks whether to erase the device. I expected that saying no would keep the settings and the Wi-Fi, but it doesn't: they are gone either way.

The reason is how the image is written. The flasher writes one merged Full.bin starting at 0x0, and release.py fills the gaps between the parts with 0xFF when it merges them. The NVS partition, where the settings and the Wi-Fi live, sits right in one of those gaps, between the partition table at 0x8000 and the OTA data at 0xE000. So writing Full.bin overwrites all of NVS with 0xFF, erase or no erase. Only the LittleFS area with the uploaded animations survives, because the image doesn't reach that far.

What I did in my fork: the manifest now lists the four parts separately, each at its own offset (bootloader at 0x0, partition table at 0x8000, OTA data at 0xE000, the app at 0x10000), and release.py puts those files next to Full.bin. Nothing between the parts is written, so "don't erase" keeps the settings. I checked that the parts rebuild Full.bin byte for byte and don't touch 0x9000 to 0xE000. Full.bin is still there for the release page and for writing by hand.

Happy to send a PR if you want.

## Русский перевод (для владельца, не публикуется)

Заголовок: Веб-прошивальщик: «не стирать» всё равно стирает настройки и Wi-Fi

Привет! Ещё одна вещь, на которую я наткнулся, на этот раз в веб-прошивальщике.

При установке прошивальщик спрашивает, стереть ли устройство. Я ожидал, что если ответить «нет», настройки и Wi-Fi сохранятся, но нет: они пропадают в любом случае.

Причина в том, как записывается образ. Прошивальщик пишет один склеенный Full.bin, начиная с 0x0, а release.py при склейке заполняет промежутки между частями байтами 0xFF. Раздел NVS, где живут настройки и Wi-Fi, лежит как раз в одном из этих промежутков, между таблицей разделов на 0x8000 и данными OTA на 0xE000. Поэтому запись Full.bin затирает весь NVS байтами 0xFF, со стиранием или без. Выживает только область LittleFS с загруженными анимациями, потому что образ до неё не доходит.

Что я сделал у себя в форке: манифест теперь перечисляет четыре части отдельно, каждую со своим адресом (загрузчик на 0x0, таблица разделов на 0x8000, данные OTA на 0xE000, приложение на 0x10000), а release.py кладёт эти файлы рядом с Full.bin. Между частями ничего не пишется, так что «не стирать» сохраняет настройки. Я проверил, что части собираются в Full.bin байт в байт и не задевают область от 0x9000 до 0xE000. Full.bin остаётся для страницы релиза и для записи вручную.

Если хочешь, пришлю PR.
