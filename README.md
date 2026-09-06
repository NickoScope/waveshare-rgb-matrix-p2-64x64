# LED Matrix Knowledge Base

База знаний по купленному железу: панель **Waveshare RGB-Matrix-P2-64x64-B** (SKU 33838)
и контроллер **Waveshare ESP32-S3-RGB-Matrix** (SKU 34422). Плюс контекст по экосистеме
Apollo Automation M-1, с которой мы сравнивали.

Собрано 2026-09-06. Все факты имеют ссылку на первоисточник, см. [docs/07-sources.md](docs/07-sources.md).

## Быстрый старт

Если железо ещё не включалось, читать по порядку:

1. [Панель](docs/01-panel.md) — что за железо, распиновка, GOB, ограничения
2. [Контроллер](docs/02-controller.md) — распиновка HUB75, периферия, питание
3. [Лучшие практики](docs/04-best-practices.md) — **прочитать до первого включения**
4. [Прошивки](docs/03-firmware.md) — выбрать путь и запустить

## Содержание

| Документ | О чём |
|---|---|
| [01-panel.md](docs/01-panel.md) | Waveshare RGB-Matrix-P2-64x64-B: спецификация, распиновка, GOB, комплект |
| [02-controller.md](docs/02-controller.md) | ESP32-S3-RGB-Matrix: SoC, память, питание, вся периферия, распиновка |
| [03-firmware.md](docs/03-firmware.md) | WLED, ESPHome, ESP-IDF, Arduino: что выбрать и как поставить |
| [04-best-practices.md](docs/04-best-practices.md) | Питание, гостинг, мерцание, яркость, память, разводка |
| [05-troubleshooting.md](docs/05-troubleshooting.md) | Симптом → причина → лечение |
| [06-projects.md](docs/06-projects.md) | Проекты сообщества, от которых можно оттолкнуться |
| [07-sources.md](docs/07-sources.md) | Все источники и за что каждый отвечает |
| [APOLLO-M1-DOSSIER.md](APOLLO-M1-DOSSIER.md) | Полное досье по экосистеме Apollo M-1 и сравнение с нашим железом |

## Готовые конфиги

| Файл | Назначение |
|---|---|
| [configs/esphome/waveshare-matrix.yaml](configs/esphome/waveshare-matrix.yaml) | Минимальный рабочий конфиг ESPHome под нашу плату и одну панель |
| [configs/arduino/smoke_test/smoke_test.ino](configs/arduino/smoke_test/smoke_test.ino) | Дымовой тест на Arduino: проверить, что панель вообще живая |

Распиновка в конфигах **сверена 2026-09-06** с собственными исходниками Waveshare
(`sdkconfig.defaults` для ESP-IDF и `esp32s3-default-pins.hpp` для Arduino) и совпала
полностью. Сами конфиги при этом **не компилировались и не заливались** на железо.

## Статус проверки фактов

| Помечено | Значение |
|---|---|
| без пометки | проверено по первоисточнику, ссылка в 07-sources.md |
| СПРАВОЧНО | из вторичного источника или отраслевая практика, на решения влиять не должно |
| НЕ ПРОВЕРЕНО | взято из чужого конфига или блога, требует сверки с железом |
