import json,time,threading,urllib.request
IP="192.168.4.62"
def one(path,res,i,to=25):
    t0=time.time()
    try:
        with urllib.request.urlopen("http://%s%s"%(IP,path),timeout=to) as r:
            res[i]=(path,time.time()-t0,r.status)
    except urllib.error.HTTPError as e: res[i]=(path,time.time()-t0,e.code)
    except Exception as e: res[i]=(path,time.time()-t0,type(e).__name__)
PAGE=["/","/portal.css","/portal.js","/api/portal","/api/status","/api/info",
      "/","/portal.js","/api/fx3d","/api/status","/api/info","/api/diagnostics"]
print("круг  худший  503  ошибки  свободно  блок   отказы  refused")
dead=0
for rnd in range(1,31):
    res={}; ths=[]
    for i,p in enumerate(PAGE):
        t=threading.Thread(target=one,args=(p,res,i)); t.start(); ths.append(t)
    for t in ths: t.join()
    worst=max(res.values(),key=lambda x:x[1])
    n503=sum(1 for r in res.values() if r[2]==503)
    errs=[r for r in res.values() if isinstance(r[2],str)]
    try:
        with urllib.request.urlopen("http://%s/api/info"%IP,timeout=20) as r: d=json.loads(r.read().decode())
        hs="%7s %6s %5s %6s"%(d["freeInternalHeap"],d["largestHeapBlock"],d["allocFails"],d.get("webRefused"))
    except Exception as ex:
        hs="  НЕ ОТВЕЧАЕТ"; dead+=1
    print("%4d %6.2fс %4d %6d   %s"%(rnd,worst[1],n503,len(errs),hs))
    if dead: break
print("\nпроверка живости и 304:")
for k in range(6):
    try:
        with urllib.request.urlopen("http://%s/api/info"%IP,timeout=10) as r:
            d=json.loads(r.read().decode())
        print("  жива: uptime %s, отказов %s, refused %s, wifiFailAgeS %s"%(d["uptime"],d["allocFails"],d.get("webRefused"),d.get("wifiFailAgeS")));break
    except Exception: print("  молчит"); time.sleep(5)
