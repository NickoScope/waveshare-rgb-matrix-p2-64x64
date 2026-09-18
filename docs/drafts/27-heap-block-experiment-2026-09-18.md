# What starves the panel's internal heap: the experiment, and the incident it caused

2026-09-18, 19:44-20:05, firmware 2.4.0 `80eb788`, panel at 192.168.4.62.

The third fx3d round left a watch item: the largest contiguous free block in internal RAM dipped to
14,836 B during the walk (22,516 in the first round, 18,420 in the second), with free heap flat and
`allocFails` 0. The fx3d session's hypothesis was that the block falls because a heavy anaglyph
scene holds `loop()` for 80-90 ms and the network's buffers queue in internal RAM behind it - and
that it would therefore fall *without any traffic at all*.

It does not. The experiment says something narrower, and then it went further than intended.

## What was measured

All figures are the panel's own counters from `/api/info`. One condition at a time, same scene
(`blobs`, red-blue - the most expensive frame we have at 82 ms), same evening, no reflash.

| Condition | largest free block | min free heap ever | allocFails | loopMaxMs |
|---|---|---|---|---|
| clock, idle | 23,540 B | 14,596 B | 0 | 5 |
| `blobs`/red-blue, 30 s, **not one request** | 23,540 B | 14,596 B | 0 | 98 |
| `blobs`/red-blue, 30 requests, one a second | 23,540 B | 14,596 B | 0 | 97 |
| `blobs`/red-blue, 20 x **two requests back to back** | **21,492 B** | 13,752 B | 0 | 105 |
| + 10 x two requests **at the same time** | 21,492 B | 13,708 B | 0 | 100 |
| + 5 x **four at the same time** | **20,468 B** | 12,752 B | 0 | 103 |
| back to the clock, 8 s | 20,468 B | 12,752 B | 0 | 93 |
| the clock, three minutes later | 20,468 B | 12,752 B | 0 | 7 |

Three things fall out of that table.

1. **A heavy frame on its own costs nothing.** 30 s of the worst scene we have, with the loop at
   98 ms and no traffic, left every memory figure untouched. The hypothesis is disproved.
2. **Traffic on its own costs nothing either** - as long as one request finishes before the next
   begins. Thirty sequential requests under the same scene: unchanged.
3. **What costs is overlap.** Requests that arrive before the previous one is served step the block
   down, and it **does not come back**: 23,540 -> 21,492 -> 20,468, still 20,468 three minutes later
   on an idle clock. A ratchet, not a dip.

That also explains the walk: each of its 37 samples asked `/api/fx3d` and `/api/info` back to back.

## Then the panel went off the network

Continuing to measure - on the clock, no scene, `loopMaxMs` 7 - the panel stopped answering:
100 % packet loss for about 25-30 seconds, the name gone from mDNS. It came back on its own and
reported what had happened:

```
uptime 1642 s (continuous - no reboot, no crash)
minFreeHeap    1,648 B      (was 12,752 B before this)
allocFails     7
allocFailBytes 314
allocFailTask  "wifi"
linkRecoveries 1, lastLinkRecovery "gateway unreachable"
ota            app0, state valid
```

So: internal free heap fell to **1.6 KB**, seven allocations of **314 bytes in the Wi-Fi task**
failed, the link died, and the firmware's own recovery reconnected it. The display never stopped,
the firmware never rebooted, the OTA image stayed valid, and the clock was on screen throughout.
Nothing was lost. But the panel was unreachable for half a minute because it ran out of internal
memory, and the thing that could not get its 314 bytes was the radio.

**The honest caveat.** RSSI fell from −61 to −72...−74 dBm across the same window, so the radio
environment changed too, and one run cannot separate the two causes. What is not ambiguous is the
panel's own record: `allocFails` went 0 -> 7, the failing task was `wifi`, and the failing size was
314 B. Whatever else was happening in the air, the panel was out of internal heap.

## What this means for us

The panel has about 33 KB of internal heap, and the Wi-Fi task needs small buffers out of it
continuously. A render tick that blocks for ~100 ms, plus several HTTP connections open at once, is
enough to starve it. This is **ours, not fx3d's**: fx3d only makes it reachable, and the same recipe
exists wherever a page is slow. It belongs next to the known audio D1 portal heap spike.

Directions, none of them taken yet:

- cap the cost of the heavy anaglyph scenes, so no tick blocks for 100 ms (the fx3d session's list
  already has this as item 3);
- refuse or queue overlapping HTTP connections rather than serving them concurrently out of the
  same heap;
- keep a reserve of internal RAM the web path may not touch, so the radio's 314 bytes always exist.

## Two working notes

- **Use the IP, not the name, when measuring.** `NickoScope-64x128.local` costs **5.0 s of name
  lookup per request** on this Mac (`time_namelookup` 5.006 s by name, 0.0008 s by IP; the panel
  itself answered in 47 ms). Every walk we have run paid that 5 s a sample. It does not touch the
  frame times - those are the panel's own counters - but it stretched each walk and the panel's
  exposure by minutes.
- The panel's Wi-Fi link recovery works, and this is the first time we have seen it fire in anger:
  `lastLinkRecovery` "gateway unreachable", one recovery, back in ~25 s without help.
