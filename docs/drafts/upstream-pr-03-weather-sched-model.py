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
    t, starts, n, pending = sc.start, [], 0, False
    kicks = sorted(sc.kicks)

    def wait(t, ms):
        nonlocal pending
        if pending:
            pending = False
            return t
        end = t + ms
        for k in kicks:
            if t < k <= end:
                return k
        return end

    while t < sc.start + sc.end:
        # a kick that lands while the task is fetching becomes pending
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
    return starts


def run_new(sc):
    """Mirrors weatherLoop()/weatherFetchTask() in 7f27643: one wait window."""
    starts, n = [], 0
    busy_until = None
    fetch_busy = False
    fetch_kick = False
    wait_from = sc.start % U32
    wait_ms = 0
    kicks = sorted(sc.kicks)
    ki = 0
    result = None
    t = sc.start
    while t < sc.start + sc.end:
        while ki < len(kicks) and kicks[ki] <= t:
            fetch_kick = True
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
            if (now - wait_from) % U32 >= wait_ms:
                if not sc.cond(now):
                    wait_from, wait_ms = now, POLL
                else:
                    starts.append(t)
                    result = sc.ok(n)
                    n += 1
                    fetch_busy = True
                    busy_until = t + FETCH_MS
        t += LOOP_MS
    return starts


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

bad = 0
for sc in scenarios:
    old, new = run_old(sc), run_new(sc)
    # align: the new scheduler checks every 5 s from boot and on loop passes
    pairs = list(zip(old, new))
    worst = max((abs(a - b) for a, b in pairs), default=0)
    same_count = len(old) == len(new)
    ok = same_count and worst <= POLL + LOOP_MS
    bad += not ok
    rel = lambda xs: [round((x - sc.start) / 1000, 1) for x in xs]
    print(f"{'ok ' if ok else 'BAD'} {sc.name:40s} fetches old {len(old)} new {len(new)}, worst start gap {worst} ms")
    if not ok:
        print("     old s:", rel(old))
        print("     new s:", rel(new))
print(f"\n{len(scenarios) - bad}/{len(scenarios)} scenarios match")
