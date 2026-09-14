# Draft: Reddit comments on the AnimatedPixelClock post

**Status: DRAFT, not posted.** Posted only when the owner says so, from his
logged-in Reddit account in Chrome (u/No-Recording-8313). Written 2026-09-15 in
the owner's own voice, plain text.

Thread: r/esp32, "I may have gone a bit overboard with this ESP32-S3 pixel clock",
by u/AdvertisingFormal746 (Keralots), 8 days old at the time, 2.3k upvotes,
104 comments:
https://old.reddit.com/r/esp32/comments/1w8vc0j/i_may_have_gone_a_bit_overboard_with_this_esp32s3/

Claims in the text and what backs them:

| Claim | Backed by |
|---|---|
| Runs on the Waveshare ESP32-S3-RGB-Matrix, two 64×64 panels | the panel on the desk, since 2026-09-14 |
| Default S3 pin map with E on GPIO9, `opi_opi` needed | fork `platformio.ini` and `matrix_display.h`; the boot failure with `qio_opi` is in commit `e0757f8` |
| Wi-Fi, web UI, NTP and OTA all work with DMA running | on the panel 2026-09-14/15: OTA test, NTP sync, portal checks ([03](../03-firmware.md)) |

## 1. Top-level comment (praise, "a great base to build on")

```text
Great work, honestly one of the nicest ESP32 projects I saw this year. Its not only a clock, its a really good base for development, the code is clean enough that you can build a lot on top of it. I forked it and run it on a Waveshare driver board with two 64x64 panels, added a knob, Home Assistant pages, world clock, flight and train boards, Lua effects, and the render loop still keeps up fine. Thanks for making it open source!
```

Russian, for reading:

```text
Отличная работа, честно один из самых классных ESP32 проектов, что я видел в этом году. Это не просто часы, это очень хорошая база для разработки, код достаточно чистый, чтобы на нём можно было много чего построить. Я сделал форк и запускаю его на драйверной плате Waveshare с двумя панелями 64x64, добавил крутилку, страницы Home Assistant, мировое время, табло аэропорта и поездов, Lua эффекты, и цикл отрисовки по-прежнему спокойно справляется. Спасибо, что выложил в открытый доступ!
```

## 2. Reply in the Waveshare thread

Where: under the author's answer to u/Fanalogy, who asked whether it works on an
"s3 portal matrix board". The author answered that no such board works out of the box
(you need a pin map and a PlatformIO env) and warned that some S3 HUB75 boards lose
Wi-Fi once DMA runs. A working all-in-one S3 board with the environment ready is
exactly what that thread lacks.

```text
For anyone looking for a ready S3 board for this: I run it on the Waveshare ESP32-S3-RGB-Matrix (their driver board, not only the panels). Pin map is the library default for S3, only E is on GPIO9. The module is octal flash + octal PSRAM, so it needs board_build.arduino.memory_type = opi_opi, with qio_opi it flashes but never boots. WiFi, web UI, NTP and OTA all work fine with DMA running on two 64x64 panels. Env for it is in my fork, branch board/waveshare-esp32-s3-rgb-matrix: https://github.com/NickoScope/AnimatedPixelClock
```

Russian, for reading:

```text
Для тех, кто ищет готовую S3 плату под это: я запускаю на Waveshare ESP32-S3-RGB-Matrix (их драйверная плата, не только панели). Раскладка пинов стандартная из библиотеки для S3, только E на GPIO9. Модуль с octal flash + octal PSRAM, поэтому нужен board_build.arduino.memory_type = opi_opi, с qio_opi прошивка заливается, но не стартует. WiFi, веб интерфейс, NTP и OTA нормально работают при запущенном DMA на двух панелях 64x64. Окружение для неё в моём форке, ветка board/waveshare-esp32-s3-rgb-matrix: https://github.com/NickoScope/AnimatedPixelClock
```
