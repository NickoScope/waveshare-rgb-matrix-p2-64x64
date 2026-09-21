#!/usr/bin/env python3
"""The owner's symptom, reproduced deliberately: the portal under load while
the rail board is fetching. A browser opening the portal issues 6-12 requests
at once; this does the same, in rounds, and watches what the panel does."""
import concurrent.futures as cf, json, time, urllib.request
H = "192.168.4.62"
PAGES = ["/", "/portal.js", "/portal.css", "/panel.js", "/panel.css",
         "/api/panel", "/api/railboard", "/api/info", "/api/status", "/favicon.ico"]

def one(path):
    try:
        with urllib.request.urlopen(f"http://{H}{path}", timeout=10) as r:
            return r.status, len(r.read())
    except Exception as e:
        code = getattr(e, "code", 0)
        return code, 0

def info():
    try:
        with urllib.request.urlopen(f"http://{H}/api/info", timeout=6) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except Exception:
        return None

rounds, worst_largest, codes = 25, 10**9, {}
start = time.time()
for n in range(rounds):
    with cf.ThreadPoolExecutor(max_workers=10) as ex:
        for st, _ in ex.map(one, PAGES):
            codes[st] = codes.get(st, 0) + 1
    d = info()
    if d:
        worst_largest = min(worst_largest, d["largestHeapBlock"])
        if n % 5 == 4:
            nb = d.get("netBroker") or {}
            print(f"  раунд {n+1:2d}: свободно {d['freeInternalHeap']:6d} "
                  f"крупнейший {d['largestHeapBlock']:6d} отказов {d['allocFails']} "
                  f"брокер served={nb.get('served')} failed={nb.get('failed')} "
                  f"стек-мин {nb.get('stackFreeMin')}", flush=True)
    else:
        print(f"  раунд {n+1:2d}: ПАНЕЛЬ НЕ ОТВЕТИЛА", flush=True)
    time.sleep(2)
print(f"\nитого за {time.time()-start:.0f} c, {rounds*len(PAGES)} запросов")
print("коды ответов:", dict(sorted(codes.items())))
print("худший крупнейший блок:", worst_largest)
d = info()
if d:
    print("после нагрузки: свободно", d["freeInternalHeap"], "крупнейший", d["largestHeapBlock"],
          "отказов выделения", d["allocFails"], "| брокер:", json.dumps(d.get("netBroker")))
else:
    print("после нагрузки: ПАНЕЛЬ НЕ ОТВЕЧАЕТ")
