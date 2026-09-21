#!/usr/bin/env python3
"""Paired measurement of the panel's largest contiguous internal block.

The point of the protocol. `largestHeapBlock` on this board swings by more than
15 KB depending only on what has been running, which is wider than the change
being measured - so a single reading of one build against a single reading of
another settles nothing. This reboots the panel, then samples at fixed offsets
from the first response, with nothing driven in between. Both builds get the
same perturbation from the sampling itself, so the comparison is fair even
though the sampling is not free (the panel stands aside for a web client for
1,500 ms, net_turns.h).

Usage:  paired.py <label> [runs]
Writes <label>.json next to itself and prints a table.
"""
import json
import sys
import time
import urllib.request

HOST = "192.168.4.62"
OFFSETS = [25]   # seconds after the panel first answers


def get_info(timeout=4.0):
    try:
        with urllib.request.urlopen(f"http://{HOST}/api/info", timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except Exception:
        return None


def wait_up(limit=90):
    start = time.time()
    while time.time() - start < limit:
        if get_info(3.0):
            return True
        time.sleep(2)
    return False


def reboot():
    try:
        urllib.request.urlopen(f"http://{HOST}/api/reboot", timeout=4)
    except Exception:
        pass           # the panel drops the connection as it goes; that is the point
    time.sleep(6)      # let it actually leave before we start polling


def one_run():
    reboot()
    if not wait_up():
        return None
    t0 = time.time()
    out = {}
    for off in OFFSETS:
        while time.time() - t0 < off:
            time.sleep(1)
        info = get_info()
        if not info:
            out[off] = None
            continue
        out[off] = {
            "largest": info.get("largestHeapBlock"),
            "free": info.get("freeInternalHeap"),
            "allocFails": info.get("allocFails"),
            "page": None,
        }
    return out


def main():
    label = sys.argv[1] if len(sys.argv) > 1 else "run"
    runs = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    results = []
    for i in range(runs):
        print(f"[{label}] прогон {i+1}/{runs} ...", flush=True)
        r = one_run()
        if r is None:
            print(f"[{label}] прогон {i+1}: панель не вернулась", flush=True)
            continue
        results.append(r)
        for off in OFFSETS:
            v = r.get(off)
            print(f"    T+{off:3d}s  largest {v['largest'] if v else '-'}"
                  f"  free {v['free'] if v else '-'}", flush=True)
    path = f"/private/tmp/claude-502/-Users-apple-LED-MATRIX-APOLLO/e31a0c50-559f-426c-88af-18af10a87d2c/scratchpad/{label}.json"
    with open(path, "w") as f:
        json.dump(results, f, indent=1)
    print(f"[{label}] записано {path}")
    # summary per offset
    print(f"[{label}] сводка: ", end="")
    for off in OFFSETS:
        vals = [r[off]["largest"] for r in results if r.get(off) and r[off]["largest"]]
        if vals:
            print(f"T+{off}s={min(vals)}..{max(vals)} ", end="")
    print()


if __name__ == "__main__":
    main()
