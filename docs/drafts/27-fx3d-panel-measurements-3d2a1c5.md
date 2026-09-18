# fx3d on the panel, second round: what the three fixes bought

`3d2a1c5` flashed over the air after its delta audits came back APPROVED, then the same HTTP walk
as the first round - 37 samples, set a scene, let it settle 8 s, read `/api/fx3d` and `/api/info`.
First round was `264d6f1`; the numbers below are the same panel, same network, an hour apart.

## The blit, which was the point

| | 264d6f1 | 3d2a1c5 |
|---|---|---|
| blit, light scenes | ~14,300 us | **6,300-7,200 us** |
| blit, busy scenes (voxel, tunnel) | ~14,350 us | **9,270-9,705 us** |

The run blit halves the cost on ordinary frames and is still well ahead on the busiest ones - the
case the feature session worried would come out slower than the pixel path did not happen.
At 30 Hz the blit now takes 19-29 % of the frame budget instead of 43 %.

## Scenes that changed

| Scene | frame before | after | fps before | after |
|---|---|---|---|---|
| `blobs / mono` | 111,819 us | 41,673 us | 7.7 | **19.7** |
| `blobs / redblue` | 217,789 us | 82,208 us | 4.2 | **10.9** |
| `terrain / mono` | 19,751 us | 20,019 us | 27.4 | **30.2** |
| `torus / redblue` | 20,030 us | 19,980 us | 27.5 | **30.3** |
| `voxel / mono` | 32,751 us | 32,765 us | 20.2 | **22.4** |
| `tunnel / mono` | 34,947 us | 35,050 us | 19.4 | **21.5** |
| `globe / mono` | 44,767 us | 44,980 us | 16.4 | **18.1** |
| `voxel / redblue` | 62,507 us | 62,490 us | 12.6 | **13.4** |
| `tunnel / redblue` | 69,274 us | 69,181 us | 11.6 | **12.6** |

`blobs` is 2.7x cheaper in both modes: 7.7 -> 19.7 fps mono, 4.2 -> 10.9 anaglyph. The rest kept
their render cost and gained fps purely from the blit.

`voxel` opens in 451,675 us instead of 1,081,490 - 2.4x faster, still a visible 0.45 s pause.

## Looks

| Look | frame before | after | gain | fps after |
|---|---|---|---|---|
| `relief` | 81,425 us | 79,084 us | 1.03x | 10.8 |
| `card` | 67,698 us | 48,354 us | 1.40x | 16.2 |
| `layers` | 43,885 us | 16,133 us | 2.72x | 19.9 |
| `pop` | 40,440 us | 21,866 us | 1.85x | 20.0 |
| `dome` | 37,466 us | 36,194 us | 1.04x | 19.9 |
| `float` | 34,804 us | 23,520 us | 1.48x | 19.9 |
| `drum` | 32,006 us | 32,625 us | 0.98x | 21.9 |
| `wiggle` | 30,220 us | 32,630 us | 0.93x | 21.7 |

`layers` 2.7x, `pop` 1.9x, `float` 1.5x, `card` 1.4x. But `dome` and `relief` barely moved (1.03-1.04x),
and `wiggle` and `drum` came out slightly **slower** (0.93x, 0.98x) - they pay the run scan without
gaining from the band sort. Every look still runs at 10-22 fps, so a clock animation under a look is
still slower than on its own.

## Health

Free internal heap 30,968 B after the walk (31,356 before the round), largest block 18,420 B
(22,516 before - the new static buffers), PSRAM 15.64 MB free. No crash, no reboot, the image
confirmed itself valid, and `scene=off&look=flat` gives the clock back.

Raw data: `27-fx3d-panel-measurements-3d2a1c5.json`; the first round is in the file next to it.
