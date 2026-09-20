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
