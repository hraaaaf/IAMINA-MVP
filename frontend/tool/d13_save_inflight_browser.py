#!/usr/bin/env python3
"""D13 strict synthetic Flutter Web FUE (real Chromium/real Drift Web)."""
import argparse, json, pathlib, re, shutil, subprocess, sys, time, urllib.request
from playwright.sync_api import sync_playwright

PORT = 7453
VIEWS = ((390,844),(768,1024),(1280,900))

def run(browser, lang, size, out):
    w,h=size
    case=lang+"-"+str(w)+"x"+str(h)
    ctx=browser.new_context(viewport={"width":w,"height":h},locale="ar-SA" if lang=="ar" else "fr-FR")
    page=ctx.new_page()
    failures=[]
    page.on("pageerror",lambda e:failures.append("pageerror:"+str(e)[:220]))
    page.on("requestfailed",lambda r:failures.append("request:"+r.url[:150]))
    proof={"case":case,"result":"FAIL","stages":[],"events":failures}
    try:
        page.goto("http://127.0.0.1:"+str(PORT)+"/?lang="+lang+"&case="+case,wait_until="domcontentloaded",timeout=45000)
        page.wait_for_function("document.documentElement.dataset.d13Stage === 'ready'",timeout=40000)
        assert page.evaluate("document.documentElement.dataset.d13Count")=="0"
        proof["stages"].append("empty")
        page.get_by_role("button",name="D13_OPEN").click(timeout=10000)
        page.get_by_role("textbox").first.fill("126",timeout=10000)
        page.screenshot(path=str(out/("before-"+case+".png")))
        page.get_by_role("button",name=re.compile("Enregistrer|حفظ|Save",re.I)).click(timeout=10000)
        page.wait_for_function("document.documentElement.dataset.d13Stage === 'held'",timeout=15000)
        proof["stages"].append("real_insert_blocked")
        page.screenshot(path=str(out/("pending-"+case+".png")))
        page.get_by_role("button",name=re.compile("Retour|رجوع|عودة|Back",re.I)).first.click(timeout=8000)
        page.wait_for_timeout(300)
        assert page.get_by_role("textbox").count()>0
        assert page.get_by_role("dialog").count()==0
        proof["stages"].append("app_back_refused")
        page.evaluate("window.dispatchEvent(new Event('d13-release'))")
        page.wait_for_function("document.documentElement.dataset.d13Stage === 'written'",timeout=15000)
        page.get_by_text(re.compile(r"126\s*mg/dL")).first.wait_for(timeout=12000)
        proof["stages"].append("receipt")
        page.screenshot(path=str(out/("receipt-"+case+".png")))
        page.reload(wait_until="domcontentloaded")
        page.wait_for_function("document.documentElement.dataset.d13Stage === 'ready'",timeout=40000)
        assert page.evaluate("document.documentElement.dataset.d13Count")=="1"
        proof["stages"].append("exactly_one_after_reload")
        assert not failures, repr(failures)
        proof["result"]="PASS"
    except Exception as e:
        proof["error"]=str(e)[:650]
        try:
            proof["state"]=page.evaluate("""() => ({
              stage:document.documentElement.dataset.d13Stage,
              count:document.documentElement.dataset.d13Count,
              error:document.documentElement.dataset.d13Error,
              text:document.body?.innerText?.slice(0,450)
            })""")
            proof["buttons"]=page.get_by_role("button").all_text_contents()[:15]
            page.screenshot(path=str(out/("failure-"+case+".png")))
        except Exception as x: proof["debug_error"]=str(x)[:150]
    finally:
        (out/("case-"+case+".json")).write_text(json.dumps(proof,ensure_ascii=False,indent=2)+"\n")
        ctx.close()
    return proof

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--build",type=pathlib.Path,required=True)
    p.add_argument("--out",type=pathlib.Path,required=True)
    a=p.parse_args()
    a.out.mkdir(parents=True,exist_ok=True)
    chrome=next((shutil.which(x) for x in ("google-chrome","chromium","chromium-browser") if shutil.which(x)),None)
    if not chrome: raise RuntimeError("Chrome not available")
    server=subprocess.Popen([sys.executable,"-m","http.server",str(PORT),"--bind","127.0.0.1","--directory",str(a.build)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        for _ in range(60):
            try: urllib.request.urlopen("http://127.0.0.1:"+str(PORT),timeout=1);break
            except Exception:time.sleep(.25)
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=chrome,headless=True,args=["--no-sandbox","--disable-dev-shm-usage","--enable-unsafe-swiftshader","--force-renderer-accessibility"])
            cases=[run(browser,l,v,a.out) for l in ("fr","ar") for v in VIEWS]
            browser.close()
        (a.out/"summary.json").write_text(json.dumps(cases,ensure_ascii=False,indent=2)+"\n")
        for c in cases:print(json.dumps({k:c.get(k) for k in ("case","result","stages","error")},ensure_ascii=False),flush=True)
        if any(c["result"]!="PASS" for c in cases):raise AssertionError("D13_FUE_NO_GO")
    finally:
        server.terminate()
        server.wait(timeout=5)

if __name__=="__main__":main()
