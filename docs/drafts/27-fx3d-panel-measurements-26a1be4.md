# fx3d sixth round: blobs and globe, and a question about the looks

`26a1be4` over OTA, 2026-09-20, confirmed `valid` at 67 s. By IP, one request at a time.

| | previous round | **26a1be4** | gain | fps |
|---|---|---|---|---|
| `blobs` / mono | 33,455 us | **26,835** | 1.25x | 28.0 |
| `blobs` / red-blue | 65,772 | **52,566** | 1.25x | 16.2 |
| `globe` / mono | 11,680 | **9,783** | 1.19x | 30.2 |
| `globe` / red-blue | 23,064 | **19,232** | 1.20x | 30.3 |
| look `pop` | 14,120 | 21,493 | **0.66x** | 30.2 |
| look `wiggle` | 16,170 | 21,757 | **0.74x** | 30.2 |

`blobs` is 1.25x again and `globe` 1.2x - both real. Cumulatively `blobs` is now 1.56x cheaper than
`80eb788` and still the slowest scene: 28.0 fps mono, 16.2 with the glasses.

**The two looks came out slower, and this is not yet a regression.** A look renders whatever page
is underneath it, and no round has ever pinned that page - the panel cycles its pages on its own.
So the 0.66x may be a different page, not different code, especially as the change here only
removed work. Both still hold 30.2 fps, so nothing is broken either way. To settle it: measure a
look twice with the same page fixed underneath, before and after.

**This round went without a fresh audit** - the feature session stopped running them to save the
owner's budget, and the change is host-verified byte-identical in output. Said plainly rather than
left implied.

Health: free internal heap 31,200 B, largest block 19,444 B, `allocFails` 0.
