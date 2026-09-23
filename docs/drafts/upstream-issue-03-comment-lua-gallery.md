# Comment on Keralots/AnimatedPixelClock#3: showing the Lua effects and the gallery (draft)

Status: POSTED 2026-09-23 19:47 on the owner's "рафалю отправляй": https://github.com/Keralots/AnimatedPixelClock/issues/3#issuecomment-5799935344

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

Rewritten 19:45 on the owner's correction: the point is the SDK (any AI agent
writes its own effects and puts them on its own panel) and our gallery that
anyone can load and propose to. The Raspberry Pi agent is another story and is
left out.

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

no request in this one and nothing to merge, just something from the fork I think you might enjoy seeing.

The fork now has an SDK for Lua effects: an MCP server and a few command line tools in tools/agent. With it any AI agent can write effects by itself. It reads what a script may call, writes the script, checks it against the panel's own rules, previews it in a simulator of the same runtime with no hardware at all, and puts it on the panel over Wi-Fi in about a second, with no build and no flash.

Around that we started a gallery of effects. In the portal, "Add from the gallery" lists them with a preview and puts the one you pick on your panel, and every effect has its own switch for whether the knob and the carousel visit it. There are nine so far, among them a flip-disc clock, the sea at sunset and an aquarium whose fish notice people in the room. Anyone can load them, and anyone who makes something really beautiful can send it to us as a pull request to the gallery folder.

Release: https://github.com/NickoScope/AnimatedPixelClock/releases/tag/v2.5.7
Gallery: https://github.com/NickoScope/AnimatedPixelClock/tree/main/gallery
SDK: https://github.com/NickoScope/AnimatedPixelClock/tree/main/tools/agent

As agreed, it all stays in the fork, and there is no need to answer.

BR
Nikolay

## Русский перевод (для владельца, не публикуется)

Привет, Рафал,

в этот раз никаких просьб и ничего для слияния, просто хочу показать кое-что из форка, думаю, тебе будет интересно.

В форке теперь есть SDK для Lua-эффектов: MCP-сервер и несколько утилит командной строки в tools/agent. С ним любой ИИ-агент может сам писать эффекты. Он узнаёт, что скрипту можно вызывать, пишет скрипт, проверяет его правилами самой панели, смотрит результат в симуляторе того же рантайма вообще без железа и ставит на панель по Wi-Fi примерно за секунду, без сборки и прошивки.

Вокруг этого мы начали собирать галерею эффектов. В портале «Add from the gallery» показывает их с превью и ставит выбранный на твою панель, а у каждого эффекта есть свой переключатель: заходят ли на него ручка и карусель. Пока их девять, среди них часы из переворачивающихся дисков, море на закате и аквариум, рыбы в котором замечают людей в комнате. Загрузить их может любой, а кто сделает что-то действительно красивое, может прислать нам пул-реквестом в папку gallery.

Релиз: https://github.com/NickoScope/AnimatedPixelClock/releases/tag/v2.5.7
Галерея: https://github.com/NickoScope/AnimatedPixelClock/tree/main/gallery
SDK: https://github.com/NickoScope/AnimatedPixelClock/tree/main/tools/agent

Как договаривались, всё остаётся в форке, и отвечать не нужно.

С уважением,
Николай
