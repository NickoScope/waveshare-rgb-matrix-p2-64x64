# fx3d fifth round: the heavy scenes

`6016158` over OTA, 2026-09-20, confirmed `valid` at 67 s before any measurement. By IP,
one request at a time.

| Scene | 80eb788 | **6016158** | gain | fps |
|---|---|---|---|---|
| `tunnel` / mono | 34,960 us | **6,366** | 5.49x | **30.3** |
| `tunnel` / red-blue | 69,372 | **12,044** | 5.76x | **30.3** |
| `globe` / mono | 45,516 | **11,680** | 3.90x | **30.3** |
| `globe` / red-blue | 90,091 | **23,064** | 3.91x | **30.1** |
| `voxel` / mono | 32,827 | **13,306** | 2.47x | **30.3** |
| `voxel` / red-blue | 62,344 | **26,591** | 2.34x | 25.9 |
| `blobs` / mono | 41,743 | **33,455** | 1.25x | 23.5 |
| `blobs` / red-blue | 82,464 | **65,772** | 1.25x | 13.3 |

`voxel` opens in **258,0 ms** mono (was 451,7 / 1,081,5 at the start), and that figure now also
carries the tables, which used to hide in the first frame. `tunnel` opens in 38-76 ms, `globe` in
41-81 ms.

**Where the panel stands now:** every scene but `blobs` holds 30 Hz in mono, and all but `blobs`
and `voxel` hold it with the glasses. Seven of the eight looks are at 30 Hz. `blobs` is the one
scene the sphere-tracing rewrite barely moved (1.25x) and is now the slowest thing on the panel.

Health after the round: free internal heap 31,180 B, largest block 19,444 B, `allocFails` 0.
