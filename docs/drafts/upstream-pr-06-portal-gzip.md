# Draft: upstream PR 6 to Keralots/AnimatedPixelClock, the lighter portal

**Status: NOT POSTED.** Written 2026-09-18 at the owner's "запускай" and "сделай полностью".
The last item in Rafał's own order (issue #3, comment 5682483397: "Lighter portal - yes, most
interesting item on the list ... Please send it last"). Goes nowhere until the owner says
"отправляй".

## What he asked for, in his words

- The prize: he measured his own literals - 76,552 B of HTML, 23,290 of CSS, 44,256 of JS,
  144,451 total, "gzipping to 32,956. That is about 109KiB of flash, taking `matrix-s3` from
  82.6% to roughly 77%."
- He accepts the consequence: "`streamTemplate()` goes and the values move to JSON."
- Two requests: **include the generator**, and **a way to fail loudly when the generated header
  goes stale**, "since a binary blob in git that silently disagrees with its source is a nasty
  trap for whoever edits the CSS next".

## What is ready

- Branch `perf/portal-gzip` (pushed to the fork, not proposed), from `upstream/main` at `517b37d`.
- Two commits:
  - `29646e6` `perf(web): serve the portal's CSS, JS and icon gzipped` - the mechanical half;
  - `5898d8a` `perf(web): make the page static and fetch its values as JSON` - the page.
- New files: `tools/web_assets_gen.py`, `tools/web_assets_check.py`, `src/web/web_assets.h`
  (generated). Changed: `src/web/web.cpp`, `src/web/web.h`, `src/web/web_pages.h`,
  `platformio.ini` (one `extra_scripts` line).
- Worktree: `/Users/apple/AnimatedPixelClock-portal`.

## The numbers

| | source | gzip | |
|---|---|---|---|
| `/` (the page) | 72,701 | 12,060 | 16 % |
| `/portal.css` | 23,290 | 5,605 | 24 % |
| `/portal.js` | 48,732 | 15,124 | 31 % |
| `/favicon.svg` | 353 | 176 | 49 % |
| **together** | | **32,965** | his prediction: 32,956 |

| Build | main `517b37d` | this branch | |
|---|---|---|---|
| matrix-s3 | 1,629,585 (82.9 %) | **1,496,373 (76.1 %)** | −133,212 |
| matrix-s3-wroom | 1,644,465 (25.1 %) | 1,511,185 (23.1 %) | −133,280 |
| matrix-waveshare | 1,632,393 (34.6 %) | 1,499,205 (31.8 %) | −133,188 |

RAM is unchanged on all three. His estimate was "roughly 77%"; it lands at 76.1 %.

## How the page gets its values now

`GET /api/portal` returns the identity, the timezone regions, the colour tables the Colors cards
are built from, and a `form` object whose keys are the form control names - the same names
`handleSave()` reads back. 111 keys; 99 of them were derived mechanically from the old
`resolvePlaceholder()` and cross-checked against `handleSave()`, the rest (times, hour lists,
timezone, scope trail, the visualizer list) by hand.

The generator refuses to write a header when the page still has a `%TOKEN%`, or when a named
control in the settings form has no key in `handlePortalValues()` - that control would show its
HTML default and Save would write it back. **It caught one while this was written** (`resetScope`,
which turned out to be a one-shot action rather than a setting, and is now listed as such).

## Audits

| Commit | Verdict | What it found |
|---|---|---|
| `29646e6` | APPROVED | 4 MINOR, all taken: the generator would have written CRLF on Windows (his `upload_port` is `COM9`), the hook blocked `pio run -t clean`, a dead parser branch, and the stale-header message named `python3` rather than the interpreter the build uses |
| `5898d8a` (before the fixes) | CHANGES-REQUIRED | **1 BLOCKER**: the layout editor was built from `/metrics`, which answers before `/api/portal`, so it used row mode 0's geometry and a metric outside that grid fell back to "None" - which Save would write back. **2 MAJOR**: the Static IP card never opened (one toggle of eight not deferred), and `/api/portal` bypassed `sendJsonGuarded()`. **1 MEDIUM**: ~15-19 KB heap peak with the document and the string alive together. All fixed; the MINOR comment rot was fixed too |

## Checked in a browser, not only built

The generated page was served locally with a stand-in `/api/portal` (same keys, values chosen to
be visible) and driven in a real browser:

| Check | Result |
|---|---|
| Values land on the right controls | clock style Tetris, its subcard and its colour block shown, digit row for style 8 |
| Row mode 3 | editor builds three cells; three metrics keep bar positions 0, 1, 2 |
| Static IP card | opens with `useStaticIP=1` (the MAJOR the audit found) |
| Lists built in the browser | timezone 7 + placeholder, selected Asia/Tokyo; hours 24; trail 5 |
| Colours | 9 pickers built from the tables |
| Sliders | read-outs formatted, `min` applied before `value` |
| Rotation editor | six rows from `cycleConfig` |
| Form state | stays "All saved" while it fills; Save enabled only after the values are in |
| Console | no errors |

## On the panel, both versions, same board and network

Flashed over the air on the owner's Waveshare board on 2026-09-18: first this branch, then
upstream main `517b37d` for the comparison, then the fork back.

| Request | main `517b37d` | this branch |
|---|---|---|
| `/` | 93,167 B, 0.222 s (0.213 s warm) | **12,060 B, 0.059 s** |
| `/portal.css` | 23,290 B, 0.071 s | **5,605 B, 0.025 s** |
| `/portal.js` | 44,256 B, 0.179 s (0.101 s warm) | **15,252 B, 0.061 s** |
| `/api/portal` | - | 6,561 B, 0.043 s |
| **a full first load** | **160,713 B, ~0.47 s** | **39,478 B, ~0.19 s** |

The page is 93,167 B on main and 72,701 B in the repository: the difference is what the template
used to write into it on every load. A reload now costs a 304 and nothing else - the ETag was
checked on the device (`If-None-Match` -> `304 Not Modified`).

Headers off the device: `Content-Encoding: gzip`, `Content-Length: 12060`, `Cache-Control:
no-cache` on the page; the assets keep `immutable`.

The portal itself, opened in a browser against the panel with its real settings: version v2.3.1 in
the topbar and the title, device name NickoScope-64x128, 57 timezone regions with the owner's
selected, weather coordinates, dim start 22:00, ambient start 20, the Mario subcard shown for
clock style 0, 69 colour pickers built from the tables, 15 rotation rows, 10 drop cells for row
mode 0, save button enabled, "All saved", no console errors.

The fork was flashed back afterwards and confirmed itself valid.

## English (to post)

Title:

```text
perf(web): serve the portal gzipped and fetch its values as JSON
```

Body:

```text
This is item 6 from #3, the lighter portal. Two commits: the mechanical half first, then the page.

What it does. tools/web_assets_gen.py gzips the page, the style, the script and the icon into src/web/web_assets.h at build time, and the panel sends those bytes with Content-Encoding: gzip. To make the page gzippable it had to become the same bytes for every browser, so the 232 %TOKEN%s are gone: everything they carried now comes from one GET /api/portal, and the page fills itself from it. streamTemplate(), resolvePlaceholder() and the four HTML-building helpers are gone with them, 460 lines.

The JSON is keyed by your own names. "form" holds one entry per control, keyed by the control's name attribute - the same names handleSave() reads back, so the round trip stays in one vocabulary. Next to it: the firmware identity, the timezone regions, and the tables the Colors cards are built from, which the page now builds in JS instead of buildColorsCard() building them in C++.

Your two conditions:

1. The generator is in the PR, and the sources stay where they are - the raw strings in web_pages.h. Editing the portal does not change.
2. A stale header fails the build. platformio.ini gains one extra_scripts line that runs the generator with --check before every build; `pio run -t clean` is deliberately left alone. It looks like this:

web_assets_gen: src/web/web_assets.h is stale - run `.../python tools/web_assets_gen.py` and commit the result.

The generator also refuses two things that would ship a page that cannot work: a %TOKEN% left in the page, and a named control in the settings form that handlePortalValues() does not fill - that control would show its HTML default and Save would write it back. That check caught one while I was writing this (resetScope, which turned out to be a one-shot action, not a setting, and is listed as such).

Flash, espressif32@6.12.0, main 517b37d before, this branch after, same directory:

matrix-s3: 1,629,585 -> 1,496,373 bytes (-133,212), 82.9% -> 76.1% of 1,966,080.
matrix-s3-wroom: 1,644,465 -> 1,511,185 bytes (-133,280), 25.1% -> 23.1%.
matrix-waveshare: 1,632,393 -> 1,499,205 bytes (-133,188), 34.6% -> 31.8%.

RAM is unchanged on all three. Your own estimate in #3 was 32,956 bytes gzipped and "roughly 77%": the four assets come to 32,965 bytes, and matrix-s3 lands at 76.1%.

Measured on the board, not only built. I flashed this branch onto my Waveshare panel over the air, then main, then back, and asked for the same three files:

                main 517b37d          this branch
/               93,167 B, 0.222 s     12,060 B, 0.059 s
/portal.css     23,290 B, 0.071 s      5,605 B, 0.025 s
/portal.js      44,256 B, 0.179 s     15,252 B, 0.061 s
/api/portal     -                      6,561 B, 0.043 s
first load      160,713 B, ~0.47 s    39,478 B, ~0.19 s

A reload costs less than that again: the page carries an ETag and a second request comes back 304 with no body, which I checked on the device. The ?v= on the style and the script now carries each file's own content hash instead of the build date, so a rebuild that does not touch them no longer expires them in anyone's browser.

The page is 93,167 bytes on main and 72,701 in the repository - the difference is what the template wrote into it on every load.

A few things worth knowing:

- The layout editor waits for /api/portal now. It is built from the row mode, and /metrics can answer first; if it built early, a metric placed outside row mode 0's grid would fall back to "None" and the next Save would write that back. I hit exactly that before it was fixed.
- Content-Encoding: gzip goes out unconditionally. A client that sends an Accept-Encoding without gzip would get gzip anyway. Browsers have accepted it for 25 years, curl without the header is fine by RFC 9110, and your own WebServer does the same for .gz files from LittleFS, so I kept it simple; the alternative is to keep the uncompressed copy in flash, which is the whole saving.
- /api/portal is 6.5 KB on this device and goes out through sendJsonGuarded() like your other JSON.

How it was tested: the three builds; the generated page driven in a browser against a stand-in /api/portal with values chosen to be visible (row mode 3 builds three cells and three metrics keep their bar positions; the static IP card opens; the lists and colour pickers build; the form stays "All saved" while it fills); then the real thing on the panel with my own settings - 57 timezone regions with mine selected, 69 colour pickers, 15 rotation rows, the right subcard for the clock style, no console errors. Not tested: your matrix-s3 and matrix-s3-wroom boards, and browsers other than mine.

Nikolay
```

## His rules, checked

| Rule | This PR |
|---|---|
| One PR per change, off `main` | one change - the lighter portal - in two readable commits, from `upstream/main` 517b37d |
| Conventional Commits | `perf(web): ...` twice |
| No `FIRMWARE_VERSION` bump or release notes | none |
| Keep the existing formatting | his C++ and JS style, his markup untouched apart from the tokens |
| README only if user setup is needed | no user setup; the generator is documented in its own docstring and the build enforces it |
| All three envs build | SUCCESS, no warnings |
| `matrix-s3` size in the description | yes |
| No build flag | none; `extra_scripts` is a build hook, not a flag |
