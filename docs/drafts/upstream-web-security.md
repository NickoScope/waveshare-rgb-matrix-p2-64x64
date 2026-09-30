# Upstream issue draft: the web server lets any page on the network reset, reflash or rewrite the clock (Keralots/AnimatedPixelClock)

Status: DRAFT, not posted. Posting waits for the owner's "отправляй". He asked for it at 18:14 on 2026-09-30: «автору пиши про все его недочеты, напиши мне на русском для подтверждения».

Facts checked 2026-09-30:
- Every point below was checked against upstream main 781b3935d6 (2026-09-29), src/web/web.cpp.
- Private vulnerability reporting is off on the repo, and there is no SECURITY.md.
- Our fixes are in fork branch fix/reset-csrf (d84c61c, 3cf33b3, fd27b56, fb5c41d), released as 2.7.9.

What an attacker needs: to get a page opened in a browser on the same network. The browser does the rest, with no script needed for some points.

## Title

Web server: any web page on the same network can factory-reset, reflash or reconfigure the clock

## Body (English, as it would be posted)

Hi, thanks for the project. I run a fork of it on a Waveshare 128x64 panel, and while testing my build I went through the web server. Everything below is in the current main (781b393). I could not find a private way to report security issues, so I am opening this here. I am happy to send a PR.

The common cause is that the ESP32 web server accepts writes from any web page. A browser sends some requests to another site without asking it first (a CORS preflight): plain GETs, and POSTs whose body is a form, multipart or text/plain. So a page on any site, opened in a browser on the same network, can make these calls to the clock:

1. Factory reset by a GET (serious). `server.on("/reset", handleReset);` has no method, so a GET is enough. handleReset clears the settings, resets the Wi-Fi and restarts, and the clock comes back in the setup AP. One `<img src="http://<clock>/reset">` does it, with no script.

2. Firmware update from any page (serious). `/update` checks nothing about where the upload comes from, and multipart/form-data needs no preflight. So a page can post a firmware image with `fetch(..., {mode: 'no-cors', body: formData})`, and the clock flashes it and restarts. That is arbitrary code on the device. Separately, a POST to `/update` with no file in it still answers OK and restarts the clock.

3. Settings rewritten from any page. `/save` (urlencoded), `/api/import` (reads the body without checking its Content-Type, so text/plain works), `/api/rename`, `/api/panel` (the HUB75 driver options), `/api/anim/upload` and `/api/notify` all accept a cross-site request.

4. Deleting by a GET. `/api/anim/delete?name=` is a GET, so an image tag can delete uploaded animations.

5. The weather API key can be read by any page. `/api/export` answers with `Access-Control-Allow-Origin: *` and includes `weatherApiKey`, so any site can read it through the visitor's browser. The export is also built by string concatenation without escaping, so a value with a quote in it breaks the JSON.

What I did in my fork, in case it helps:
- `/reset` is POST only, needs Content-Type application/json and the body `{"confirm":"factory-reset"}`; a GET gets 405. A cross-site JSON POST needs a preflight, and the server answers no OPTIONS, so a browser will not send it.
- One check, used by every write: when the request has an Origin header (browsers send it on every POST), it must be exactly `http://<Host>`, and Host must be an IP address or a `.local` name. That also blocks DNS rebinding. An Origin of `null` (no-referrer pages, sandboxed iframes) is refused. Home Assistant, curl and scripts send no Origin and are not affected.
- The OTA upload, the animation upload, `/save`, `/api/import`, `/api/rename` and `/api/notify` use that check. Nothing of a refused upload is written.
- `/api/anim/delete` is POST.
- No CORS header on `/api/export`.

The other GET controls (display on/off, brightness, mode, clock style, reboot) can be triggered the same way, but they lose nothing, so I left them as documented for home automation.

## Русский перевод (для владельца, не публикуется)

**Заголовок:** Веб-сервер: любая веб-страница в той же сети может сбросить, перепрошить или перенастроить часы.

Привет, спасибо за проект. Я использую его форк на панели Waveshare 128x64 и, проверяя свою сборку, прошёлся по веб-серверу. Всё ниже есть в текущей main (781b393). Закрытого способа сообщить об уязвимостях я не нашёл, поэтому пишу здесь. Могу прислать PR.

Общая причина: веб-сервер ESP32 принимает изменения от любой веб-страницы. Некоторые запросы браузер отправляет на чужой сайт, не спрашивая его заранее (предварительный запрос CORS): обычные GET и POST, у которых тело — форма, multipart или text/plain. Поэтому страница любого сайта, открытая в браузере в той же сети, может сделать с часами следующее:

1. Сброс к заводским настройкам через GET (серьёзно). У `server.on("/reset", handleReset);` не указан метод, поэтому хватает GET. handleReset стирает настройки, сбрасывает Wi-Fi и перезагружает; часы поднимаются в точке доступа настройки. Делается одной картинкой `<img src="http://<часы>/reset">`, без скрипта.

2. Обновление прошивки с любой страницы (серьёзно). `/update` никак не проверяет, откуда пришла загрузка, а multipart/form-data не требует предварительного запроса. Значит, страница может отправить образ прошивки через `fetch(..., {mode: 'no-cors', body: formData})` — часы его запишут и перезагрузятся. Это произвольный код на устройстве. Отдельно: POST на `/update` без файла всё равно отвечает OK и перезагружает часы.

3. Перезапись настроек с любой страницы. `/save` (urlencoded), `/api/import` (читает тело, не проверяя Content-Type, так что text/plain проходит), `/api/rename`, `/api/panel` (параметры драйвера HUB75), `/api/anim/upload` и `/api/notify` — все принимают запрос с чужого сайта.

4. Удаление через GET. `/api/anim/delete?name=` — это GET, так что картинка может удалить загруженные анимации.

5. Ключ погодного сервиса может прочитать любая страница. `/api/export` отвечает с `Access-Control-Allow-Origin: *` и содержит `weatherApiKey`, так что любой сайт прочитает его через браузер посетителя. К тому же экспорт собирается склейкой строк без экранирования, и значение с кавычкой ломает JSON.

Что я сделал у себя в форке, если пригодится:
- `/reset` — только POST, Content-Type application/json и тело `{"confirm":"factory-reset"}`; на GET — 405. Межсайтовый JSON-POST требует предварительного запроса, а сервер на OPTIONS не отвечает, так что браузер его не отправит.
- Одна проверка для всех изменений: если у запроса есть заголовок Origin (браузеры ставят его на каждый POST), он должен быть ровно `http://<Host>`, а Host — IP-адресом или именем `.local`. Это закрывает и подмену DNS. Origin `null` (страницы с no-referrer, песочницы iframe) отклоняется. Home Assistant, curl и скрипты Origin не шлют, их это не затрагивает.
- Эту проверку используют загрузка прошивки, загрузка анимаций, `/save`, `/api/import`, `/api/rename` и `/api/notify`. От отклонённой загрузки ничего не записывается.
- `/api/anim/delete` — POST.
- У `/api/export` нет заголовка CORS.

Остальные GET-команды (включить и выключить экран, яркость, режим, стиль часов, перезагрузка) тоже можно вызвать так же, но они ничего не теряют, поэтому я оставил их, как они описаны для домашней автоматизации.
