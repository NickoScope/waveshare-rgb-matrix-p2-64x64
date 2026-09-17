# Playable screens: what the self-playing demos would need to become games

**Draft, 2026-09-17.** Read-only study of `/Users/apple/AnimatedPixelClock-integration`, branch
`feature/market-climate-audio`, HEAD `e3b5f65`, env `matrix-waveshare-rgb`. Nothing was built,
flashed or changed. Flash and RAM deltas below are **estimates from the source**, not
measurements — a flag matrix was running in that tree's `.pio` and no build was made.

The question, in the owner's words: several screens already run game-like scenarios that play
themselves. Can they become games he plays, now that there is a rotary encoder and soon an
infrared remote?

**Short answer.** Four of them are already games with an AI holding the controller. Making them
playable is not "adding a game engine" — it is taking the steering wheel away from the code that
is already driving. The state is `.bss`, already linked; the render tick, the collision tests and
in two cases the death event already exist. What does not exist is any path from an input event to
a clock style, and that is the whole of the work.

## 1. Inventory

Derived by reading every file under `src/` that draws motion. Tick rates are the update gate
inside the screen; the frame rate that drives it is `getOptimalRefreshRate()` (`src/main.cpp:251`)
— 20 Hz for animated clock styles, 60 Hz while `isAnimationActive()`, 30 Hz for ambient.

| # | Screen | File / entry | What it simulates now | Tick | State it keeps | Player object today | How much of a game |
|---|---|---|---|---|---|---|---|
| 1 | **Arkanoid** (clockStyle 5) | `src/clocks/clock_pong.cpp:1046` → `:913` | Ball physics, a paddle, the time digits as bricks, fragments, multi-ball at :55 | 16 ms, resync after 5 (`:917-926`) | `pong_balls[2]`, `pong_fragments[40]`, `breakout_paddle` (`clock_globals.h:76-87`) | **Yes — a real paddle**; AI at `clock_pong.cpp:148` sets `target_x` to the nearest ball | **~90 %.** The miss is already an explicit branch (`:488-497`) |
| 2 | **TRON** (16) | `src/clocks/clock_tron.cpp:277` → `:88` | Two light cycles on a 64×32 grid, trails, digit tracing | 80 ms per step (`STEP_MS` `:15`) | `bikes[2]` with 96-point trails (`:23`), `occupied[32][64]` (`:31`) | **Yes — bike 0**, steered by scoring three directions | **~85 %.** Crash → `b.dead` (`:107`), respawn after 650 ms |
| 3 | **Snake** (7) | `src/clocks/clock_snake.cpp:415` | Nokia snake: body, food, growth, digits as obstacles | 45–320 ms per cell (`:215`) | `snake_body[24]` (`:68`), `snake_pellets[35]`, phases (`:44`) | **Yes — the snake**, steered by a flow field (`:266`) | **~80 %.** `snakeCellFree()` (`:141`) exists but is used to *avoid* death |
| 4 | **Tetris block game** (8) | `src/clocks/clock_tetris.cpp:742` → `:411` | A 32-column well, 7 pieces in 19 orientations, row clears, a scoring AI | 16 ms (`TET_ANIM_SPEED` `:33`) | `tet_well[13]` row masks (`:99`), `TET_ROTS[19]` (`:127`) | **Yes — the falling piece** (`tetGamePickPiece()` `:341`) | **~75 %.** No game over: it wipes the well (`:414-417`) |
| 5 | **Ambient Space Invaders** (ambient 0) | `src/ambient/ambient_invaders.cpp:215` | A 4×6 fleet in lockstep, an auto-aiming cannon, bombs, a UFO, waves | 30 Hz; march `650 − (24−alive)·18` ms (`:235`) | `invAlive[24]`, bullets, booms, ufo | **Yes — the cannon** (`fireCannon()` `:134`), death at `:317-320` | **~85 %**, and no clock at risk |
| 6 | **Ambient Pac-Man** (ambient 1) | `src/ambient/ambient_pacman_chase.cpp:336` | A 15×7 maze, dots, power pellets, four ghosts with scatter/chase | dt-based, clamped 0.1 s (`:346`) | maze arrays, `gh[4]`, `ghMode[4]`, `deathTimer` | **Yes — Pac** (`choosePacDir()` `:197-222`) | **~90 %.** Caught → `deathTimer = 32` (`:409`) |
| 7 | **Asteroids** (10) | `src/clocks/clock_asteroids.cpp:631` → `:370` | A ship with inertia and wrap, splitting rocks, a bullet | dt-based (`:374`) | ship state (`:83-85`), `ast_rocks[8]`, `ast_shards[14]` | **Yes — the ship**, but wants turn + thrust + fire | ~70 %, least suited to one knob |
| 8 | **Bomberman** (15) | `src/clocks/clock_bomberman.cpp:190` | A hero walking a lane graph between brick digits, bombs, blast | dt-based (`:206`) | hero position, `route[20]`, phases (`:25`) | Partly — waypoints only (`laneX[5]`, `laneY[4]`) | ~45 %: free movement is a rewrite |
| 9 | **Dino** (11) | `src/clocks/clock_dino.cpp:410` → `:166` | A runner, scrolling ground, cacti, a pterodactyl | dt-based (`:171`) | jump state, cactus timer, clouds | **Yes — one button** (auto-jump `:292-310`) | ~50 %: **no collision test exists** |
| 10 | **Pac-Man clock** (6) | `src/clocks/clock_pacman.cpp` | Pac patrols and eats the changing digit | 16 ms | patrol/eat state, pellets | A sprite on a path | ~20 % |
| 11 | **Space Invaders clock** (3/4) | `src/clocks/clock_space.cpp:330` | One invader lasers the changing digit | 16 ms | patrol/slide/shoot/explode | One lane, one target | ~15 % |
| 12 | **Mario** (0) | `src/clocks/clock_mario.cpp:221` | Mario walks, jumps and bumps digits | 16 ms | `mario_state`, jump physics, enemy | A sprite on rails | ~20 % |
| 13 | **Lua: snooker** | `tools/luasim/scripts/snooker_clock.lua` (1082 lines) | A full frame to WPBSA rules, plays itself | task "luafx", core 0 | in Lua, PSRAM canvas | The cue ball | **~95 % of a game**, 0 % of an input path |
| 14 | **Lua: football** | `football_clock.lua` (1038 lines) | A match plays itself, IFAB pitch, score bug | as above | in Lua | 22 players | ~80 %, same input problem |
| — | Matrix rain (12), Weather (14), Standard/Large (1/2), ambient Stars / Aquarium / This-is-fine / Custom, the nine `viz/wow` effects | Motion, not play | — | — | — | none | **0 %** — checked and rejected |

## 2. Input: the real contract today

### The knob

| Fact | Source |
|---|---|
| EC11 on A = IO45, B = IO46, switch on GPIO0 shared with BOOT | `src/control/control.cpp:34-36` |
| Sampled by an `esp_timer` at **1 kHz**, not at loop speed | `control.cpp:74`, `:275-286` |
| Events: `CTRL_CW`, `CTRL_CCW`, `CTRL_PRESS`, `CTRL_LONG` | `src/control/control.h:39-45` |
| Queue of 16, single producer, single consumer; full → the newest is dropped | `control.cpp:106-108`, `:175-178` |
| `CTRL_PRESS` is pushed **on release**, if held under 500 ms | `control.cpp:75`, `:249` |
| `CTRL_LONG` fires **at** 1000 ms of hold, once | `control.cpp:76`, `:252-255` |
| **There is no long-press gesture on this panel**: `loop()` folds `CTRL_LONG` into `CTRL_PRESS` | `src/main.cpp:901`, rationale `control.h:8-16` |
| **A clock style can see no input at all today** — rotation reaches a page only if `ctrlPageHasControls()` says so, and the clock page is not in that list | `main.cpp:611-628`, `:928-952` |
| `controlHeld()` / `controlHeldMs()` are public but used only by the portal's knob tester | `control.h:53-54`, `src/web/web_panel.cpp:875` |

### The remote

The knowledge base's claim holds exactly: **the IR module produces what the encoder produces —
detents and a button level — and nothing else** (`src/ir/ir_map.h:2-10`, docs/24).

| Fact | Source |
|---|---|
| Eight slots; three (CCW, CW, OK) drive the knob's state machine, five are reserved | `ir_map.h:38-48` |
| The seam is **inside the encoder's 1 kHz task**: `irTakeRotate()`, `irOkDown()` | `control.cpp:222-223`, `:242` |
| A held NEC key repeats every **108 ms**; `kHoldMs` 250, `kRepeatFreshMs` 200 | `ir_map.h:102-105`; Vishay 80071 rev 2.3 |
| **A build cannot carry the receiver and the knob together** — header U8 is IO45/IO46 and that is the whole budget | `ir.cpp:46-50`, docs/24 |
| No receiver is soldered; the 2.2 kΩ pull-up is arithmetic, not a measurement | HANDOFF open item 2 |

### Latency, end to end (derived, not measured)

| Path | Floor | Ceiling |
|---|---|---|
| Knob detent → action | ~1 ms sample + one `loop()` pass | loop passes **5–11 ms idle, 43 ms with the visualizer, 211–324 ms while the portal serves a page** (docs/22 §12.2) |
| IR detent → action | one pass to decode + ~1 ms + one pass to consume | same |
| **IR click → `CTRL_PRESS`** | **≥ 250 ms** | the level is held `kHoldMs` after the last frame and `CTRL_PRESS` only fires on release |
| IR button **level** (`controlHeld()`) | one pass + 20 ms debounce | the path a game must use for fire |

**Consequence:** a game that needs a fire button cannot read it as an event over IR. It must poll
the level — which is why `controlHeld()` is already in the public header.

## 3. Per-screen playability, ranked

All listed state is `.bss`, linked at build time, so run-time heap is **zero** everywhere.

| Rank | Screen | Player controls | The loop still needs | Effort | Flash (est.) | Risk to the clock |
|---|---|---|---|---|---|---|
| **1** | **Arkanoid (5)** | paddle x from detents | lives (hang on the miss at `clock_pong.cpp:488`), score, game over, restart | **S** | ~2–3 KB | **Low** |
| **2** | **TRON (16)** | bike 0's turn | score = survival; death exists (`:107`); restart | **S** | ~2 KB | **Low** |
| **3** | **Snake (7)** | direction | turn `snakeCellFree()` (`:141`) into a death test; score; restart | **S/M** | ~2 KB | **Medium** (the eat-the-digit phase must yield) |
| **4** | **Ambient Invaders** | cannon x + fire | fire input, lives from `cannonHitTimer` (`:317`), score, waves | **M** | ~2 KB | **None** |
| **5** | **Tetris (8)** | column + rotation | a real game over (today it wipes the well, `:414`), line score | **M** | ~2–3 KB | **Low** in small-clock mode |
| 6 | Ambient Pac-Man | Pac's direction | lives from `deathTimer` (`:409`), dot score, level clear | M | ~2 KB | None |
| 7 | Dino (11) | jump | **a collision test that does not exist**, score, restart | S + one new rule | ~1.5 KB | Low |
| 8 | Asteroids (10) | turn, thrust, fire | three inputs on one knob | L | ~3 KB | Medium |
| 9 | Bomberman (15) | free movement + bomb | movement off the lane graph — a rewrite | L | ~4 KB | Medium |
| 10 | Snooker (Lua) | aim + power + strike | **a `px` input binding that does not exist** | L | 0 (script) | core-0 budget |
| — | Pac-Man clock (6), Space Invaders (3), Mario (0) | — | a play space would have to be invented | L, low value | — | High, for no gain |

**Shortlist: Arkanoid, TRON, Snake, ambient Invaders, Tetris.** The first three are playable with
the knob alone; Invaders wants a fire button and should wait for the receiver.

## 4. Architecture

**Play mode does not add a game. It takes the steering wheel from the AI that is already driving.**

### Recommended: `src/play/`, an arbiter plus one guarded hook per screen

| File | What it holds |
|---|---|
| `src/play/play_model.h` | Plain C++, no Arduino: session state machine, idle-exit rule, score and lives arithmetic, high-score merge. Host-tested by `tools/play/check_play.py`, as `ir_map.h`, `climate_model.h`, `presence_model.h` are |
| `src/play/play.{h,cpp}` | The arbiter: which screen is playable, enter/leave, the NVS namespace, the HUD, the `/api/info` block |
| `src/play/play_games.h` | One table row per playable screen — `{styleId, name, begin, steer, tick, over, score}`, the way `kClockStyles` is a table |
| each screen's `.cpp` | **One guarded hook**, three lines |

The hook in Arkanoid is the whole pattern:

```cpp
void updateBreakoutPaddle() {
#if defined(PLAY_MODE_ENABLED)
  if (!playSteerPaddle(&breakout_paddle.target_x))
#endif
  { ...the existing AI tracking, unchanged... }
```

plus a second at the miss branch (`clock_pong.cpp:488`) calling `playLostBall()`.

**Input routing — no new gesture.** `ctrlPageHasControls(PAGE_CLOCK)` (`main.cpp:611`) returns true
while the style is playable; the existing click-to-enter path (`:928-931`) enters play; the
existing rotate-while-entered path (`:934`) routes detents to `playKnob(d)`; the amber corner mark
(`:1302`) already means "the knob acts here"; leaving is another click or the per-page timeout
(`ctrlEnterTimeoutMs()` `:633`), ~45 s from the last game input.

**Fire.** Not the click — the click is the way out. Poll the button *level* with `controlHeld()`
inside the game tick: ~20 ms after a knob press, one loop pass after an IR frame, against the
250 ms floor the event path imposes on IR.

**Attract mode.** The self-playing code *is* the attract mode and stays byte for byte.
`playBegin()` seeds the player object from wherever the AI left it, so nothing resets; on leaving,
the AI recomputes its target on the next tick.

| Subsystem | Rule while a game runs |
|---|---|
| The clock | **Keeps running.** The digits are the bricks — that is the point |
| The minute change | Open question §7: at :55 Arkanoid starts breaking digits itself and spawns a second ball |
| Carousel | Held (`carouselNote()` already fires on knob events, `main.cpp:897`) |
| Notifications / cards | Pause the game, show the banner; the first click dismisses it and must not also fire |
| Scheduled off | `isDisplayForcedOff()` gates the render tick (`main.cpp:1143`) → record the score, leave play |
| The portal | Unchanged; a read-only `play` block in `/api/info` is enough for phase 1 |
| Watchdog | Nothing new: the game tick is the render tick |

**Score.** NVS namespace `play`, one blob `{u8 version; u8 count; row{u8 game; u32 best; u32 when;}}`
— eight games is 74 bytes. Written only on a new best, never during play.

**Merge friction.** Upstream takes no new features, so this stays in the fork — but `clock_*.cpp`
are upstream files. This shape keeps the conflict surface to **one three-line `#if` per file**.

### Alternative A — a games page of its own (`PAGE_GAMES`)

Touches no upstream file, zero merge friction, but every game needs its own renderer and art,
costs flash on the `matrix-s3` env already at 82 % of 4 MB, and the device stops being "the clock
you can play". Right home for phase-2 games that are not clocks; wrong first step.

### Alternative B — play in Lua

No C++ risk, hot-swappable, and snooker maps perfectly onto one knob. But the effect task sits on
core 0 beside Wi-Fi with a 12 KB stack, frame-budget debts are on record (docs/22 D6/D7), and
**`px.*` has no input binding today**. Right home for snooker later.

## 5. Constraints and traps from the knowledge base

| # | Trap | Consequence | Source |
|---|---|---|---|
| 1 | Internal heap is the scarce resource (~33–41 KB free, minimum seen 504 B under the portal + mics) | Play mode must allocate **nothing** at run time. This design allocates nothing | HANDOFF; docs/22 §12.2 |
| 2 | The portal's ~20 KB spike (D1) and 0.2–0.3 s freeze per page (D8) | The honest ceiling on responsiveness; dt-clamped physics, never count a stall as input | docs/22 §12.3 |
| 3 | `esp_task_wdt_init(15, true)`, only `loop()` subscribed | Do not create a task | `main.cpp:567-568` |
| 4 | HUB75 DMA flips take effect at the end of the scan | Draw inside the same tick as every other page | `main.cpp:1155-1163` |
| 5 | 30 Hz vs 60 Hz beat on full-panel content | A full-panel game must not ask for 60 Hz | `main.cpp:294-301` |
| 6 | `matrix-s3` is at 82 % of 4 MB | The flag must be off by default there | docs/03 |
| 7 | Upstream takes no new features | Fork only; one guarded hook per upstream file | docs/09 |
| 8 | The flag matrix (53 rows) and its known false-failure mode | A new flag adds rows; never pipe the matrix through `tail` | docs/24 |
| 9 | Host-test convention | `play_model.h` + `tools/play/check_play.py`, or it is untested where it matters | `ir_map.h`, `climate_model.h` |
| 10 | `millis()` wrap — both IR blockers were this class | Ages unsigned, no deadlines; exercise the model at 25.5 days | docs/24 |
| 11 | The receiver has never run | Nothing IR-dependent before it is soldered and measured | HANDOFF open item 2 |

## 6. A staged plan

| Stage | What | Why now | Gate |
|---|---|---|---|
| **0** | Owner answers §7 | Two questions change the architecture | — |
| **1** | **Arkanoid on the knob, end to end**: `play_model.h` + host test, `src/play/`, two hooks in `clock_pong.cpp`, `-DPLAY_MODE_ENABLED`, flag-matrix rows, README | The cheapest proof: paddle, ball, bricks and *the miss* already exist | Measure `loopMaxMs`, free internal heap, flash delta on the panel |
| **2** | **TRON and Snake** | Proves the adapter is a table row, not a rewrite | Under ~60 lines each outside `src/play/` |
| **3** | Score, high score, game-over overlay, HUD, NVS, `/api/info` | Worth building once three games agree what a score is | One flash write per new best |
| **4** | **After the receiver is soldered:** `kBack` to leave, a slot to fire; then ambient Space Invaders, optionally Asteroids | A fire button costs a gesture the knob does not have | The receiver measured, `ir.enabled` explained |
| **5** | Optional: Tetris with player control; snooker in Lua once `px` has input | Good games, not on the critical path | — |

## 7. Open questions for the owner

1. **"A game that is also the clock", or "games on the panel"?** Picks between the recommended design and Alternative A.
2. **The minute change during play.** Does the game win (defer the transition) or the clock win (the bricks change under you)?
3. **The long press.** `main.cpp:901` deliberately makes it identical to a click. Keep that law, or spend the long press on "leave play"?
4. **Ambient window and carousel:** may a session suppress both?
5. **Lives and score on screen:** a band like the style toast, or folded into the digit area?
6. **High score:** per game only, or with a name? Names need text entry, painful on one knob.
7. **Once the receiver works, which remote buttons become what?** Five reserved slots wait in `ir_map.h:42-46`.

## Findings most likely to change the plan

- An IR click cannot reach a page faster than **250 ms**, because `CTRL_PRESS` only fires on
  release and the IR button is a 250 ms level. A fire button must poll `controlHeld()`.
- **The receiver and the knob cannot exist in the same image** (`ir.cpp:46-50`): one input device
  per build, so no arbitration is ever needed.
