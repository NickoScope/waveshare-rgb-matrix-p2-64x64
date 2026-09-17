# Draft: reply on Keralots/AnimatedPixelClock issue #3, after "no new features for now"

**Status: DRAFT, not posted.** Waits for the owner's "отправляй".

- **Answers:** Rafał's comment of 2026-09-17 14:25 UTC,
  https://github.com/Keralots/AnimatedPixelClock/issues/3#issuecomment-5716011106
- **What he said:** no new features in main for now (mic source, eight styles,
  IR remote, SHTC3 all stay in the fork; SHTC3 was interest, not a request).
  The list is unchanged: weather task lifetime, then the crash report half of
  boot_health, then the gzip portal last. The settings fix (isKey() before
  remove() at settings.cpp:889 and :899) is welcome as a small PR, and may go
  before the weather task. He asks for the real idle voltage on IO45 if we
  ever solder a receiver.
- **Voice:** the owner's. Plain, short, no formatting, no long dashes.
- **Before posting:** nothing in it promises a date. If the settings PR is
  already open by then, replace the second paragraph with its link.

---

Hi Rafał,

understood, and thanks for saying it straight. Everything else stays in my fork, and I won't send updates about fork features here unless you ask.

I'll send the settings fix first since it's small, then the weather task lifetime, then the crash report, and the gzip portal last. Same rules as before, one PR per change, all three envs built, matrix-s3 size in the description.

When I solder a receiver to IO45 I'll measure the idle level and post the number here.

Nikolay
