# Draft: comment on Keralots/AnimatedPixelClock issue #3, the visualizer on the board's microphones

**Status: DRAFT, not posted.** Written 2026-09-15 22:20 at the owner's request ("напишешь автору, что перенесли аудиовизуальные эффекты на микрофоны и расширили варианты"). Post only on his "отправляй".

- **Where:** a comment on https://github.com/Keralots/AnimatedPixelClock/issues/3, the thread where Rafał answered and set the PR order.
- **Voice:** the owner's, correct and natural English, plain text.
- **Optional paragraphs:** the SHTC3 paragraph and the settings-save paragraph are additions the owner did not ask for. Rafał named the SHTC3 as the one peripheral he would take, and the save stall is a real bug in his current main. The owner can strike either.

## Figures used, and where they come from

| Figure | Source |
|---|---|
| PR #4 merged 2026-09-15 18:35:59 UTC as a091505 | `gh api repos/Keralots/AnimatedPixelClock/pulls/4` |
| Two analog mics, ES7210 ADC on I2S0; I2C on GPIO47/48 | KB [22](../22-audio-visualizer-onboard-mic.md), Waveshare schematic and BSP |
| 48 kHz capture, 20 ms DSP frames (about 50 per second) | panel serial `[audio] ES7210 up: 48 kHz, gain 30 dB`; `/api/info` audioFrames 245-256 per 5 s |
| The DSP builds the companion's FFT1 packet: 32 bands, 128 waveform samples; AGC, gate, beats | `tools/audiofx/dsp.py`, `src/audio/audio_dsp.cpp`, held equal on six WAVs by `make -C tools/audiofx/host check` |
| The PC stream wins when it is fresh (1.5 s), mics otherwise; source auto/pc/mic | `src/audio/audio_mic.cpp` `kPcFreshMs`, settings |
| Capture only while the visualizer shows the mics, stops 25 s after | `audio_mic.cpp` `kIdleStopMs`; panel test 2026-09-15 21:35-21:45 |
| 10.4 KB internal heap while running, nothing lost per start/stop cycle | panel `/api/info`: 32,952 B idle, 22,556 B running, 32,952 B after the second cycle |
| DSP 12-15 ms per 20 ms frame on core 0 | panel `/api/info` audioDspUs 11,782-15,134 µs |
| Eight new styles, pixel-identical to the Python previews in double | `make -C tools/audiofx/host wow`, 300 frames each |
| About 74 KB of flash for the mic path and the eight styles | `pio run -e matrix-waveshare-rgb`: 2,146,893 B at 776fc04, 2,220,729 B at 1dd9adb |
| Settings save held loop() 1,175 ms; "Settings saved (v2.0) in 1109 ms"; 51 ms after the fix | panel serial 2026-09-15 21:50 and 21:55; fork f79fe99 |
| The same code in his main | `src/config/settings.cpp:885-899` at a091505, `MAX_METRICS` 20 in `src/config/config.h:19` (read with `gh api` 2026-09-15 22:16); from dbe3978 (git blame) |
| SHTC3 id 0x0887, 10 reads, 0 CRC or I2C errors; reads about 31 °C inside the case, offset not measured | panel `/api/info` climate, KB [21](../21-onboard-climate-sensor.md) §12.7 |

## English (to post)

```text
Thanks for merging #4.

A small update from my side, not a PR. The visualizer on my Waveshare board now runs from its own two microphones, so it no longer needs the PC companion. The mics go through the ES7210 on I2S0, and the S3 captures at 48 kHz and runs the DSP every 20 ms. The DSP builds the same packet your companion sends, 32 bands and 128 waveform samples, with AGC, a noise gate and beat detection. Because of that your six styles work from the mics unchanged. When the companion stream is present it still wins, and the mics take over when it has been silent for 1.5 seconds; the source can also be forced to PC or mic in the portal.

I was careful with internal heap, since you know how tight it is on this board. Capture only runs while the visualizer is on screen and stops 25 seconds after it leaves. While it runs it costs about 10.4KB of internal heap (task stack, I2S DMA buffers, driver), measured on the panel. The DSP and style buffers live in PSRAM, and a start/stop cycle gives every byte back. The DSP itself takes 12 to 15 ms of each 20 ms frame on core 0, which is more than I would like, so that is next.

I also added eight new styles next to your six, all driven by the same frames with beat reactivity: Prism EQ, Neon Mirror+, Spectrogram, Radial Bloom, Beat Particles, Scope Afterglow, Twin VU and Synthwave Grid. I designed them as Python previews first and hold the C++ port pixel-identical to them in a host test. Together with the mic path they add about 74KB of flash. Not tested yet: latency against a clap, and noise from the LED supply.

It lives in my fork, behind -DAUDIO_MIC_ENABLED and -DVIZ_WOW_ENABLED, on the feat/audiofx-onboard-mic branch: https://github.com/NickoScope/AnimatedPixelClock/tree/feat/audiofx-onboard-mic
You said optional modules belong in the fork, so I am not assuming anything. If a local microphone source for the existing visualizer is something you would want upstream for the Waveshare env, tell me and I will cut it down to that.

On the SHTC3 you mentioned: it is working in my fork too, read on the shared I2C bus and shown on the weather clock as outdoor and indoor side by side. It reads about 31 C inside my case, so it needs a self-heating offset that I have not measured yet. I can send it after the four you asked for.

One bug you may want even without any of this. saveSettings() removes all 20 label keys and all 20 name keys whenever they are empty, and each key that does not exist is a failed nvs_erase_key with an error line on serial. On my panel every portal save froze the display for about 1.1 s: "Settings saved (v2.0) in 1109 ms". Checking preferences.isKey() before remove() brought it to 51 ms. The code is the same in your current main (src/config/settings.cpp). Happy to send that as a one-line PR if you like.

Nikolay
```

## Русский (для чтения, не публикуется)

```text
Спасибо, что влили #4.

Небольшая новость с моей стороны, не PR. Визуализатор на моей плате Waveshare теперь работает от её собственных двух микрофонов, так что компаньон на ПК больше не нужен. Микрофоны идут через ES7210 на I2S0, S3 пишет звук на 48 кГц и каждые 20 мс прогоняет DSP. DSP собирает тот же пакет, что шлёт ваш компаньон: 32 полосы и 128 отсчётов формы волны, с АРУ, шумовым порогом и детектором ударов. Поэтому ваши шесть стилей работают от микрофонов без изменений. Если поток компаньона есть, он по-прежнему главнее, а микрофоны подхватывают, когда он молчит 1,5 секунды; источник можно также принудительно выбрать в портале: ПК или микрофон.

Я аккуратно обошёлся с внутренней памятью: вы знаете, как на этой плате с ней тесно. Захват работает, только пока визуализатор на экране, и останавливается через 25 секунд после ухода с него. Пока работает, он стоит около 10,4 КБ внутренней памяти (стек задачи, DMA-буферы I2S, драйвер), измерено на панели. Буферы DSP и стилей лежат в PSRAM, а цикл старт/стоп возвращает всё до байта. Сам DSP занимает 12–15 мс из каждых 20 мс на ядре 0, это больше, чем хотелось бы, так что это следующее.

Ещё я добавил восемь новых стилей рядом с вашими шестью, все от тех же кадров и с реакцией на удары: Prism EQ, Neon Mirror+, Spectrogram, Radial Bloom, Beat Particles, Scope Afterglow, Twin VU и Synthwave Grid. Сначала я сделал их превью на Python, а порт на C++ держу попиксельно равным им в тесте на компьютере. Вместе с микрофонным трактом они добавляют около 74 КБ флеша. Пока не проверено: задержка по хлопку и шум от питания светодиодов.

Всё это живёт в моём форке за флагами -DAUDIO_MIC_ENABLED и -DVIZ_WOW_ENABLED, в ветке feat/audiofx-onboard-mic: ссылка.
Вы писали, что опциональные модули место в форке, так что я ничего не предполагаю. Если локальный источник с микрофона для существующего визуализатора вам нужен в upstream для env Waveshare, скажите, и я урежу до этого.

Про SHTC3, о котором вы писали: у меня в форке он тоже работает, читается на общей шине I2C и показывается на погодных часах как «улица» и «дом» рядом. В моём корпусе он показывает около 31 °C, так что ему нужна поправка на самонагрев, которую я ещё не измерил. Могу прислать после тех четырёх, что вы просили.

И одна ошибка, которая может пригодиться независимо от всего этого. saveSettings() удаляет все 20 ключей подписей и все 20 ключей имён, когда они пустые, и каждый несуществующий ключ даёт неудачный nvs_erase_key со строкой ошибки в порт. На моей панели каждое сохранение из портала замораживало экран примерно на 1,1 с: "Settings saved (v2.0) in 1109 ms". Проверка preferences.isKey() перед remove() довела это до 51 мс. В вашем текущем main тот же код (src/config/settings.cpp). Если хотите, пришлю однострочным PR.

Николай
```
