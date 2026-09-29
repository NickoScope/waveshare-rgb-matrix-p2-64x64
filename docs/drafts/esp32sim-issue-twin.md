# Issue on joakimeriksson/esp32sim: a virtual twin of an LED panel built on esp32sim (draft)

Status: DRAFT, not posted. Post only on the owner's «отправляй».

**Where:** a new issue on https://github.com/joakimeriksson/esp32sim/issues. Discussions are off on that repository, and issues are the only public channel.

**Facts checked 2026-09-29:**
- **Upstream is active:** last push 2026-09-23. The author merges outside pull requests (67 merged from aliceisjustplaying).
- **Waveshare boards are already welcome upstream:** the repository has `waveshare-lcd4b`, `waveshare-cam` and `waveshare-amoled18-v2`.
- **The fork:** https://github.com/NickoScope/TWIN-NickoScopeMatrix-64x128, branch `nickoscope/twin`, 49 commits over upstream 4ab7e90. What it adds is in NICKOSCOPE.md there.
- **Verified with the real, unmodified firmware (AnimatedPixelClock v2.7.3 and v2.7.4):**
  - boot from the octal flash;
  - the HUB75 picture at 106.1 refreshes a second;
  - the IR remote codes learned by the firmware's own learn mode;
  - the knob;
  - Wi-Fi, the portal and OTA;
  - on the owner's LAN through socket_vmnet;
  - the project's ESP Web Tools page flashing a blank twin, with Improv Wi-Fi after it.

## Body (English, as it would be posted)

Hi Joakim,

thank you for esp32sim. I build firmware for an LED clock panel, a Waveshare ESP32-S3-RGB-Matrix board with a 128x64 HUB75 panel, and I wanted a copy of the panel on my Mac that runs the real firmware binary. esp32sim was the one emulator that got there. It boots our Arduino 2.0.17 image from the real ROM, and the Wi-Fi works with the real blob. I did not expect that.

I forked it and added what our board needed. The work is on this branch, with a short list of what it adds in NICKOSCOPE.md:
https://github.com/NickoScope/TWIN-NickoScopeMatrix-64x128/tree/nickoscope/twin

In short:
- octal Macronix flash and a flash file that is written through;
- LCD_CAM in i8080 mode streaming the GDMA ring, with a HUB75 decoder and a page that shows the panel;
- an empty SD slot;
- the panel's inputs at pin level: an NEC IR receiver and an EC11 knob;
- inbound port forwarding, and a bridge mode to the real LAN through socket_vmnet;
- the USB Serial/JTAG line state (DTR/RTS resets as in the TRM tables), a lossless WebSocket channel for it, and RFC 2217. With these, esptool and ESP Web Tools flash the emulated chip through the real ROM and stub;
- a fractional CPI, which I calibrated against our panel's frame times.

Everything was checked with our real firmware, unmodified. If any of it is useful to you, I would be glad to send pull requests one piece at a time, in your style and with tests. If not, no answer is needed. Thank you again for the emulator.

Nikolay

## Русский перевод (для владельца, не публикуется)

Привет, Йоаким,

спасибо за esp32sim. Я делаю прошивку для светодиодной панели-часов: плата Waveshare ESP32-S3-RGB-Matrix с панелью HUB75 128x64. Мне хотелось иметь на Маке копию панели, которая запускает настоящий бинарник прошивки. esp32sim оказался единственным эмулятором, который до этого дошёл. Он загружает наш образ на Arduino 2.0.17 с настоящего ПЗУ, и Wi-Fi работает на настоящей библиотеке. Этого я не ожидал.

Я сделал форк и добавил то, что нужно нашей плате. Работа лежит в этой ветке, короткий список добавленного — в NICKOSCOPE.md:
https://github.com/NickoScope/TWIN-NickoScopeMatrix-64x128/tree/nickoscope/twin

Коротко:
- октальная флэш Macronix и файл флэша, в который всё сразу записывается;
- LCD_CAM в режиме i8080, который гонит кольцо GDMA, с декодером HUB75 и страницей, где видна панель;
- пустой слот SD;
- входы панели на уровне выводов: ИК-приёмник NEC и энкодер EC11;
- входящий проброс портов и режим моста в настоящую сеть через socket_vmnet;
- состояние линий USB Serial/JTAG (сбросы по DTR/RTS по таблицам TRM), канал для него через WebSocket без потерь и RFC 2217. С ними esptool и ESP Web Tools прошивают эмулированный чип через настоящее ПЗУ и стаб;
- дробный CPI, который я откалибровал по времени кадров нашей панели.

Всё проверено на нашей настоящей прошивке без правок. Если что-то из этого тебе пригодится, буду рад прислать pull request'ы по одному куску, в твоём стиле и с тестами. Если нет — отвечать не нужно. Ещё раз спасибо за эмулятор.

Николай
