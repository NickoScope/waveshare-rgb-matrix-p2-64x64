#!/usr/bin/env python3
"""One portal visit, the way a browser does it: a burst of requests for the
page and its assets, then the idle polling a left-open tab does. Not a
stress test - this is the thing the owner actually does."""
import concurrent.futures as cf, json, time, urllib.request
H = "192.168.4.62"
FIRST = ["/", "/portal.css", "/portal.js", "/panel.css", "/panel.js", "/favicon.ico"]
POLL  = ["/api/info", "/api/panel", "/api/railboard"]

def get(p):
    try:
        with urllib.request.urlopen(f"http://{H}{p}", timeout=12) as r:
            return p, r.status, len(r.read())
    except Exception as e:
        return p, getattr(e, "code", 0), 0

print("— открываем портал (одна пачка, как браузер) —")
with cf.ThreadPoolExecutor(max_workers=6) as ex:
    for p, st, n in ex.map(get, FIRST):
        print(f"   {st}  {n:7d} B  {p}")
print("— тикаем, как оставленная открытой вкладка: раз в 5 с, три круга —")
for round_ in range(3):
    time.sleep(5)
    for p in POLL:
        _, st, n = get(p)
        print(f"   {st}  {n:7d} B  {p}")
try:
    with urllib.request.urlopen(f"http://{H}/api/info", timeout=8) as r:
        d = json.loads(r.read().decode())
    print("\nпосле визита: свободно", d["freeInternalHeap"], "крупнейший", d["largestHeapBlock"],
          "отказов выделения", d["allocFails"], "| восстановлений связи", d.get("linkRecoveries"))
except Exception as e:
    print("\nпанель не ответила:", e)
