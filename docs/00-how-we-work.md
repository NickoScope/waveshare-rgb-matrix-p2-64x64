# How we work: one repository, many worktrees, one session each

Read this first in any session about the panel. It says where to stand, what you
may touch, and how work gets back into the firmware the owner actually runs.

## The rule in one line

**One repository. One worktree per line of work. One session per worktree. One
session flashes.**

## Why not the alternatives

| Idea | Why not |
|---|---|
| A separate GitHub fork per feature | Splits the history. Every fork then has to be kept in sync with Keralots upstream by hand, and a merge back is a cross-repo exercise instead of a branch merge. |
| Everyone in one folder | Two sessions fight over `.pio`, over the git index, and over the one USB port. A build started by one clobbers the other's objects. |
| All features on one branch | An audit then has to reason about three unrelated changes at once, and a single bad one holds up the rest. |

## The layout

| Line of work | Worktree | Branch | Who touches it |
|---|---|---|---|
| The panel's own firmware: integration, releases, **flashing** | `/Users/apple/AnimatedPixelClock-integration` | `feature/market-climate-audio` | the integration session (the owner's main one) |
| A new feature | `/Users/apple/AnimatedPixelClock-<name>` | `feat/<name>` | its own session |
| A change offered to Keralots | `/Users/apple/AnimatedPixelClock-<topic>` | from `upstream/main` | its own session |

All of them are worktrees of the one clone at `/Users/apple/AnimatedPixelClock`,
so `git log`, tags and remotes are shared and a merge back is an ordinary merge.

## The physical constraint

There is one panel and one USB port. **Only the integration session flashes**,
and only it runs `pio run -t upload` or opens `/dev/cu.usbmodem*`. Everything
else builds in its own worktree - builds run in parallel happily, each worktree
has its own `.pio`.

Before any upload: `pkill -f panel_logger` (the serial logger holds the port).

## Starting a feature

```bash
git -C /Users/apple/AnimatedPixelClock worktree add -b feat/<name> \
    /Users/apple/AnimatedPixelClock-<name> feature/market-climate-audio
```

or `tools/new-feature.sh <name>` in this repository, which does that plus the
module skeleton, the flag-matrix row and the knowledge-base stub.

Inside the worktree the conventions are the ones `src/ir/`, `src/market/` and
`src/climate/` already follow:

- the code lives in `src/<name>/`, behind `-D<NAME>_ENABLED`, off by default;
- anything with rules or arithmetic gets a plain-C++ model header and a host
  test in `tools/<name>/check_<name>.py`, so it is tested without the panel;
- `src/<name>/README.md` says what the module is, what it costs and what it
  refuses to do;
- a row in `tools/flag_matrix.py` - the build without the flag must stay clean,
  and a build that needs a dependency must fail loudly without it.

## Where the context lives

Not in a chat. A session that starts tomorrow reads files:

1. `docs/NN-<feature>.md` in this repository - the goal, the constraints, the
   decisions already taken, the open questions. Written in the first hour, not
   at the end.
2. A line in `HANDOFF.md` - what is being done, in which worktree, on which
   branch, and what is unfinished.
3. `docs/00-how-we-work.md` - this page.

Opening line for a new session: *"read docs/NN-x.md and HANDOFF.md, the branch
is feat/x, the worktree is -x"*. That is the whole handover.

**Messages between sessions are not memory.** They are delivered into a session's
context, not into the visible transcript and not into any repository - the owner
cannot see them in either window, and they die with the session. Use them to
coordinate; copy anything agreed into the feature's document, or into a
`docs/drafts/NN-<feature>-coordination.md` alongside it, in the words it was sent.
If it is not in a file, it did not happen.

## Getting work back into the panel

1. The feature session takes the module to green host tests and its own build,
   commits and pushes its branch.
2. It writes what it did in `docs/NN-<feature>.md` and one line in `HANDOFF.md`.
3. The integration session merges, runs the **flag matrix** and the **audit**,
   builds, flashes and watches the panel.

That order is what has caught every real defect so far: the audit found the
crash-report and portal blockers, the flag matrix found the IR include under the
wrong guard, and the panel itself found what neither could.

## The standing rules, so they are in one place

- Nothing public - a PR, an issue comment, a post - without the owner's explicit
  word.
- Commit and push after every verified step, in both repositories.
- Every threshold, figure or "norm" comes from a source, and the source is named.
- Audits gate on BLOCKER and MAJOR; minors go to the backlog, not into the same
  evening.
- Helper sessions never flash, never push to `main`, never touch `/dev/cu.*`.
- The panel answers at `http://NickoScope-64x128.local/` - the IP moves.
