#!/usr/bin/env python3
"""IAMINA PERF-WEB public guest-only locale diagnostic; no clinical data."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from playwright.sync_api import sync_playwright

TARGETS = {
 "frontend_live":"https://iamina-review.vercel.app/",
 "frontend_prior_release":"https://iamina-review-101uvcmqh-achraf-benmoussa-s-projects.vercel.app/",
}
LOCALES = (None,"en-US","fr-FR","ar-MA","fr")

INSTRUMENT = r"""
(() => {
 window.__localeAudit={failures:[],rejects:0,firstFrame:null};
 function safeTag(v){
   if(typeof v!=='string')return {type:typeof v};
   if(/^[a-zA-Z][a-zA-Z0-9_-]{0,23}$/.test(v))return {tag:v};
   return {type:'non_locale_or_redacted',length:v.length};
 }
 for(const key of ['Locale','DateTimeFormat','NumberFormat','RelativeTimeFormat']){
   const original=Intl[key];
   if(typeof original!=='function')continue;
   Intl[key]=new Proxy(original,{
     construct(target,args,newTarget){
       try{return Reflect.construct(target,args,newTarget);}
       catch(e){
         window.__localeAudit.failures.push({
           api:key,operation:'construct',first_arg:safeTag(args[0]),
           error_name:String(e?.name||'Error').slice(0,25)
         });throw e;
       }
     },
     apply(target,thisArg,args){
       try{return Reflect.apply(target,thisArg,args);}
       catch(e){
         window.__localeAudit.failures.push({
           api:key,operation:'call',first_arg:safeTag(args[0]),
           error_name:String(e?.name||'Error').slice(0,25)
         });throw e;
       }
     }
   });
 }
 window.addEventListener('unhandledrejection',()=>window.__localeAudit.rejects++);
 window.addEventListener('flutter-first-frame',
   ()=>window.__localeAudit.firstFrame=performance.now(),{once:true});
})();
"""
READ = r"""() => ({
 language:navigator.language,
 resolved_locale:Intl.DateTimeFormat().resolvedOptions().locale,
 invalid_locale_calls:(window.__localeAudit?.failures||[]).slice(0,12),
 rejects:window.__localeAudit?.rejects||0,
 flutter_host:!!document.querySelector('flutter-view, flt-glass-pane'),
 first_frame_ms:window.__localeAudit?.firstFrame===null?null:
   Math.round(window.__localeAudit.firstFrame),
 bootstrap:!!document.querySelector('script[src*="flutter_bootstrap"]')
})"""

def main():
 records=[]
 with sync_playwright() as pw:
  browser=pw.chromium.launch(headless=True)
  try:
   for name,url in TARGETS.items():
    for locale in LOCALES:
     options={"viewport":{"width":390,"height":844},"service_workers":"block"}
     if locale is not None: options["locale"]=locale
     context=browser.new_context(**options)
     context.add_init_script(script=INSTRUMENT)
     item={"frontend":name,"requested_locale":locale or "default"}
     try:
      page=context.new_page()
      response=page.goto(url,wait_until="domcontentloaded",timeout=30000)
      item["http_status"]=response.status if response else None
      page.wait_for_timeout(7000)
      item.update(page.evaluate(READ))
     except Exception as e:
      item["probe_error_type"]=type(e).__name__
     finally:
      context.close()
     records.append(item)
     print(json.dumps(item,ensure_ascii=False),flush=True)
  finally:
   browser.close()
 result={
  "date_utc":datetime.now(timezone.utc).isoformat(),
  "head_sha":os.getenv("GITHUB_SHA","unknown"),
  "privacy":"Fresh guest Chromium; no cookies, credentials, clinical data, raw exceptions, URLs with query parameters.",
  "records":records,
 }
 Path("perf_web_locale_matrix.json").write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding="utf-8")
 lines=["## IAMINA PERF-WEB — Intl Locale startup matrix",
  "Anonymous Chromium at 390×844; 7-second observation; not patient representative.","",
  "| Frontend | Browser locale | Intl resolved | Invalid Intl call | Rejects | Flutter frame |",
  "|---|---|---|---|---:|---|"]
 for r in records:
  failures=", ".join(x["api"]+"("+str(x["first_arg"].get("tag",x["first_arg"].get("type","?")))+")"
    for x in r.get("invalid_locale_calls",[])) or "none"
  rendered=r.get("flutter_host",False) or r.get("first_frame_ms") is not None
  lines.append("| "+" | ".join([
   r["frontend"],r["requested_locale"],r.get("resolved_locale","UNKNOWN"),
   failures,str(r.get("rejects","UNKNOWN")),"YES" if rendered else "NO"
  ])+" |")
 lines.extend(["","The Intl proxy observes exceptions then rethrows unchanged; correlation does not prove a production-user regression."])
 summary="\n".join(lines)+"\n"
 Path("perf_web_locale_matrix.md").write_text(summary,encoding="utf-8")
 if os.getenv("GITHUB_STEP_SUMMARY"):
  with open(os.environ["GITHUB_STEP_SUMMARY"],"a",encoding="utf-8") as f:f.write(summary)
 print(summary)
 return 0

if __name__=="__main__":
 raise SystemExit(main())
