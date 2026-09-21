# Draft: upstream PR 7 to Keralots/AnimatedPixelClock, the link watchdog

**Status: POSTED 2026-09-21 12:43** on the owner's "отправляй":
https://github.com/Keralots/AnimatedPixelClock/pull/10 - head
`NickoScope:fix/link-watchdog-unsent-probe` at `b674699` onto upstream main `1555601`, one
commit, +20 -1 in one file. Rewritten twice before posting at his word ("напиши по человечески
моим языком и чуть короче") - the posted body is about half the first draft. **First PR without
the Claude Code attribution line**, on his instruction of the same day; PRs 1-6 carry it.

## The bug, in his code

`src/network/network.cpp`, the probe result:

```c
} else if (++netProbeFails >= NET_PROBE_FAILS_BEFORE_RECOVERY && !cooling) {
    netRecover("gateway unreachable");
}
```

There is no check that the probe was actually **sent**. When the Wi-Fi driver has no buffer for
the ICMP request, `esp_ping` cannot transmit it, and the silence that follows is indistinguishable
from a gateway that ignored it. `NET_PROBE_FAILS_BEFORE_RECOVERY` is 2, so two in a row restart
the radio.

**The watchdog then becomes the outage it exists to prevent.** The radio was only short of
memory; the restart takes the panel off the network for minutes, and the shortage is still there
when it returns. Nothing exotic is needed to reach that state - a browser holding the
configuration portal open squeezes the internal heap far enough on its own.

## Why it is a real risk for his users, not just for us

Ours is a heavily extended fork, but this needs none of our additions. The ingredients are the
stock portal, the stock watchdog and a browser. Any ESP32 panel that runs low on internal SRAM
while the link is idle can hit it.

Measured on our panel over the cable, 2026-09-20: internal heap down to **2,712 B** with a portal
tab open, the Wi-Fi task failing repeated **1,626 B** DMA allocations, and the watchdog restarting
Wi-Fi **every sixty seconds for seven minutes**. After the fix, the same starvation leaves the link
alone and the panel stays reachable - verified again 2026-09-21 under 250 concurrent requests:
`allocFails` climbed to 133 and `linkRecoveries` stayed at **0**.

## The fix

ESP-IDF already records the distinction and we do not have to infer it. In `ping_sock.c` the
`transmitted++` that feeds `ESP_PING_PROF_REQUEST` sits in the **else** of the send-failure
branch, so a session ending with zero requests transmitted is one where nothing left the board.
Read it in `on_ping_end` and treat that case as "try again later".

20 lines added, 1 changed, one file.

## What is ready

- Worktree `/Users/apple/AnimatedPixelClock-watchdog`, branch `fix/link-watchdog-unsent-probe`
  from `upstream/main` at `1555601`, one commit `b674699`.
- Builds on **his** environment: `pio run -e matrix-s3` → SUCCESS.
- Not pushed to the fork. Not proposed.

## Notes for when it is sent

- His house style, from the six PRs before this: prose rather than bullet lists, the owner's
  voice. **No Claude Code attribution line** - the owner's instruction of 2026-09-21, "убери из
  всех будующих". PRs 1-6 carry it; this one and everything after do not.
- Worth offering alongside, but **not** in the PR - two measurements that cost us days and may
  save him the same:
  - a 128x64 HUB75 panel holds **131,072 B** of DMA framebuffer in internal RAM
    (32 row-pairs x 128 px x 8 bits x 2 bytes, double-buffered), which is where the internal
    heap on these boards actually goes;
  - `largestHeapBlock` does **not** decay over time. It is identical to the byte within one boot
    and varies *between* boots in 1,024-byte steps, one boot in seven landing 6 KB low. Anyone
    tuning memory by comparing two readings is measuring the boot, not the change. Seven boots,
    `tools/nsc/measure/paired.py`.
