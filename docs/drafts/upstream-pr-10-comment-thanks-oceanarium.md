# Comment on Keralots/AnimatedPixelClock#10: thanks for v2.3.2, and the Oceanarium (draft)

Status: POSTED 2026-09-24 21:56 on the owner's "отправляй на английском": https://github.com/Keralots/AnimatedPixelClock/pull/10#issuecomment-5821208488

**Where:** https://github.com/Keralots/AnimatedPixelClock/pull/10.
- It is the PR he merged today, and a comment on it reaches him.
- Issue #3 is closed, and a new issue would sit in his tracker as work.
- Discussions are off.

**Why nothing is asked:** on 2026-09-17 he wrote that new features stay in the fork and called Lua "a different product built on the same base". So this is a thank-you and a show-and-tell. It offers no PR and says no answer is needed.

**Facts checked, 2026-09-24:**
- **PR #10:** merged 16:38:16 UTC by Keralots.
- **v2.3.2:** published 16:51:22 UTC. It ships #4-#10 (all seven of ours were merged: #4 on 09-15, #5-#8 on 09-17, #9 on 09-18, #10 today). Its notes end with "Thanks to @NickoScope for contributing."
- **His panel:** the one-piece 128x64 panel he wrote about on #2 on 2026-09-23 arrived with broken corner LEDs.
- **The Oceanarium:**
  - 119 kinds of sea life;
  - measured on the owner's Waveshare panel: 14.8-15.2 fps, 37-47 ms a frame;
  - about 45,000 Lua instructions a frame by day;
  - the script is 134 KB;
  - the sprite helpers px.grab and px.blit came in fork release v2.7.3.
- **The presentation page:** https://nickoscope.github.io/AnimatedPixelClock/oceanarium/en.html answers 200.

## Body (English, as it would be posted)

Hi Rafał,

thank you for merging this one, and for v2.3.2. I saw all seven PRs went out in it, and the thanks at the end of the release notes made my day. Working with you on them was a real pleasure: every one was merged the same day, with no back and forth.

And, as before with nothing to merge and no need to answer, one more thing from the fork that I think you might enjoy. I'm sorry to read about your new panel arriving with the corners broken. It is exactly this 128x64 size that the Oceanarium is made for.

The Oceanarium is a Lua effect: a window into a big public aquarium, with 119 kinds of sea life living on their own in it. There is no scene playing on a loop. Every fish, shark, ray, jelly or turtle is its own little agent that decides where to go, keeps to its own part of the tank, hides from the sharks and leaves when it wants to. Nothing on screen is a bitmap. Each animal is drawn from a description (a body shape, colours, a pattern, fins, a tail), once per pose. The fork's firmware then cuts the pose out as a sprite and stamps it every frame, mirrored when the animal turns and hazed toward the water colour by its distance. The light follows the panel's clock from noon through a violet dusk to a dark night with glowing jellies. With a presence radar in the room, the curious fish come to the glass where you stand. On the Waveshare board it runs at 15 fps, about 45,000 Lua instructions a frame.

I made a short page about it, with the tank running and the numbers from the panel:
https://nickoscope.github.io/AnimatedPixelClock/oceanarium/en.html

Thanks again,
Nikolay

## Русский перевод (для владельца, не публикуется)

Привет, Рафал,

спасибо, что влил этот PR, и за v2.3.2. Я увидел, что в неё вошли все семь PR, а благодарность в конце описания выпуска меня очень порадовала. Работать с тобой над ними было настоящим удовольствием: каждый влит в тот же день, без лишних кругов.

И, как и в прошлый раз, без просьб и без необходимости отвечать, ещё одна вещь из форка, которая, думаю, тебе понравится. Жаль, что твоя новая панель пришла с отбитыми углами. Океанариум сделан именно под такой размер, 128x64.

Океанариум — это Lua-эффект: окно в большой океанариум, где своей жизнью живут 119 видов морских обитателей. Никакой сцены по кругу там нет. Каждая рыба, акула, скат, медуза или черепаха — свой маленький агент: сама решает, куда плыть, держится своей части аквариума, прячется от акул и уплывает, когда хочет. На экране нет ни одной готовой картинки. Каждое животное рисуется по описанию (форма тела, окраска, узор, плавники, хвост), по одному разу на позу. Потом прошивка форка вырезает позу как штамп и ставит её каждый кадр: зеркально, когда животное разворачивается, и с дымкой воды по расстоянию. Свет идёт по часам панели: от полудня через фиолетовые сумерки до тёмной ночи со светящимися медузами. Если в комнате есть радар присутствия, любопытные рыбы подплывают к стеклу туда, где ты стоишь. На плате Waveshare он идёт 15 кадров в секунду, около 45 000 команд Lua на кадр.

Я сделал про него небольшую страницу, с живым аквариумом и цифрами с панели:
https://nickoscope.github.io/AnimatedPixelClock/oceanarium/en.html

Ещё раз спасибо,
Николай
