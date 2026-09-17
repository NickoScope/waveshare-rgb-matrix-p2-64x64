"""Does the one-shot weather task fetch at the same moments as the old forever-task?

A discrete-time model of both schedulers in Keralots' tree (loop() passes of LOOP_MS):

OLD (upstream bbb861c): one task, forever.
    loop: if not (configured and on screen and wifi): ulTaskNotifyTake(5 s) -> continue
          ok = fetch()                                 (takes FETCH_MS)
          ulTaskNotifyTake(ok ? 10 min : 1 min)
    weatherSettingsChanged(): xTaskNotifyGive -> ends the current wait at once;
    a give while not waiting is remembered and ends the next wait at once.

NEW (branch fix/weather-fetch-task, 7f27643): weatherLoop() every loop pass, a task per fetch,
    one wait window (waitFromMs, waitMs).

Scenarios drive conditions, kicks and fetch results over time; the model records
when each fetch STARTS. The loop() pass is LOOP_MS. Differences up to a loop pass
plus the 5 s check are expected where the old task was in its 5 s poll; anything
else is a behaviour change and is printed.
"""
FETCH_MS = 1800          # a TLS fetch
LOOP_MS = 16             # one loop() pass
POLL = 5000
INTERVAL = 600_000
RETRY = 60_000
U32 = 2**32


class Scenario:
    def __init__(self, name, end, cond, kicks=(), fail_at=(), start=0):
        self.name, self.end, self.cond, self.kicks, self.fail_at, self.start = name, end, cond, set(kicks), fail_at, start

    def ok(self, n):          # result of the n-th fetch
        return n not in self.fail_at


def run_old(sc):
    """The upstream task. Returns (fetch starts, waits) - every wait the task
    slept, in order, as how long it actually lasted."""
    t, starts, waits, n, pending = sc.start, [], [], 0, False
    kicks = sorted(sc.kicks)

    def wait(t, ms):
        nonlocal pending
        if pending:                       # a give that landed during the fetch
            pending = False
            waits.append(("kick", 0))
            return t
        end = t + ms
        for k in kicks:
            if t < k <= end:              # a give ends the wait at once
                waits.append(("kick", 0))
                return k
        waits.append(("full", ms))
        return end

    while t < sc.start + sc.end:
        if not sc.cond(t % U32):
            t = wait(t, POLL)
            continue
        starts.append(t)
        f0 = t
        t += FETCH_MS
        if any(f0 < k <= t for k in kicks):
            pending = True
        t = wait(t, INTERVAL if sc.ok(n) else RETRY)
        n += 1
    return starts, waits


def run_new(sc):
    """Mirrors weatherLoop()/weatherFetchTask() on fix/weather-fetch-task: one
    wait window. Returns (fetch starts, waits), a wait being how long it lasted
    until the loop() pass that ended it."""
    starts, waits, n = [], [], 0
    busy_until = None
    fetch_busy = False
    fetch_kick = False
    wait_from = sc.start % U32
    wait_ms = 0
    first = True
    kicks = sorted(sc.kicks)
    ki = 0
    last_kick_at = None
    kicked = False
    result = None
    t = sc.start
    while t < sc.start + sc.end:
        while ki < len(kicks) and kicks[ki] <= t:
            fetch_kick = True
            last_kick_at = kicks[ki]
            ki += 1
        if fetch_busy and t >= busy_until:          # the task finishes
            wait_from = busy_until % U32
            wait_ms = INTERVAL if result else RETRY
            fetch_busy = False
        if not fetch_busy:                           # one weatherLoop() pass
            now = t % U32
            if fetch_kick:
                fetch_kick = False
                wait_ms = 0
                kicked = True
            if (now - wait_from) % U32 >= wait_ms:
                if not first:
                    if kicked:   # ended by the settings change: how late after it
                        waits.append(("kick", t - max(last_kick_at, busy_until or 0)))
                    else:
                        waits.append(("full", (now - wait_from) % U32))
                first = False
                kicked = False
                if not sc.cond(now):
                    wait_from, wait_ms = now, POLL
                else:
                    starts.append(t)
                    result = sc.ok(n)
                    n += 1
                    fetch_busy = True
                    busy_until = t + FETCH_MS
        t += LOOP_MS
    return starts, waits


MIN = 60_000
scenarios = [
    Scenario("always on screen, 45 min", 45 * MIN, lambda t: True),
    Scenario("not on screen for 12 min, then on", 45 * MIN, lambda t: t >= 12 * MIN),
    Scenario("on, off 3-20 min, on again", 45 * MIN, lambda t: not (3 * MIN <= t < 20 * MIN)),
    Scenario("settings change mid-interval", 30 * MIN, lambda t: True, kicks=[4 * MIN]),
    Scenario("settings change during a fetch", 30 * MIN, lambda t: True, kicks=[1000]),
    Scenario("settings change while not on screen", 30 * MIN, lambda t: t >= 7 * MIN, kicks=[2 * MIN]),
    Scenario("first two fetches fail", 30 * MIN, lambda t: True, fail_at=(0, 1)),
    Scenario("across millis() rollover", 40 * MIN, lambda t: True, start=U32 - 15 * MIN),
]

# The criterion, per the audit of 2026-09-17: compare EVERY wait on its own. A
# full wait may last up to one loop() pass longer than the old task's (it only
# runs on a pass), never shorter; a wait cut short by a settings change must end
# within one pass of that change. Compare a cut wait by its end, not its length:
# the two schedulers' poll grids drift apart, so the same cut wait can have
# started at different moments. Absolute start times
# then drift by at most one pass per wait - that is the honest claim.
bad = 0
for sc in scenarios:
    (os_, ow), (ns, nw) = run_old(sc), run_new(sc)
    k = min(len(ow), len(nw))
    # the old model also records the wait still running when the simulation ends;
    # the new one only records a wait once a loop() pass ends it
    counts_match = len(nw) in (len(ow), len(ow) - 1)
    kinds_match = counts_match and all(ow[i][0] == nw[i][0] for i in range(k))
    # a full wait: how much longer than the old one; a kicked wait: how long after
    # the settings change (or after the fetch it waited for) it ended
    ext = [nw[i][1] - ow[i][1] for i in range(k)]
    ok = len(os_) == len(ns) and kinds_match and all(0 <= e < LOOP_MS for e in ext)
    bad += not ok
    drift = max((abs(a - b) for a, b in zip(os_, ns)), default=0)
    print(f"{'ok ' if ok else 'BAD'} {sc.name:38s} fetches {len(os_)}/{len(ns)}, waits {len(ow)}/{len(nw)}, "
          f"extension per wait {min(ext, default=0)}..{max(ext, default=0)} ms, start drift {drift} ms")
    if not ok:
        bad_i = [i for i, e in enumerate(ext) if not 0 <= e < LOOP_MS or ow[i][0] != nw[i][0]][:5]
        print("     first bad waits (index, old ms, new ms):", [(i, ow[i], nw[i]) for i in bad_i])
print(f"\n{len(scenarios) - bad}/{len(scenarios)} scenarios: every wait ends within one loop() pass of the old task")
