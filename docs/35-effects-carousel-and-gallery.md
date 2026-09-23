# 35. Effects: the carousel switch, delete, the gallery, and agent publishing

Firmware 2.5.7 (unreleased as of 2026-09-23). Code:
`NickoScope/AnimatedPixelClock` main at f3c515a. The owner's panel runs the
same source over the air (image SHA-256 `3bc280ca70100454…`).

## What the owner asked (2026-09-23)

- 16:31: "каждый луа эффект можно было отключить из карусели (убрать +),
  удалить и добавить из галереи на гитхабе".
- 17:00: "сам оттестируй вкл/выкл, удаление/добавление, все задокументируй".
- Later: "дай нашему агенту open claw доступ публиковать созданные им луа
  эффекты в галереи на гитхабе и удалять неудачные".

## How it works

### Per-effect switch

- **Storage.** A list of the effects that are switched off, **by name**, in NVS
  key `luaOff`. It sits in a 512 B PSRAM buffer, so it takes no internal RAM.
  An empty list means no key at all.
- **Knob and carousel.** Both skip an effect that is off
  (`ctrlEffectInWalk` in `ctrlNextVisited`). "Show" still shows it.
- **Deleting.** Deleting an upload forgets its switch
  (`panelEffectsPrune`). An upload with the same name therefore comes back
  switched on.
- **API.**
  - `GET /api/lua` returns `inWalk[]`.
  - `POST /api/lua {"walk":{"i","name","on"}}` switches one effect.
  - `/api/panel` returns `effectOn` per page and takes
    `POST {"enable":{"page","name","on"}}`.
  - `name` is optional. If it no longer matches index `i` (an upload or a
    delete renumbered the list), the panel answers **409** and switches
    nothing.
  - A full list of off names is also a 409, not a silent success.
- **Upload names.** An upload is refused if its name would read the same as an
  existing effect: a built-in, or another case of the same stem ("aquarium"
  vs AQUARIUM). Uploading the same stem again replaces the effect.

### Portal (Effects & clips)

- **Each effect has:**
  - a switch;
  - Show;
  - Delete, only on uploaded effects. It asks first.
- **"Add from the gallery":**
  - The list is read from
    `raw.githubusercontent.com/NickoScope/AnimatedPixelClock/main/gallery/index.json`.
  - "Add" fetches the script and uploads it to `/api/lua/upload?name=NAME`.
  - An entry is drawn only if its file is `<stem>.lua` and its preview is
    `preview/<stem>.png`, by the panel's own stem rule. The preview address is
    escaped. This came from the gate audit: a bad index could otherwise have
    put script on the panel's origin.
  - If GitHub cannot be reached, the portal asks again once a minute.
- **Pages card:** one switch for all effects, plus one per effect.

### Gallery publishing (agents)

- **Commands.**
  - `tools/agent/gallery.py publish <stem> --about "…" --by <who>` and
    `unpublish <stem> --by <who>`. Both take `--dry-run`, and `--any` for a
    person.
  - MCP tools `gallery_publish` and `gallery_unpublish`. The publisher comes
    from `LEDMATRIX_PUBLISHER`.
- **Checks, in order:**
  1. The name follows the panel's rule, and no built-in or other gallery entry
     reads the same.
  2. Nothing made from a photograph: markers from `photo_to_lua.py` and
     `chafa_to_lua.py`. The repository is public.
  3. The panel's own validator passes.
  4. 300 frames in the simulator: an error or an all-black screen is refused.
- **Output:**
  - a preview;
  - a README section written from `--about`;
  - the index, which records `"by"`;
  - one commit that touches only `gallery/`, then a push.
- **Where it runs:** in a throwaway worktree of the remote's `main`, so the
  local clone is never touched. A push that loses a race is retried once.
- **Ownership:** an entry marked `-- @by X` can be replaced or removed only by
  X. A person's entries are out of an agent's reach.

## Tests run

| What | Where | Result |
|---|---|---|
| Off → on → off, then reboot (uptime 93 → 15 s) | panel | stays off. Before the fix it came back on: gate-audit HIGH, `putString("")` returns 0 |
| All back on, reboot | panel | all on, key removed |
| All off except AQUARIUM, 3 min of carousel (before this session's fixes) | panel | never landed on an effect that was off |
| Upload "aquarium", "LA_GIOCONDA" | panel | 400: "an effect called … is already on the panel" |
| Wrong name with a switch | panel (self-test) | 409 |
| `health.py --effects`: switch round trip; gallery upload → show → delete (CANNES) | panel | PASS; 14 effects, all in the walk; ping 39/39 |
| Portal JS in JavaScriptCore (`tools/web/check_effects_ui.py`) | Mac | 22/22. Six mutations tried (escape removed, rollback removed, wrong delete body, filter removed, back-off removed, note clear removed): all six caught |
| `test_effect_walk.py` | Mac | 7/7 |
| `test_gallery_publish.py`: the whole path against a local bare remote, plus a remote that refuses every push | Mac, in pre-commit | 13/13 |
| `gallery.py publish flip_dot_clock --dry-run` | nickol | passes every check, 11 s |

## Incidents in this session

- **The portal was flashed without the gzipped assets rebuilt.**
  `web_assets.h` is generated, and the build does not regenerate it. The first
  image served the old `panel.js`. Pre-commit caught it, and the image was
  rebuilt and reflashed. Checked: the panel serves `galEntryOk`.
- **A test commit landed on my local branch.**
  - Cause: run from pre-commit, the publishing test inherited git's
    `GIT_DIR`/`GIT_INDEX_FILE`. They override `-C`, so the worktree's commit
    went onto my local branch.
  - Caught before any push and undone.
  - Fix: the tool now drops `GIT_*` for every git call. The test runs the tool
    with those variables set and checks that the checkout's HEAD and status
    do not change.
- **nickol could not reach GitHub at all.**
  - `ssh -T git@github-ledmatrix` says Permission denied, and the repository
    has no deploy keys.
  - The nightly pull still worked on 2026-09-23 at 01:40 UTC.
  - `gh repo deploy-key add --help` says that keys added by gh are removed when
    the gh token is de-authorized. That is one possible cause. **Not verified.**
  - Effect: the agent's MCP was stale (24 tools, before v2.5.6).
  - Fix: the clone now fetches over https (a public repository needs no key)
    and pushes over the ssh alias. The agent's two unpushed commits are kept as
    branch `openclaw/unpushed-2026-09-23`, on nickol and on the Mac, not on
    GitHub. The clone is now at main f3c515a with 30 tools. Pillow is installed
    and pinned in `update.sh`, and `.env` has `LEDMATRIX_PUBLISHER=openclaw`.

## Write access: the owner's decision

The agent's publishing works up to the push. The push needs a key that GitHub
accepts for writing, and adding one is a security setting, so it is the
owner's step.

GitHub's documentation, "Managing deploy keys" (read 2026-09-23):

- "Deploy keys only grant access to a single repository."
- "A deploy key with write access lets a deployment push to the repository."
- The page says nothing about limiting such a key to certain branches.
  Whether a ruleset can do that: **not verified**.

What follows for us: a write key on `AnimatedPixelClock` would let anything
with a shell on nickol push anything, including `docs/firmware/`, which the
web flasher serves. The agent is an LLM that takes messages.

- **A (quick):** add the existing nickol key with write access to
  AnimatedPixelClock. Add it in the web UI rather than with gh, so it is not
  tied to a gh token.
- **B (recommended):** a separate public repository just for the gallery, with
  its own write key. The agent then cannot reach the firmware. The cost is
  that the portal's gallery address and the tools move to it. Now is the time,
  before 2.5.7 is released.

## Backlog (not blockers)

- **Carried over from the audit:**
  - `panelEffectsPrune` at boot is deliberately not added: a LittleFS mount
    failing at boot would wipe the switches;
  - `keep[512]` on the loop stack.
- **The agent's Screen of the Day plan:** its
  `gallery/SCREEN_OF_THE_DAY.md` plans a new screen every day at 07:00,
  published to the gallery with 👍/👎 from the owner. That is daily commits to
  a public repository. The owner has not decided this yet.
- **`rbStn` in `panelTick`** uses the same `putString` return check. It is only
  wrong for an empty station name. Not touched.
