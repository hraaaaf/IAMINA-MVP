#!/usr/bin/env python3
"""D21 real-Chromium first-user functional matrix; fail closed per case."""
import argparse, hashlib, json, pathlib, re, shutil, subprocess, sys, time, urllib.request
from playwright.sync_api import sync_playwright
PORT = 7463
VIEWS = ((390,844),(768,1024),(1280,900))
LABELS = {"fr":("Suivi médical","IAmina","Données & appareils","Confidentialité"),
          "ar":("المتابعة الطبية","IAmina","البيانات والأجهزة","الخصوصية")}

def nodes(cdp):
    return cdp.send("Accessibility.getFullAXTree")["nodes"]

def label(node):
    return str(node.get("name",{}).get("value","")).strip()

def names(cdp):
    return [label(n) for n in nodes(cdp) if label(n)]

def has(seq,s):
    return any(s.casefold() in n.casefold() for n in seq)

def active(cdp):
    return next((label(n) for n in reversed(nodes(cdp))
                 if label(n) and label(n)!="IAMINA"
                 and any(p.get("name")=="focused" and p.get("value",{}).get("value") is True
                         for p in n.get("properties",[]))),None)

def load(page,lang,surface,seed="0",history=False):
    url=f"http://127.0.0.1:{PORT}/?surface={surface}&locale={lang}&seed={seed}"
    if history: url+="&fue_ramadan_history=1"
    page.goto(url,wait_until="domcontentloaded")
    page.wait_for_timeout(12000)

def click_section(page,cdp,word):
    before=names(cdp)
    locator=page.get_by_role("button",name=re.compile(re.escape(word),re.I))
    locator.first.scroll_into_view_if_needed(timeout=4500)
    locator.first.click(timeout=4500)
    page.wait_for_timeout(500)
    expanded = names(cdp)
    if expanded == before:
        return False
    # FUE must prove both directions of the real expansion control.
    locator.first.click(timeout=4500)
    page.wait_for_timeout(500)
    collapsed = names(cdp)
    return collapsed != expanded

def keyboard(page,cdp):
    # Mirror the separately certified RTL/keyboard Chrome harness: CDP
    # keydown/up and real Shift events, with DOM receipts and AX/DOM focus.
    # Run AFTER all four sections have been opened and closed; never reset
    # focus to conceal an interaction-induced keyboard trap.
    page.bring_to_front()
    cdp.send("Page.bringToFront")
    cdp.send("Emulation.setFocusEmulationEnabled", {"enabled": True})
    page.evaluate("""() => {
      window.__d21FUEKeys = [];
      document.addEventListener('keydown', e => window.__d21FUEKeys.push(
        {key:e.key, shift:e.shiftKey, trusted:e.isTrusted}), true);
    }""")
    fw=[];rev=[];dom=[];received=[]
    for index in range(28):
        shift=index>=12
        if shift:
            cdp.send("Input.dispatchKeyEvent", {
                "type":"rawKeyDown","key":"Shift","code":"ShiftLeft",
                "windowsVirtualKeyCode":16,"nativeVirtualKeyCode":16,"modifiers":8})
        for kind in ("rawKeyDown","keyUp"):
            cdp.send("Input.dispatchKeyEvent", {
                "type":kind,"key":"Tab","code":"Tab",
                "windowsVirtualKeyCode":9,"nativeVirtualKeyCode":9,
                "modifiers":8 if shift else 0})
        if shift:
            cdp.send("Input.dispatchKeyEvent", {
                "type":"keyUp","key":"Shift","code":"ShiftLeft",
                "windowsVirtualKeyCode":16,"nativeVirtualKeyCode":16,"modifiers":0})
        page.wait_for_timeout(180)
        (rev if shift else fw).append(active(cdp))
        dom.append(page.evaluate("""() => {
          let n=document.activeElement;
          while(n && n.shadowRoot && n.shadowRoot.activeElement)
            n=n.shadowRoot.activeElement;
          return n ? (n.getAttribute('aria-label') || n.outerHTML.slice(0,180)) : null;
        }"""))
        received=page.evaluate("window.__d21FUEKeys.slice(-6)")
    distinct={x for x in fw if x}
    step=next((i+1 for i,x in enumerate(rev) if x in distinct and x!=fw[-1]),None)
    shift_received=any(e.get("key")=="Shift" and e.get("shift") is True
                       for e in page.evaluate("window.__d21FUEKeys"))
    return {"forward_distinct":len(distinct),"reverse_return_step":step,
            "received_shift_keydown":shift_received,
            "forward":fw,"reverse":rev,"dom_focus":dom,"recent_dom_keys":received}

def run(browser,lang,size,out):
    w,h=size;id=f"{lang}-{w}x{h}";issues=[];proof={}
    ctx=browser.new_context(viewport={"width":w,"height":h},locale=lang)
    page=ctx.new_page();cdp=ctx.new_cdp_session(page)
    cdp.send("Accessibility.enable")
    def check(k,yes,reason):
        if not yes:issues.append({"id":k,"reason":reason})
    try:
        load(page,lang,"profile",seed="1",history=True)
        ax=names(cdp);shot=out/f"profile-history-{id}.png";page.screenshot(path=str(shot))
        proof["history_screenshot"]=shot.name
        check("FUE-01",len(ax)>10 and all(has(ax,s) for s in LABELS[lang]) and
              not any("ramadan" in x.lower() or "رمضان" in x for x in ax),
              "Ramadan not hidden or expected Profile copy missing")
        actions={}
        for s in LABELS[lang]:
            try:actions[s]=click_section(page,cdp,s)
            except Exception as e:actions[s]=str(e)[:200]
        proof["profile_actions"]=actions
        check("FUE-02",all(v is True for v in actions.values()),
              "An actual expansion/touch activation did not change visible AX state")
        keys=keyboard(page,cdp);proof["keyboard"]=keys
        check("FUE-03",keys["forward_distinct"]>=3 and
              keys["reverse_return_step"] is not None and
              keys["received_shift_keydown"],
              "Tab/Shift+Tab after section interactions: focus traversal or Shift delivery failed")

        load(page,lang,"fue-d21-history")
        proof["history_before_reload"]=names(cdp)[:30]
        check("FUE-04",has(names(cdp),"FUE_HISTORY_PRESENT=true"),
              "Saved historic profile interval missing across navigation")
        page.reload(wait_until="domcontentloaded");page.wait_for_timeout(12000)
        check("FUE-04",has(names(cdp),"FUE_HISTORY_PRESENT=true"),
              "Historic Ramadan profile lost on browser reload")
        # First-user browser Back must lead to a usable Profile after history.
        page.go_back(wait_until="domcontentloaded")
        page.wait_for_timeout(12000)
        back_names = names(cdp)
        proof["after_browser_back"] = back_names[:30]
        check("FUE-02", all(has(back_names, x) for x in LABELS[lang]),
              "Browser back did not return to functional Profile")

        load(page,lang,"add-log-meal")
        meal=names(cdp);proof["meal_ax"]=meal[:85]
        banned=("ramadan","رمضان","suhoor","iftar","السحور","الإفطار")
        regular = ("Petit-déjeuner","Déjeuner","Dîner","Collation") if lang == "fr" else (
            "الفطور","الغداء","العشاء","وجبة خفيفة")
        check("FUE-05",len(meal)>10
              and not any(any(token in n.lower() for token in banned) for n in meal)
              and all(has(meal,choice) for choice in regular),
              "Web meal choices must show four regular types and no Ramadan vocabulary")
        shot=out/f"meal-history-{id}.png";page.screenshot(path=str(shot))
        proof["meal_screenshot"]=shot.name

        fresh=browser.new_context(viewport={"width":w,"height":h},locale=lang)
        f=fresh.new_page();fcdp=fresh.new_cdp_session(f);fcdp.send("Accessibility.enable")
        load(f,lang,"profile",seed="0")
        fn=names(fcdp);shot=out/f"profile-first-use-{id}.png";f.screenshot(path=str(shot))
        proof["fresh_screenshot"]=shot.name
        check("FUE-06",all(has(fn,s) for s in LABELS[lang]) and
              not any("ramadan" in n.lower() or "رمضان" in n for n in fn),
              "Fresh profile missing essential controls or displays Ramadan")
        check("FUE-06",f.evaluate("document.documentElement.scrollWidth")<=w+8,
              "Fresh profile horizontal overflow")
        f.reload(wait_until="domcontentloaded");f.wait_for_timeout(12000)
        check("FUE-06",not any("ramadan" in n.lower() or "رمضان" in n
                             for n in names(fcdp)), "Ramadan reappears after reload")
        fresh.close()
    except Exception as e:
        issues.append({"id":"RUNNER","reason":str(e)[:450]})
    finally:
        (out/f"fue-{id}.json").write_text(json.dumps(
            {"locale":lang,"viewport":[w,h],"issues":issues,"evidence":proof,
             "status":"PASS" if not issues else "FAIL"},
            indent=2,ensure_ascii=False)+"\n")
        ctx.close()
    return {"locale":lang,"viewport":[w,h],"status":"PASS" if not issues else "FAIL",
            "issues":issues}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--build",type=pathlib.Path,required=True)
    ap.add_argument("--output",type=pathlib.Path,required=True)
    args=ap.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    chrome=next((shutil.which(x) for x in ("google-chrome","chromium","chromium-browser")
                 if shutil.which(x)),None)
    if not chrome:raise SystemExit("Chrome not installed")
    srv=subprocess.Popen([sys.executable,"-m","http.server",str(PORT),"--bind",
                          "127.0.0.1","--directory",str(args.build)],
                         stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        for _ in range(60):
            try:urllib.request.urlopen(f"http://127.0.0.1:{PORT}/",timeout=1);break
            except Exception:time.sleep(.25)
        else:raise RuntimeError("Web server not ready")
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=chrome,headless=True,
               args=["--no-sandbox","--disable-dev-shm-usage",
                     "--enable-unsafe-swiftshader","--force-renderer-accessibility"])
            results=[run(browser,lang,size,args.output) for lang in LABELS for size in VIEWS]
            browser.close()
        (args.output/"fue-summary.json").write_text(json.dumps(
            {"cases":results,"pass":sum(r["status"]=="PASS" for r in results)},
            ensure_ascii=False,indent=2)+"\n")
        for result in results:print(json.dumps(result,ensure_ascii=False),flush=True)
        if any(x["status"]!="PASS" for x in results):
            raise AssertionError("D21 FUE_NO_GO: inspect complete browser artifacts")
    finally:
        srv.terminate();srv.wait(timeout=5)
if __name__=="__main__": main()
