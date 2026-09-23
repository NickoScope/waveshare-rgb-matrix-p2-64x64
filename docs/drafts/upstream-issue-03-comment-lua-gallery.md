# Comment on Keralots/AnimatedPixelClock#3: showing the Lua effects and the gallery (draft)

Status: DRAFT. It is posted only on the owner's "отправляй".

Where: https://github.com/Keralots/AnimatedPixelClock/issues/3. Rafał closed
it as completed on 2026-09-18; a comment on it still reaches him.

Why there, and why nothing is asked:
- The repository has Discussions turned off, and a new issue would sit in his
  tracker as work.
- On 2026-09-17 he wrote that new features stay in the fork, and that Lua in
  particular is "a different product built on the same base, and a good one".
  He also thanked us for always asking first.

So the comment is only a show-and-tell. It asks for nothing, offers no PR, and
says no reply is needed.

Facts checked:
- **Release v2.5.7:** published today.
- **raw.githubusercontent.com CORS:** answers `*`, measured 2026-09-23.
- **The switch:** kept by name in NVS; a stale name gets 409 (the panel
  self-test).
- **Nine gallery screens:** gallery/index.json on main.
- **The agent:** on nickol, no GitHub write access. Every key there was
  checked against GitHub on 2026-09-23, and there are no tokens. Its entries
  are checked again and pushed by the maintainer's `sync`.
- **Checks available to the agent:** the panel's own validator compiled for
  the host (tools/luasim/validate.py) and the host simulator (luasim).

## Body (English, as it would be posted)

Hi Rafał,

no request in this one and nothing to merge. You wrote that the fork reads like a different product built on the same base, and I wanted to show you one piece of it that turned out better than I expected. Only if you have a spare minute.

It is the Lua effects in the portal. Every effect has its own switch for whether the knob and the carousel visit it, the uploaded ones can be deleted, and an "Add from the gallery" list shows the scripts in the fork's gallery folder with a preview and sends the one you pick to the panel. The browser fetches the script from raw.githubusercontent.com, which answers any origin, and posts it to the panel, so the panel itself never goes to the internet for it. The switches are kept in NVS by effect name rather than by index, so uploads and deletes do not shift them, and each click carries the name it saw, so if the list changed in between the panel answers 409 instead of switching the neighbour.

The part I enjoy most is where the gallery screens come from. An agent on a Raspberry Pi here writes new screens against a host build of the same Lua runtime, checks them with the panel's own validator compiled for the host, and publishes them into a branch on its own machine. It has no write access to GitHub. Every evening my Mac takes only its gallery entries from that branch, runs every check again, renders the previews itself and pushes them. There are nine screens now, among them a flip-disc clock and the sea at sunset.

Release: https://github.com/NickoScope/AnimatedPixelClock/releases/tag/v2.5.7
Gallery: https://github.com/NickoScope/AnimatedPixelClock/tree/main/gallery

As agreed, it all stays in the fork, and there is no need to answer.

BR
Nikolay

## Русский перевод (для владельца, не публикуется)

Привет, Рафал,

в этот раз никаких просьб и ничего для слияния. Ты писал, что форк выглядит как другой продукт на той же основе, и мне захотелось показать тебе одну его часть, которая получилась лучше, чем я ожидал. Только если найдётся свободная минута.

Это Lua-эффекты в портале. У каждого эффекта свой переключатель: заходят ли на него ручка и карусель. Загруженные можно удалять. А список «Add from the gallery» показывает скрипты из папки gallery форка с превью и отправляет выбранный на панель. Скрипт загружает браузер с raw.githubusercontent.com, который отвечает любому источнику, и передаёт панели, так что сама панель за ним в интернет не ходит. Переключатели хранятся в NVS по имени эффекта, а не по номеру, поэтому загрузки и удаления их не сдвигают. Каждый клик несёт имя, которое видел, и если список за это время изменился, панель отвечает 409, а не переключает соседа.

Больше всего мне нравится, откуда берутся экраны галереи. Агент на Raspberry Pi здесь пишет новые экраны под хост-сборку того же Lua-рантайма, проверяет их собственным валидатором панели, собранным для хоста, и публикует в ветку на своей же машине. Права на запись в GitHub у него нет. Каждый вечер мой Mac забирает из этой ветки только его записи галереи, заново прогоняет все проверки, сам делает превью и пушит. Экранов уже девять, среди них часы из переворачивающихся дисков и море на закате.

Релиз: https://github.com/NickoScope/AnimatedPixelClock/releases/tag/v2.5.7
Галерея: https://github.com/NickoScope/AnimatedPixelClock/tree/main/gallery

Как договаривались, всё остаётся в форке, и отвечать не нужно.

С уважением,
Николай
