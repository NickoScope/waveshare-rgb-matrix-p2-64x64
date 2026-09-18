# fx3d fourth round: the profile survives a reboot, card and drum come home

`0f3b2c7` over OTA, 2026-09-18 21:18. Measured by IP (not the mDNS name - that costs 5 s a request
on this Mac), one request at a time.

## The glasses profile in NVS - all four steps pass

| Step | Result |
|---|---|
| set depth 3.37 px | `profile` goes `pending`, then `kept` after the settle |
| reboot | depth **3.37 px** came back |
| set red-cyan, swap, left eye 80 % | `pending` -> `kept` |
| reboot | red-cyan, swap, 80/100 **all came back** |
| `profile=reset` | defaults at once |
| reboot | defaults held |

**The write's cost:** it never became the slowest part of a loop pass in any 10 s window containing
a write, while the ordinary worst part was the web server at 10 ms. So the write is **under 10 ms**;
a finer figure needs serial, and no USB cable is attached. `allocFails` stayed 0 throughout.

## card and drum

| Look | 80eb788 | **0f3b2c7** | fps |
|---|---|---|---|
| `drum` / red-blue | 31,476 us | **15,533 us** | 24.1 -> **30.3** |
| `card` / red-blue | 45,963 us | **26,363 us** | 17.6 -> **26.3** |
| `drum` / mono | - | 7,934 us | 30.3 |
| `card` / mono | - | 13,604 us | 26.7 |

`drum` doubled and now holds the full rate. `card` is 1.74x and no longer the panel's worst frame.
**Seven of the eight looks are at 30 Hz; `card` alone is short, at 26.3.**

## The rollback fired, and it was my mistake

The first flash of this image was lost: the test rebooted the panel at about 45 s of uptime, before
the new image had confirmed itself at 60 s, so the bootloader rolled back - `/api/info` reported
`rolledBackFrom: app1` and the old build. Nothing was harmed and the panel stayed up; the guard did
exactly its job, and this is the first time we have seen it fire in anger. **The rule that follows:
after an OTA, wait for `ota.state` to read `valid` before any reboot.** The second flash, waited out
and confirmed at 64 s, is the one measured above.
