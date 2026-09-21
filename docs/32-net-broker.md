# 32. The network broker: one owner of the outbound socket

**Why this exists, in one line:** four modules each start their own 9-12 KB task with its own TLS
session to fetch a few kilobytes of JSON, on a board with 34 KB of internal RAM - and the panel
spends its day either short of memory or short of it *in one piece*.

Decided with the owner on 2026-09-20, after a day of one-constant fixes that each moved the
symptom somewhere else. The council of models consulted the same evening reached the same place
from the other direction: widen the budget before managing it, and the budget is not widened by
trimming - it is widened by having one consumer instead of four.

## What the panel does today

| Consumer | How it fetches | Internal RAM at peak |
|---|---|---|
| Rail board (`src/railboard/rtt_direct.cpp`) | its own FreeRTOS task, its own TLS | 9 KB stack + ~2.2 KB TLS context + socket |
| Flight board (`src/flightboard/aero_direct.cpp`) | the same, separately | 12 KB stack + the same |
| Weather (`src/weather/weather.cpp`) | the same, separately | 8 KB stack + the same |
| World clock's location (`src/worldclock/wc_home.cpp`) | the same, separately | 8 KB stack + the same |

They already take turns among themselves (`src/network/net_lock.h`, since 2026-09-14), and since
2026-09-20 the web server takes turns with them too. **Turn-taking was necessary and is not
sufficient**: each turn still creates a task, allocates its stack out of whatever the heap has at
that moment, runs, and frees it - leaving the heap a little more broken than it found it.

Measured on the panel, 2026-09-20, over the cable:

- After boot: **34 KB free, 25.6 KB largest contiguous block.**
- After a few minutes of ordinary use: **30 KB free, 11 KB largest block.** The memory is there;
  it is no longer in one piece.
- The rail board asks for a 13 KB contiguous block and stops fetching when it cannot have one -
  short by **524 bytes** on one occasion, with 30,828 B free.
- With a browser holding the portal open, internal free walked down in six steps -
  30,712 → 17,096 → 14,396 → 11,056 → 8,796 → 4,652 → **1,268 B** - and the Wi-Fi task could no
  longer allocate its 1,626-byte DMA receive buffers.

## What the broker is

**One task, created at boot, that owns the outbound socket and the TLS session.** Nobody else
opens one. The other modules stop being fetchers and become callers:

```
  rail board ─┐
flight board ─┤
    weather ──┼──►  request queue  ──►  net broker task  ──►  the network
 world clock ─┘      (bounded)          (one stack, one TLS,
                                         allocated once at boot)
```

Three properties, and each of them removes a class of failure we met today:

1. **The stack is allocated once, at boot, while the heap is whole.** A task stack must be
   internal in this SDK - checked against the FreeRTOS source, `xPortcheckValidStackMem` requires
   `esp_ptr_internal` unless `CONFIG_FREERTOS_TASK_CREATE_ALLOW_EXT_MEM`, which this pre-built SDK
   does not set. So the only way to stop paying for it repeatedly is to pay once.
2. **Nothing is allocated per fetch.** One request buffer and one response buffer, sized once,
   reused. No allocation in steady state means no fragmentation from this path at all - and
   fragmentation, not exhaustion, is what has been stopping the rail board.
3. **The queue is bounded and the refusal is at the front door.** A caller whose request does not
   fit is told so immediately and cheaply, instead of starting something that fails halfway.

## The interface

Deliberately small. A caller says what it wants and where to put the answer; it never sees a
socket, a task or a buffer.

```c
// src/net/net_broker.h  (sketch - the real one arrives with the code)

typedef enum { NB_OK, NB_QUEUE_FULL, NB_BUSY, NB_HTTP, NB_NET, NB_AUTH, NB_TOO_BIG } NbResult;

typedef struct {
  const char *host;          // "example.org"
  const char *path;          // "/api/thing?x=1"
  const char *bearer;        // optional, not logged, not echoed
  uint16_t    port;          // 443
  uint32_t    timeoutMs;
  char       *into;          // caller's buffer, in PSRAM
  size_t      intoCap;
  void      (*done)(NbResult, size_t len, void *user);   // called on the LOOP task
  void       *user;
} NbRequest;

bool     nbSubmit(const NbRequest *req);   // false when the queue is full; never blocks
bool     nbBusy(void);                     // a request is on the wire right now
uint8_t  nbQueued(void);                   // how many are waiting
void     nbStatusJson(JsonObject out);     // for /api/info: queue depth, last result, stack high-water
```

Rules the broker keeps, so callers do not have to:

- **One request on the wire at a time.** The queue is FIFO with one exception: a request marked
  *interactive* (the owner just changed the station) jumps ahead of a scheduled refresh.
- **The answer lands in the caller's PSRAM buffer**, and the callback runs on the loop task, where
  the existing code already parses.
- **The web server yields to the broker and the broker yields to the web server** - the mechanism
  already in place since 2026-09-20 (`net_turns.h`), kept, but now with one counterpart instead
  of four.

## What each consumer loses

Each of the four modules deletes its task creation, its TLS client, its own retry/back-off task
plumbing, and its share of the `netLock` dance - and keeps its parsing, its schedule and its own
back-off policy. That is the bulk of `rtt_direct.cpp`, `aero_direct.cpp` and the fetch halves of
`weather.cpp` and `wc_home.cpp`.

## The budget, before and after

| | today | with the broker |
|---|---|---|
| tasks that can hold a TLS session | 4 | **1** |
| internal RAM for those stacks | 8-12 KB **per fetch, when it happens** | **one 12 KB stack, taken at boot** |
| allocations per fetch | a task, a stack, a TLS context | **none** |
| contiguous block needed at fetch time | 10-13 KB | **none** |
| fragmentation contributed by fetching | every fetch | **none** |

The 12 KB does not disappear - it is paid once, at boot, out of the 34 KB, and never returned.
What disappears is the *variance*: the panel stops needing a large contiguous block at the worst
possible moment.

## Risks, named before they bite

- **One broker is a single point of stall.** A slow host blocks everyone behind it. Mitigation: a
  hard per-request deadline enforced by the broker, not by the caller, and the queue keeps moving.
- **A single shared buffer means a size limit for everyone.** Sized for the largest real response
  we have (the rail board's, measured), with `NB_TOO_BIG` rather than a silent truncation.
- **Callbacks on the loop task can still be slow.** Parsing stays where it is, so nothing new -
  but the broker must not hold its lock across the callback.
- **This is a big change to four working modules.** It lands behind `-DNET_BROKER_ENABLED`, one
  consumer at a time, with the old path intact until the last one moves.

## Order of work

1. This document, and the numbers in it re-checked on the panel. **Done 2026-09-20.**
2. `src/net/net_broker.{h,cpp}` plus a host test of the queue's rules - ordering, the interactive
   jump, the bounded refusal, the deadline - with no Arduino in it.
3. The **weather** moves first: it is the simplest consumer and the least visible if it breaks.
4. The **world clock's lookup** second: it runs once per boot.
5. The **rail board** third, with the owner watching, because it is the one he uses.
6. The **flight board** last; then the old fetch paths and `netLock` come out.
7. The audit gate at every step, and the panel only after it.

## What this does not fix

The yacht radar's AIS websocket is a long-lived session, not a fetch, and holds 17.5 KB while its
page is shown - measured. It does not belong in the broker's queue and needs its own answer.
The web server's own per-request cost stays as it is; today's measurements say it is not the
binding constraint once the fetchers stop fragmenting the heap.

---

## What was actually built, 2026-09-20, and where it differs from the sketch above

Steps 2 and 3 are done (`feat/net-broker`, `1dc96fb` the queue, `f8e044c` the task and the
weather). Three things came out different from the interface sketched above, and the differences
matter more than the agreements do.

**There is no shared response buffer, and no `NB_TOO_BIG`.** The sketch had the answer copied into
the caller's PSRAM buffer. That was wrong: not one of the four consumers works that way today -
every one of them parses straight off the socket (`deserializeJson(doc, http.getStream())`), so a
buffer would have *added* a full second copy of every response and a size ceiling that does not
exist now. The broker hands the caller the live stream instead:

```c
struct NbReply { int code; Stream *body; bool tls; void *ctx; };
typedef bool (*NbParseFn)(const NbReply &reply);
bool nbSubmitRequest(uint8_t who, const NbRequest &req, bool interactive);
bool nbTake(uint8_t who, bool *ok);     // the outcome, once, on the loop task
```

**The parse therefore runs on the broker task, not on the loop task.** It has to: the body is only
on the wire during the call. This is not a regression - it is exactly where the parse runs today,
on the fetch task the module started itself - but it means the contract is now explicit, and it is
written on `NbParseFn` in the header: touch only your own module's published data, under your own
lock. What the loop task gets is the *outcome*, through `nbTake()`.

**One URL, not host/path/port.** `HTTPClient::begin(client, url)` is what all four already build.

**The per-request deadline is the library's, not a hard abort.** The sketch promised a deadline
"enforced by the broker, not by the caller". What is actually enforced is `setConnectTimeout`,
`setTimeout` and a 12 s TLS handshake timeout (against the library's own default of 120 s). A
genuinely hard deadline would mean closing the socket from a second task while the first is inside
mbedTLS, and that is not safe. So: a stuck host holds the wire for up to the timeout, and no
longer - but it does hold it. Say it that way rather than claim more.

### The numbers, from the map file rather than from hope

`s_stack` is **12,288 B at 0x3fca5290** - `.bss`, internal DRAM, confirmed with `nm` on the
firmware image, plus 36 B for the queue and 40 B for the job table. It is 12 KB the heap never
gets back, and that is the trade: against it, the *peak contiguous internal demand of a fetch*
falls from 8-12 KB, needed at an unpredictable moment, to nothing at all - there is no longer a
task to create. 12 KB because it is the largest of the four stacks it replaces (flight 12, rail 9,
weather 8, world clock 8), so no caller can be worse off than today. It is deliberately not
tightened yet: the broker prints its own stack high-water mark on every fetch, and the number comes
down when there is a distribution to cut it from, the way the rail board's 12 KB became 9.

### The transitional risk, named

While the other three modules still start their own fetch tasks, the broker waits on the old
`netLock` for up to 30 s **with its queue slot marked on-air**. So during the migration a stalled
rail-board fetch can delay an interactive weather request. It is transitional by construction - the
lock has no other holder once step 6 lands - but it is real until then, and it is the reason the
remaining consumers should move quickly rather than sit half-migrated for a week.

---

## The panel said no, 2026-09-20 23:25, and it is the same mistake as `net_reserve`

The broker build was flashed over the cable and measured against the known-good build on the
same board, minutes apart:

| | `fix/panel-tonight` | `feat/net-broker` |
|---|---|---|
| free internal | **34,888 B** | 19,624 → 18,492 B |
| **largest contiguous block** | **16,372 B** | 11,252 → **9,716 B** |

And the three modules that have not moved still need a contiguous internal block for their own
task stacks, checked before they even try: **flight 13,312 B, rail 10,240 B, world clock 9,216 B.**
At a largest block of 9,716 the flight board cannot fetch at all, and the other two are at the
edge. The panel was put back on `fix/panel-tonight` the same minute, before the owner had to find
it.

This is **exactly the `net_reserve` failure again** (`src/net/net_reserve.h`): take a large
contiguous block at boot, and the modules that still need one starve. The difference is that
`net_reserve` bought nothing, while this buys an end state where *nobody* needs a contiguous
stack - but that end state does not exist until all four have moved. **In between, the panel is
worse, and "in between" is where a one-consumer-at-a-time migration lives.** The staged order in
this document was written without that arithmetic in it. It is wrong as written.

Two ways out, and they are not exclusive:

1. **Size the stack from a measurement instead of from the largest of the four.** 12 KB was
   chosen so no caller could be worse off; it is not a measured figure and nothing has measured
   it yet. The rail board's own task turned out to use 6,152 B of 12,288. A 6 KB broker stack
   would return ~6 KB of contiguity and put the flight board back above its threshold on its own.
2. **Land all four at once**, so the three thresholds disappear at the same moment the 12 KB does.

### And the first consumer was the wrong one

`served` stayed at **0** for the whole test: the broker was never asked. The weather page was on
screen - the owner confirmed it - and the settings are good (enabled, 43.5513/7.0127, no key). So
something between `weatherOnScreen()` and `nbSubmitRequest()` did not fire, and **I do not yet
know what**; the next session starts by turning the remote log on (`/api/log?on=1`) and reading
it, not by reasoning about it.

**Corrected the next morning, 2026-09-21.** The paragraph that stood here said this panel had
reported `weatherValid:false` for days on the old firmware too, and concluded that weather was the
wrong first consumer because a module that does not work cannot validate anything. **That was
wrong.** After the panel was power-cycled and came back on `fix/panel-tonight`, `/api/info`
reports `weatherValid: true` with `weatherAgeSeconds: 140` - a fresh fetch, two minutes after
boot, through weather's own task. The weather works.

Which sharpens the finding rather than softening it: weather fetches perfectly well on its own
path, so **`served: 0` on the broker build was a defect in the broker path, not a pre-existing
fault in weather**. Doc 29's "broken" entry for the weather is stale and has been corrected too.
The original criterion in this document - weather first, because it is the simplest and least
visible if it breaks - stands. It was my reasoning about it that did not.

The cause is still not known, and the next session still starts by turning the remote log on and
reading it. But it is now a search for my own bug, with a known-good control to compare against.

---

## A correction about the measurements themselves, 2026-09-21

Several numbers in this document were obtained by comparing one reading of
`largestHeapBlock` against another. **That comparison is much weaker than it
looks**, and I got it wrong twice in one morning before noticing.

The same firmware, on the same board, reports:

| when | good build | broker build |
|---|---|---|
| seconds after boot | 23,540 – 25,588 | 16,372 |
| settled, after the transport pages have run | **16,372** | 16,372 |
| under pressure, portal open or a fetch running | 9,716 – 12,276 | 10,228 – 12,276 |

So the good build's own largest block falls from 25,588 to 16,372 to under
10,000 depending only on what has been running - a swing of more than 15 KB,
larger than the entire change being measured. The figure quoted earlier in this
document, "16,372 B before, 9,716 B after", paired a *settled* good-build
reading with a *pressured* broker-build one. The direction may well be right;
the magnitude was not established.

**What a real measurement of this needs:** both builds read at the same point
in the same sequence - fixed time after boot, same page on screen, no HTTP
traffic in the preceding two seconds (the panel stands aside for a web client
for 1,500 ms, `net_turns.h`, so the tool that measures perturbs the thing) -
and several readings each, not one. That is the project's own rule about
distributions, applied to a number I had been treating as a constant.

Until that is done, the honest statement is narrower than the earlier one: the
broker's `.bss` stack unquestionably removes that many bytes from the heap, and
the flight board unquestionably refuses to fetch below 13,312 B contiguous -
but *how much* contiguity the broker actually costs, against the noise of
normal operation, has not been measured properly yet.
