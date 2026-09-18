# fx3d on the panel: what it measured, 2026-09-18

Flashed `feat/fx3d` at `264d6f1` (the ordinary build with `-DFX3D_ENABLED`) over the air on the
owner's Waveshare panel after a delta audit of that exact commit came back APPROVED. The USB cable
was not plugged in, so the module's own serial bench could not be read; instead every scene and look
was driven over HTTP - set it, let it settle 8 s, then read `/api/fx3d` (frameUs, blitUs, fps, openUs)
and `/api/info` (heap). 37 samples. `stack_min_free` and `frame_us_max` stay unmeasured until the
cable is back.

## The blit is half the budget

`blitUs` was 14,190-14,890 us for **every** scene and every look, with no exception: pushing 8,192
pixels costs ~14.3 ms. At 30 Hz the whole frame budget is 33,333 us, so 43 % of it is gone before
anything is drawn. That is the number the bench existed to produce, and it is where any headroom has
to come from.

## Scenes

| Scene | mono frame | mono fps | anaglyph frame | anaglyph fps | open |
|---|---|---|---|---|---|
| `cube` | 1,819 us | 30.2 | 4,596 us | 30.3 | 11 us |
| `calib` | 2,502 us | 30.2 | 2,497 us | 30.2 | 8 us |
| `layers` | 2,590 us | 30.3 | 5,689 us | 30.2 | 9 us |
| `stars` | 2,907 us | 29.6 | 6,473 us | 30.3 | 116 us |
| `dial` | 3,055 us | 30.2 | 6,826 us | 30.2 | 11 us |
| `helix` | 3,880 us | 30.2 | 8,002 us | 30.2 | 10 us |
| `rings` | 4,655 us | 30.3 | 9,706 us | 30.2 | 9 us |
| `vclock` | 6,002 us | 30.3 | 12,828 us | 30.2 | 15 us |
| `torus` | 9,760 us | 30.2 | 20,030 us | 27.5 | 135 us |
| `terrain` | 19,751 us | 27.4 | 38,520 us | 18.1 | 71 us |
| `voxel` | 32,751 us | 20.2 | 62,507 us | 12.6 | 1,081,490 us |
| `tunnel` | 34,947 us | 19.4 | 69,274 us | 11.6 | 14 us |
| `globe` | 44,767 us | 16.4 | 88,453 us | 9.5 | 55 us |
| `blobs` | 111,819 us | 7.7 | 217,789 us | 4.2 | 80 us |

Anaglyph costs about twice the render, as two eyes should. Eight scenes hold 30 Hz in both modes.

## Looks (any page in 3D)

| Look | frame | fps |
|---|---|---|
| `wiggle` | 30,220 us | 20.6 |
| `drum` | 32,006 us | 19.7 |
| `float` | 34,804 us | 18.6 |
| `dome` | 37,466 us | 17.8 |
| `pop` | 40,440 us | 16.9 |
| `layers` | 43,885 us | 16.0 |
| `card` | 67,698 us | 11.6 |
| `relief` | 81,425 us | 9.9 |

## What has to change

1. **`blobs` is unusable**: 111,819 us (7.7 fps) mono, 217,789 us (4.2 fps) anaglyph.
2. **`globe`, `tunnel`, `voxel`, `terrain`** fall below 30 Hz in at least one mode.
3. **`voxel` blocks for 1,081,490 us - 1.08 s - while it opens.** Every other scene opens in 8-140 us.
4. **A look costs 10-20 fps**, not 30: `relief` 9.9, `card` 11.6. Clock animations under a look run at
   a third of their speed, not half.
5. **`look=off` is refused** (only `flat` is a look). A walk that sends it leaves the panel in whatever
   look was last set - it left mine in `drum` until I noticed.

## What is already right

- **No leak**: 37 scene switches, free internal heap 31,356-33,248 B, largest block a constant 22,516 B,
  PSRAM 15.95 MB free.
- The 30 Hz ceiling works: the light scenes report 30.2-30.3 fps.
- Scenes open instantly apart from `voxel`.
- `/fx3d` renders and works: glasses, depth, per-eye gain, six calibration steps, every scene and look,
  and a live status line with the frame time and fps.
- The image confirmed itself valid after 60 s; no crash; `scene=off&look=flat` gives the clock back.

Raw data: `27-fx3d-panel-measurements-2026-09-18.json` next to this file.
