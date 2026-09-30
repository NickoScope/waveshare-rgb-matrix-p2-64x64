# Upstream issue draft: the web server lets any page on the network reset, reflash or rewrite the clock (Keralots/AnimatedPixelClock)

Status: POSTED 2026-09-30 18:21 on the owner's «да, отпрвляй»: https://github.com/Keralots/AnimatedPixelClock/issues/11 (as NickoScope, no attribution line).

Facts checked 2026-09-30:
- Every point below was checked against upstream main 781b3935d6 (2026-09-29), src/web/web.cpp.
- Private vulnerability reporting is off on the repo, and there is no SECURITY.md.
- Our fixes are in fork branch fix/reset-csrf (d84c61c, 3cf33b3, fd27b56, fb5c41d), released as 2.7.9.

What an attacker needs: to get a page opened in a browser on the same network. The browser does the rest, with no script needed for some points.

## Title

Any web page on the home network can reset or reflash the clock

## Body (English, as it would be posted; plain, in the owner's voice - his request 18:18 «напиши человеческим языком, как я»)

Hi! Thanks for the clock, I really like it. I run a fork on a Waveshare 128x64 panel.

While testing my build I found a few holes in the web server, and they are in your current main too. I didn't find a private way to report this, so I'm writing here.

In short: the clock trusts any web page. If someone at home opens a bad page in their browser, that page can quietly send commands to the clock, and nobody has to click anything.

What such a page can do:

1. Wipe the clock to factory settings. /reset works on a plain GET, so one image on a page pointing at http://<clock>/reset erases the settings and the Wi-Fi.
2. Put its own firmware on the clock. /update takes an upload from anywhere, so a page can flash anything it wants. This is the worst one. Also, a POST to /update with no file still restarts the clock.
3. Change the settings: /save, /api/import, /api/rename, /api/panel, /api/anim/upload and /api/notify accept requests from other sites.
4. Delete uploaded animations: /api/anim/delete is a GET.
5. Read the weather API key: /api/export lets any site read it (Access-Control-Allow-Origin: *). And the export is glued together from strings, so a quote in any value breaks the JSON.

How I fixed it in my fork, if it helps:
- /reset only works as a POST with {"confirm":"factory-reset"} in the body.
- Every command that changes something checks the Origin header: if a browser sent it from someone else's page, the clock says no. Home Assistant, curl and scripts don't send that header, so they keep working.
- /api/anim/delete became a POST, and /api/export no longer lets other sites read it.

The rest (screen on/off, brightness, clock style, reboot) I left as is: it's harmless and people use it from Home Assistant.

Happy to send a PR if you want.

## Русский перевод (для владельца, не публикуется)

Заголовок: Любая веб-страница в домашней сети может сбросить или перепрошить часы

Привет! Спасибо за часы, очень нравятся. Я использую форк на панели Waveshare 128x64.

Пока проверял свою сборку, нашёл несколько дыр в веб-сервере, и они есть в твоей текущей main. Закрытого способа сообщить не нашёл, поэтому пишу здесь.

Если коротко: часы доверяют любой веб-странице. Если кто-то дома откроет в браузере плохую страницу, она может тихо отправить часам команды, и никому ничего нажимать не нужно.

Что такая страница может сделать:

1. Сбросить часы к заводским настройкам. /reset срабатывает на обычный GET, так что одна картинка на странице с адресом http://<часы>/reset стирает настройки и Wi-Fi.
2. Залить на часы свою прошивку. /update принимает загрузку откуда угодно, так что страница может прошить что угодно. Это самое плохое. Кроме того, POST на /update без файла всё равно перезагружает часы.
3. Поменять настройки: /save, /api/import, /api/rename, /api/panel, /api/anim/upload и /api/notify принимают запросы с чужих сайтов.
4. Удалить загруженные анимации: /api/anim/delete работает через GET.
5. Прочитать ключ погодного сервиса: /api/export разрешает читать себя любому сайту (Access-Control-Allow-Origin: *). И экспорт склеен из строк, так что кавычка в любом значении ломает JSON.

Как я починил у себя в форке, если пригодится:
- /reset работает только как POST с {"confirm":"factory-reset"} в теле.
- Каждая команда, которая что-то меняет, проверяет заголовок Origin: если браузер прислал её с чужой страницы, часы отказывают. Home Assistant, curl и скрипты этот заголовок не шлют, так что у них всё работает.
- /api/anim/delete стал POST, а /api/export больше не даёт чужим сайтам себя читать.

Остальное (включить и выключить экран, яркость, стиль часов, перезагрузка) оставил как есть: это безобидно, и этим пользуются из Home Assistant.

Если хочешь, пришлю PR.
