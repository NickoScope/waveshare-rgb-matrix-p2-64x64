# Draft: closing note on Keralots/AnimatedPixelClock issue #3, after he closed it

**Status: DRAFT, not posted. Optional - nothing is owed here.** Waits for the
owner's "отправляй".

- **Answers:** the closing of issue #3,
  https://github.com/Keralots/AnimatedPixelClock/issues/3 - closed as
  completed 2026-09-18 20:36:32 UTC, two seconds after PR #9 was merged, with
  no closing comment.
- **What happened:** his list is done. Six PRs offered, six merged, not one
  review comment: #4 TLS buffers in PSRAM, #5 the settings `isKey()` fix, #6
  the weather fetch task, #7 the crash report in `/api/info`, #8 the crash
  cause name kept across a firmware update, #9 the gzip portal. Release is
  still v2.3.1, so none of them has shipped to users.
- **What he still has open with us, from his own words:** the measured idle
  level on IO45 once a receiver is soldered - he said he would put the number
  in the hardware notes with the owner's name. That is the only thing he asked
  for. Everything else (mic source, eight styles, IR remote, SHTC3) stays in
  the fork by his decision of 2026-09-17, and he asked not to be sent fork
  updates unless he asks.
- **Voice:** the owner's. Plain, short, no formatting, no long dashes.
- **Before posting:** the closed issue does not need an answer. Post this only
  if the owner wants the thread to end with a word from our side. If the
  receiver is soldered by then, the voltage belongs in its own comment
  instead, which is the one he actually asked for.

---

Hi Rafał,

I see #3 is closed and all six are in. Thanks for taking them at that speed, and for being clear about what you did not want - that made the whole thing easy.

Two notes and then I will leave the thread alone.

The portal generator is `tools/web_assets_gen.py` and the staleness check is `tools/web_assets_check.py`, which runs as a pre-build step and fails the build if `src/web/web_assets.h` no longer matches the sources. I saw you pinned that header to LF in .gitattributes right after the merge, so I assume the check caught it on Windows. If it ever fails for a reason that is not a stale header, tell me and I will fix it.

The IO45 idle level is still owed. I have not soldered a receiver yet. When I do you get the number here.

Nikolay
