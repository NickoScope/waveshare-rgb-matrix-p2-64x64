# Upstream issue draft: /reset factory-resets on a GET (Keralots/AnimatedPixelClock)

Status: DRAFT, not posted. It is posted only on the owner's "отправляй".

**Facts checked 2026-09-30:**
- Upstream main 781b3935d6 (2026-09-29) still registers `server.on("/reset", handleReset);` with no method, at src/web/web.cpp:64.
- handleReset clears NVS "pcmonitor", calls wifiManager.resetSettings() and ESP.restart().
- Private vulnerability reporting is off on the repo (`{"enabled":false}`), and there is no SECURITY.md.
- Our fix is fork commit d84c61c (branch fix/reset-csrf); it goes in with 2.7.9.

The impact is limited to someone who can get a page opened in a browser on the same network. Nothing is read out: the board is wiped and falls back to the setup AP.

## Title

Factory reset (/reset) runs on a plain GET, so any web page can wipe the clock

## Body (English, as it would be posted)

Hi, thanks for the project, I run a fork of it on a Waveshare 128x64 panel.

While testing my build I found that /reset is registered for every HTTP method (src/web/web.cpp, `server.on("/reset", handleReset);`). handleReset clears the settings, resets the Wi-Fi credentials and restarts. So a plain GET is enough, and any page opened in a browser on the same network can do it with one image tag pointing at http://<clock>/reset. No script and no user action are needed; the clock comes back up in the setup AP.

What I changed in my fork, in case it helps:
- /reset is POST only; a GET gets a 405 with a short note.
- The request must be Content-Type application/json with the body {"confirm":"factory-reset"}. A cross-site JSON POST needs a CORS preflight, and the server does not answer OPTIONS, so a browser will not send it from another site.
- When the browser sends an Origin header it must be exactly http://<Host>, and the Host must be an IP address or a .local name. That also covers DNS rebinding.
- The Factory reset button in the portal now does a fetch POST with that body after its two confirm dialogs.

The other GET controls (display off, brightness, reboot) can be triggered the same way, but they do not lose data, so I left them as documented.

I did not see a private way to report this, so I am opening it here. Happy to send a PR.

## Русский перевод (для владельца, не публикуется)

**Заголовок:** Сброс к заводским настройкам (/reset) срабатывает на обычный GET, и любая веб-страница может стереть часы.

Привет, спасибо за проект, я использую его форк на панели Waveshare 128x64.

Проверяя свою сборку, я нашёл, что /reset зарегистрирован на любой HTTP-метод (src/web/web.cpp, `server.on("/reset", handleReset);`). handleReset стирает настройки, сбрасывает Wi-Fi и перезагружает. Значит, хватает обычного GET: любая страница, открытая в браузере в той же сети, делает это одной картинкой с адресом http://<часы>/reset. Скрипт не нужен, действия пользователя тоже; часы поднимаются в точке доступа настройки.

Что я поменял у себя в форке, если пригодится:
- /reset только POST; на GET — 405 с короткой подсказкой.
- Запрос должен быть Content-Type application/json с телом {"confirm":"factory-reset"}. Межсайтовый JSON-POST требует предварительного запроса CORS, а сервер на OPTIONS не отвечает, так что браузер с чужого сайта его не отправит.
- Если браузер шлёт заголовок Origin, он должен быть ровно http://<Host>, а Host — IP-адресом или именем .local. Это закрывает и подмену DNS.
- Кнопка Factory reset в портале после двух подтверждений теперь делает fetch POST с этим телом.

Остальные GET-команды (выключить экран, яркость, перезагрузка) тоже можно вызвать так же, но они не теряют данные, поэтому их я оставил как задокументировано.

Закрытого способа сообщить об уязвимости я не нашёл, поэтому пишу здесь. Могу прислать PR.
