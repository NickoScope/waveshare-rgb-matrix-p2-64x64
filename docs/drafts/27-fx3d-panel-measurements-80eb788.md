# fx3d on the panel, third round: the looks come home

`80eb788` flashed over the air after its delta audit came back APPROVED, then the same HTTP walk
as the two rounds before it - 37 samples, set a scene or a look, let it settle 8 s, read
`/api/fx3d` and `/api/info`. Same panel, same network, same evening. Firmware 2.4.0,
build Sep 18 2026 17:25:46.

The change under test: the extra frame copy the looks were making (`lin_`) is gone, and the looks
now blit through the same run path the scenes already use.

## The question we came to answer

The second round left three looks looking wrong: `wiggle` and `drum` came out *slower* than before
the run blit landed, and `dome` and `relief` barely moved. Here is what the panel says now.

| Look | 264d6f1 | 3d2a1c5 | **80eb788** | fps now | this step |
|---|---|---|---|---|---|
| `relief` | 81,425 us | 79,084 us | **10,972 us** | **30.2** | −86 % |
| `dome` | 37,466 us | 36,194 us | **16,652 us** | **30.2** | −54 % |
| `wiggle` | 30,220 us | 32,630 us | **16,170 us** | **30.3** | −50 % |
| `float` | 34,804 us | 23,520 us | **14,421 us** | **30.2** | −39 % |
| `pop` | 40,440 us | 21,866 us | **14,120 us** | **30.3** | −35 % |
| `layers` | 43,885 us | 16,133 us | **14,567 us** | **30.3** | −10 % |
| `card` | 67,698 us | 48,354 us | **45,963 us** | 17.6 | −5 % |
| `drum` | 32,006 us | 32,625 us | **31,476 us** | 24.1 | −3 % |

**Six of the eight looks now hold the full 30 Hz.** That is the headline: before this build not a
single look reached 30 fps - the best was 22. A page rendered under `pop`, `layers`, `float`,
`dome`, `wiggle` or `relief` now animates at exactly the speed it does flat.

- `wiggle` recovered and then some: 32,630 -> 16,170 us. The second round's regression was the
  extra copy, exactly as suspected.
- `relief` is the surprise - 79,084 -> 10,972 us, 7.2x. It is now the *cheapest* look on the panel.
  The audit had already flagged that `relief` renders differently in this build by design
  (988 pixels flip on or off); the picture needs eyes on it, the clock does not.
- `drum` did **not** recover. 32,625 -> 31,476 us, 3 %. Its blit did fall (9,192 -> 6,514 us), so the
  blit is no longer what costs it - about 25 ms of the 31.5 ms frame is the look's own geometry.
- `card` is now the slowest thing on the panel at 45,963 us / 17.6 fps, and the same story: blit
  7,398 us, so ~38 ms is its own work.

## The blit, per look

This is the measurement that proves what the fix did. The scenes' blit did not move at all between
the second and third rounds - it was already on the run path. The *looks'* blit fell by a quarter:

| | 3d2a1c5 | 80eb788 |
|---|---|---|
| looks, blit | 8,947-9,527 us | **6,514-7,398 us** |
| scenes, blit | 6,323-9,705 us | 6,310-9,750 us (unchanged) |

## Scenes: nothing moved, as intended

All 28 scene samples are within ±1.5 % of the second round, which is the walk's own noise. The one
exception is worth naming:

| Scene | 264d6f1 | 3d2a1c5 | 80eb788 |
|---|---|---|---|
| `vclock / mono` | 6,002 us | 6,415 us | 6,947 us |
| `vclock / redblue` | 12,828 us | 13,484 us | 14,012 us |

`vclock` has crept up 8-9 % over the three rounds, monotonically. The most likely explanation is
not the code: `vclock` draws the current time, the three rounds were taken hours apart, and a
different set of digits is a different number of lit voxels. It costs nothing at 30.3 fps either
way, but it is the one number in this table we cannot yet explain from the diff, so it is written
down rather than waved away. To settle it, one measurement of `vclock` twice within the same
minute would do.

`voxel` still opens in 453,060 us (451,675 in the second round) - the 0.45 s pause is untouched.

## Health

| | 264d6f1 | 3d2a1c5 | 80eb788 |
|---|---|---|---|
| free internal heap, over the walk | 31,392-33,248 B | 30,760-32,868 B | 30,956-32,852 B |
| largest free block, low water | 22,516 B | 18,420 B | **14,836 B** |

Free heap is flat across all three builds. The largest *contiguous* free block is not: it dipped to
14,836 B during `blobs / redblue` and `globe / redblue`, lower than either earlier round. After the
walk `/api/info` reports it back at 23,540 B, `allocFails` 0, `minFreeHeap` 14,596 B, uptime 548 s,
no crash and no reboot (`lastCrash.thisBoot` false), OTA partition `app0` state `valid`,
`loopMaxMs` 5 with the slow part `render` at 3 ms.

So: transient, recovered, nothing failed to allocate. But on a board with ~33 KB of internal heap
this is the number that decides whether a web request can be served while the effect runs, and it
is drifting down build over build. **Watch item, not a blocker**: worth a look at which buffer the
anaglyph path takes and gives back per frame.

## Verdict

The fix did what it said and more. Six looks at 30 fps, no scene regressed, no memory lost, the
panel is healthy after the walk. What is left, in order: `card` at 17.6 fps, `drum` at 24.1 fps,
`voxel`'s 0.45 s open, the contiguous-block drift, and one unexplained 9 % on `vclock`.

Raw data: `27-fx3d-panel-measurements-80eb788.json`; the two earlier rounds are in the files
beside it.
