#!/usr/bin/env python3
"""The panel's functional sweep, from docs/29-panel-control-map.md.

Why this exists as a script and not a checklist. Doc 29 is the standing answer
to "what can the panel do and how do I drive it", and it has twice recorded a
mistake that a human reading it still made: a payload that answers success and
does nothing. A checklist cannot catch that. This drives every page and reads
the state back, so "it worked" is a comparison rather than an impression.

It is deliberately gentle - one request at a time, paced - because the panel
stands aside for a web client for 1,500 ms (net_turns.h), and a sweep that
hammers it measures the sweep rather than the panel. The stress case is
scratchpad/stress.py and it is a different question.

    python3 functional.py [--host IP] [--quick]

Exit code 0 when everything passed, 1 when anything failed, 4 when the panel
could not be reached at all.
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.request

PAGES = [
    (0, "CLOCK"), (1, "FOOTBALL CLOCK"), (2, "MINECRAFT"), (3, "ROOM RADAR"),
    (4, "SNAKE CLOCK"), (5, "SNOOKER CLOCK"), (6, "TETRIS CLOCK"), (7, "WORLD CLOCK"),
    (8, "FLIGHTS"), (9, "TRAINS"), (10, "MARKETS"), (11, "TICKER"),
    (12, "PORTFOLIO"), (13, "HOLDINGS"), (14, "YACHTS"), (15, "MEDIA"),
]
# Styles that exist in this build, from /api/panel's own styles[].
PORTAL_ASSETS = ["/", "/portal.css", "/portal.js", "/panel.css", "/panel.js", "/favicon.ico"]

PASS, FAIL = [], []


def note(ok, what, detail=""):
    (PASS if ok else FAIL).append(what)
    mark = "ok  " if ok else "ПЛОХО"
    print(f"  {mark} {what}{(' - ' + detail) if detail else ''}", flush=True)


def get(host, path, timeout=10.0):
    try:
        with urllib.request.urlopen(f"http://{host}{path}", timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, b""
    except Exception:
        return 0, b""


def get_json(host, path, timeout=10.0):
    st, body = get(host, path, timeout)
    if st != 200:
        return st, None
    try:
        return st, json.loads(body.decode("utf-8", "replace"))
    except Exception:
        return st, None


def post(host, path, payload, timeout=10.0):
    req = urllib.request.Request(f"http://{host}{path}", data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, b""
    except Exception:
        return 0, b""


def retrying(fn, tries=6, wait=6.0):
    """The panel answers 503 while it is busy; that is the back-off working, not
    a failure. Retry a few times before calling anything broken."""
    for _ in range(tries):
        st, val = fn()
        if st == 200:
            return st, val
        time.sleep(wait)
    return st, val


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="192.168.4.62")
    ap.add_argument("--quick", action="store_true", help="pages only, no data checks")
    args = ap.parse_args()
    host = args.host

    print("=== до прогона ===")
    st, before = retrying(lambda: get_json(host, "/api/info"))
    if not before:
        print("ПАНЕЛЬ НЕ ОТВЕЧАЕТ")
        return 4
    nb = before.get("netBroker") or {}
    print(f"  прошивка {before.get('version')} build {before.get('build')}")
    print(f"  свободно {before['freeInternalHeap']} крупнейший {before['largestHeapBlock']}"
          f" отказов {before['allocFails']} обрывов связи {before.get('linkRecoveries')}")
    print(f"  посредник {json.dumps(nb)}")

    print("\n=== страницы: ставим и читаем обратно ===")
    for num, name in PAGES:
        st, _ = post(host, "/api/panel", {"show": {"page": num}})
        if st != 200:
            time.sleep(6)
            st, _ = post(host, "/api/panel", {"show": {"page": num}})
        time.sleep(2.0)
        _, panel = retrying(lambda: get_json(host, "/api/panel"), tries=4, wait=5)
        now = (panel or {}).get("now", {})
        got = now.get("page")
        note(got == num, f"страница {num} {name}",
             "" if got == num else f"панель на {got} ({now.get('name')})")

    print("\n=== стили часов ===")
    _, panel = retrying(lambda: get_json(host, "/api/panel"))
    styles = [s["id"] for s in (panel or {}).get("styles", [])]
    post(host, "/api/panel", {"show": {"page": 0}})
    time.sleep(1.5)
    for sid in styles[:6] + ([14] if 14 in styles else []):
        post(host, "/api/panel", {"style": sid})
        time.sleep(1.5)
        _, panel = retrying(lambda: get_json(host, "/api/panel"), tries=3, wait=4)
        got = (panel or {}).get("now", {}).get("style")
        note(got == sid, f"стиль {sid}", "" if got == sid else f"панель на {got}")

    if not args.quick:
        print("\n=== данные табло ===")
        checks = [
            ("/api/railboard", "жд-табло",
             lambda d: (d.get("direct") or {}).get("state") in ("OK", "WAITING", "DAY CAP", "CAP")),
            ("/api/flightboard", "авиа-табло",
             lambda d: isinstance(d.get("direct"), dict)),
            ("/api/worldclock", "мировые часы", lambda d: d is not None),
            ("/api/market", "рынки", lambda d: d is not None),
            ("/api/media", "медиа", lambda d: d is not None),
        ]
        for path, name, ok in checks:
            st, d = retrying(lambda p=path: get_json(host, p), tries=4, wait=6)
            note(st == 200 and d is not None and ok(d), name,
                 "" if st == 200 else f"HTTP {st}")
        st, d = retrying(lambda: get_json(host, "/api/info"))
        note(bool(d and d.get("weatherValid")), "погода получена",
             f"возраст {d.get('weatherAgeSeconds')} c" if d else "")

    print("\n=== портал ===")
    for path in PORTAL_ASSETS:
        st, body = get(host, path, timeout=15)
        if st == 503:
            time.sleep(6)
            st, body = get(host, path, timeout=15)
        note(st == 200 and len(body) > 0, f"портал {path}", f"HTTP {st}, {len(body)} B")

    print("\n=== диагностика ===")
    # Retried, with a bound, and the count reported. **Not to make it go green**:
    # a 503 here is the panel's designed back-off, and the sweep's own traffic -
    # six portal assets including a 39 KB file, moments earlier - is what raises
    # it. A test that fails on designed behaviour tests the wrong thing; one that
    # retries without a bound hides a panel that is genuinely stuck. So: bounded,
    # and a run that needed three attempts reads differently from one that needed
    # none, instead of both saying "ok".
    for path in ("/api/info", "/api/diagnostics", "/api/status", "/metrics"):
        tries = 0
        st, body = 0, b""
        for tries in range(1, 5):
            st, body = get(host, path)
            if st == 200:
                break
            time.sleep(5)
        note(st == 200 and len(body) > 0, f"диагностика {path}",
             f"HTTP {st}" if st != 200 else (f"со {tries}-й попытки" if tries > 1 else ""))

    print("\n=== после прогона ===")
    st, after = retrying(lambda: get_json(host, "/api/info"))
    if not after:
        note(False, "панель отвечает после прогона")
        print(f"\nПРОВАЛЕНО: {len(FAIL)} из {len(PASS) + len(FAIL)}")
        return 1
    nb = after.get("netBroker") or {}
    print(f"  свободно {after['freeInternalHeap']} крупнейший {after['largestHeapBlock']}")
    print(f"  отказов выделения {after['allocFails']} (было {before['allocFails']})"
          f"  задача: {after.get('allocFailTask') or '-'}")
    print(f"  обрывов связи {after.get('linkRecoveries')} (было {before.get('linkRecoveries')})")
    print(f"  посредник {json.dumps(nb)}")
    note(after.get("linkRecoveries", 0) == before.get("linkRecoveries", 0),
         "связь не рвалась за прогон")
    note((after.get("lastCrash") or {}).get("thisBoot") is not True,
         "краха в этой загрузке не было")

    total = len(PASS) + len(FAIL)
    if FAIL:
        print(f"\nПРОВАЛЕНО {len(FAIL)} из {total}:")
        for f in FAIL:
            print("   -", f)
        return 1
    print(f"\nВСЁ ПРОЙДЕНО: {total} проверок")
    return 0


if __name__ == "__main__":
    sys.exit(main())
