#!/usr/bin/env python3
"""Public, unauthenticated Flutter Web startup comparison for GitHub Actions.

No clinical records, cookies, credentials, or URLs with query strings are stored.
Each cold/warm pair uses a fresh isolated Chromium context. This deliberately
cannot reproduce a real patient's existing IndexedDB vault.
"""
import argparse
import json
import os
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from playwright.sync_api import sync_playwright

TARGETS = {
    "frontend_live": (
        "https://iamina-review.vercel.app/",
        "current public frontend alias; latest deployed SHA must be checked independently",
    ),
    "frontend_preview": (
        "https://iamina-review-lbucreox3-achraf-benmoussa-s-projects.vercel.app/",
        "Vercel preview (51996d18); SSO protection may block unauthenticated CI",
    ),
    "frontend_prior_release": (
        "https://iamina-review-101uvcmqh-achraf-benmoussa-s-projects.vercel.app/",
        "older frontend production deployment (9570e4c); reference only",
    ),
}

INSTRUMENT = r"""
(() => {
  window.__perf = {firstFrame: null, host: null, longTasks: 0, longTaskMs: 0, jsErrorCount: 0, rejectionCount: 0, errorCategories: [], rejectionEvidence: []};
  const classify = (raw) => {
    const msg = String(raw ?? '').toLowerCase();
    if (msg.includes('indexeddatabase') || msg.includes('indexeddb') || msg.includes('idberror')) return 'indexeddb';
    if (msg.includes('secure_storage') || msg.includes('securestorage') || msg.includes('missingpluginexception')) return 'secure_storage_or_plugin';
    if (msg.includes('aborterror') || msg.includes('operationerror')) return 'browser_storage_or_abort';
    if (msg.includes('quotaexceeded') || msg.includes('notreadableerror')) return 'storage_access';
    if (msg.includes('flutter') || msg.includes('dart')) return 'flutter_runtime';
    if (msg.includes('sqlite') || msg.includes('drift') || msg.includes('wasm')) return 'sqlite_or_wasm';
    if (msg.includes('failed to fetch') || msg.includes('networkerror')) return 'network_or_fetch';
    if (msg.includes('firebase')) return 'firebase';
    if (msg.includes('typeerror')) return 'type_error';
    if (msg.includes('securityerror') || msg.includes('notallowederror')) return 'security_policy';
    if (msg.includes('syntaxerror')) return 'syntax_error';
    if (msg.includes('referenceerror')) return 'reference_error';
    return 'other';
  };
  window.addEventListener('error', event => {
    window.__perf.jsErrorCount++;
    window.__perf.errorCategories.push(classify(event.error?.message || event.message));
  });
  window.addEventListener('unhandledrejection', event => {
    window.__perf.rejectionCount++;
    const reason = event.reason;
    const reasonName = String(reason?.name ?? 'unknown');
    const message = String(reason?.message ?? reason ?? '');
    const stack = typeof reason?.stack === 'string' ? reason.stack : '';
    const source = stack.match(/(main\.dart\.js|flutter_bootstrap\.js|flutter\.js|canvaskit\.js|sqlite3\.wasm|drift_worker\.js)(?::(\d+):(\d+))?/);
    const safeNames = ['Error','TypeError','RangeError','ReferenceError','SyntaxError','DOMException','AbortError','SecurityError','StateError','MissingPluginException'];
    const category = classify(message);
    window.__perf.errorCategories.push(category);
    window.__perf.rejectionEvidence.push({
      category,
      reason_name: safeNames.includes(reasonName) ? reasonName : 'other',
      reason_type: Object.prototype.toString.call(reason) === '[object Error]' ? 'Error' : typeof reason,
      message_length: message.length,
      source_file: source ? source[1] : 'unknown',
      source_line: source && source[2] ? Number(source[2]) : null,
      source_column: source && source[3] ? Number(source[3]) : null,
      markers: ['auth','vault','sqlite','drift','index','storage','firebase','wasm','network','fetch','platform','unsupported','permission','null','security','crypto','worker','404','401','403','cors','database','open'].filter(k => message.toLowerCase().includes(k)),
    });
  });
  window.addEventListener('flutter-first-frame', () => {
    window.__perf.firstFrame = performance.now();
  }, {once: true});
  const scan = () => {
    if (window.__perf.host === null &&
        document.querySelector('flutter-view, flt-glass-pane')) {
      window.__perf.host = performance.now();
    }
  };
  new MutationObserver(scan).observe(document, {subtree: true, childList: true});
  document.addEventListener('DOMContentLoaded', scan);
  try {
    new PerformanceObserver(list => {
      for (const entry of list.getEntries()) {
        window.__perf.longTasks++;
        window.__perf.longTaskMs += entry.duration;
      }
    }).observe({type: 'longtask', buffered: true});
  } catch (_) {}
})();
"""

READ_TIMINGS = r"""async () => {
  const navigation = performance.getEntriesByType('navigation')[0];
  const resources = performance.getEntriesByType('resource');
  const patterns = [
    'flutter_bootstrap.js', 'main.dart.js', 'flutter.js',
    'canvaskit.wasm', 'skwasm.wasm', 'sqlite3.wasm', 'drift_worker.js'
  ];
  const assets = resources.filter(r => patterns.some(p => {
    try { return new URL(r.name).pathname.endsWith(p); }
    catch (_) { return false; }
  })).map(r => ({
    file: new URL(r.name).pathname.split('/').pop(),
    duration_ms: Math.round(r.duration),
    encoded_bytes: r.encodedBodySize || null,
    transfer_bytes: r.transferSize || null
  }));
  const api = resources.filter(r => {
    try { return new URL(r.name).pathname.startsWith('/api/'); }
    catch (_) { return false; }
  });
  let storage = {indexeddb_count: null, usage_bytes: null};
  try {
    const estimates = await navigator.storage?.estimate?.();
    storage.usage_bytes = estimates?.usage ?? null;
    storage.indexeddb_count = (await indexedDB.databases?.())?.length ?? null;
  } catch (_) {}
  return {
    title: document.title.slice(0,80),
    has_bootstrap: !!document.querySelector('script[src*="flutter_bootstrap"]'),
    ready_state: document.readyState,
    flutter_element_count: document.querySelectorAll('flutter-view, flt-glass-pane').length,
    flutter_loader_present: typeof window._flutter?.loader?.load === 'function',
    js_error_count: window.__perf.jsErrorCount,
    promise_rejection_count: window.__perf.rejectionCount,
    js_error_categories: window.__perf.errorCategories.slice(0, 15),
    rejection_evidence: window.__perf.rejectionEvidence.slice(0, 4),
    body_tags: Array.from(document.body.children).slice(0, 10).map(e => e.tagName),
    ttfb_ms: navigation ? Math.round(navigation.responseStart) : null,
    dom_content_loaded_ms: navigation ?
       Math.round(navigation.domContentLoadedEventEnd) : null,
    load_event_ms: navigation && navigation.loadEventEnd > 0 ?
       Math.round(navigation.loadEventEnd) : null,
    flutter_first_frame_event_ms: window.__perf.firstFrame === null ? null :
       Math.round(window.__perf.firstFrame),
    flutter_host_ms: window.__perf.host === null ? null :
       Math.round(window.__perf.host),
    long_task_count: window.__perf.longTasks,
    long_task_total_ms: Math.round(window.__perf.longTaskMs),
    assets,
    api_request_count: api.length,
    api_max_ms: api.length ? Math.max(...api.map(r => r.duration)) : null,
    storage
  };
}"""

def med(items, key):
    values = [item.get(key) for item in items]
    values = [v for v in values if isinstance(v, (float, int))]
    return round(statistics.median(values)) if values else None

def one_page(page, label, url, run_no, temperature, observe_ms):
    record = {"target": label, "run": run_no, "phase": temperature, "url": url}
    try:
        response = page.goto(url, wait_until="domcontentloaded", timeout=40000)
        record["http_status"] = response.status if response else None
        page.wait_for_timeout(observe_ms)
        reading = page.evaluate(READ_TIMINGS)
        record.update(reading)
        title = reading.get("title","").lower()
        if record["http_status"] != 200:
            record["classification"] = "http_error"
        elif "vercel" in title and ("login" in title or "authentication" in title):
            record["classification"] = "protected_preview"
        elif not reading.get("has_bootstrap") or "iamina" not in title:
            record["classification"] = "non_flutter_page"
        elif reading.get("flutter_host_ms") is None and reading.get("flutter_first_frame_event_ms") is None:
            record["classification"] = "flutter_unrendered_within_observation_window"
        else:
            record["classification"] = "flutter_observed"
    except Exception as exc:
        record["classification"] = "probe_exception"
        record["error_type"] = type(exc).__name__
    return record

def healthcheck():
    url = "https://iamina-certified.vercel.app/api/v1/health"
    rows = []
    for i in range(3):
        start = time.perf_counter()
        result = {"run": i+1, "endpoint": "/api/v1/health"}
        try:
            with urlopen(Request(url, headers={"Accept":"application/json", "User-Agent":"IAMINA-public-perf-probe/1.0"}), timeout=20) as response:
                result["status"] = response.status
                body = json.loads(response.read(2048))
                result["db"] = body.get("db")
                result["cache"] = body.get("cache")
                result["service_status"] = body.get("status")
        except (HTTPError, URLError, TimeoutError, ValueError, OSError) as exc:
            result["error_type"] = type(exc).__name__
        result["wall_ms"] = round((time.perf_counter() - start)*1000)
        rows.append(result)
    return rows

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--runs",type=int,default=3)
    parser.add_argument("--observe-ms",type=int,default=9000)
    parser.add_argument("--output",default="perf_web_results.json")
    args=parser.parse_args()
    if not 1 <= args.runs <= 5 or not 3000 <= args.observe_ms <= 30000:
        parser.error("runs must be 1..5; observe-ms must be 3000..30000")
    samples=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True)
        try:
            for label,(url,description) in TARGETS.items():
                for i in range(args.runs):
                    context=browser.new_context(service_workers="allow", viewport={"width":390,"height":844})
                    context.add_init_script(script=INSTRUMENT)
                    try:
                        page=context.new_page()
                        for phase in ("cold","warm"):
                            record=one_page(page,label,url,i+1,phase,args.observe_ms)
                            samples.append(record)
                            print(label, phase, "run", i+1, record["classification"],
                                  "ttfb", record.get("ttfb_ms"), "first-frame",
                                  record.get("flutter_first_frame_event_ms"),
                                  "host", record.get("flutter_host_ms"),
                                  "js_errors", record.get("js_error_categories", []),
                                  "rejections", record.get("rejection_evidence", []), flush=True)
                    finally:
                        context.close()
        finally:
            browser.close()
    summary=[]
    for label,(url,description) in TARGETS.items():
        for phase in ("cold","warm"):
            subset=[s for s in samples if s["target"]==label and s["phase"]==phase]
            valid=[s for s in subset if s["classification"] in
                   ("flutter_observed","flutter_unrendered_within_observation_window")]
            summary.append({
                "target":label,"phase":phase,"url":url,"description":description,
                "total":len(subset),"flutter_bootstrap_pages":len(valid),
                "flutter_rendered_pages":sum(s["classification"]=="flutter_observed" for s in subset),
                "classifications":{k:sum(s["classification"]==k for s in subset)
                    for k in sorted({s["classification"] for s in subset})},
                "ttfb_median_ms":med(valid,"ttfb_ms"),
                "flutter_first_frame_median_ms":med(valid,"flutter_first_frame_event_ms"),
                "flutter_host_median_ms":med(valid,"flutter_host_ms"),
                "load_median_ms":med(valid,"load_event_ms"),
                "long_tasks_median_ms":med(valid,"long_task_total_ms"),
                "api_max_median_ms":med(valid,"api_max_ms"),
                "js_error_median_count":med(valid,"js_error_count"),
                "unhandled_rejection_median_count":med(valid,"promise_rejection_count"),
                "error_categories":sorted({c for s in valid for c in s.get("js_error_categories",[])}),
                "rejection_evidence":sorted({json.dumps(e,sort_keys=True) for s in valid for e in s.get("rejection_evidence",[])})[:5],
            })
    health=healthcheck()
    document={
        "timestamp_utc":datetime.now(timezone.utc).isoformat(),
        "runner":os.getenv("RUNNER_OS","unknown"),
        "github_sha":os.getenv("GITHUB_SHA","unknown"),
        "method":"headless Chromium, 390x844, isolated cold + same-context warm; unauthenticated",
        "limitations":[
            "Protected previews do not provide valid Flutter measurements.",
            "Different frontend SHAs and build envs prevent causal attribution.",
            "No returning-patient vault is opened; real IndexedDB/secure-storage latency not measured.",
            "Flutter first-frame event may not fire; missing metric is UNKNOWN, never zero.",
            "Flutter bootstrap presence is not a rendered Flutter frame; report counts separately.",
            "Error evidence includes only allowlisted categories, script basenames, line/columns and keyword markers; never raw error strings.",
            "Resource timing may be restricted across origins; transfer bytes are diagnostic only.",
            "GitHub runner network differs from user device and Moroccan network."
        ],
        "summary":summary,"backend_health":health,"samples":samples,
    }
    Path(args.output).write_text(json.dumps(document,indent=2,ensure_ascii=False),encoding="utf-8")
    lines=["## IAMINA Web — GitHub Actions performance audit",
           "Unauthenticated Chromium only; **not patient-representative**.",
           "","| Target | Mode | Bootstrap / runs | Rendered / runs | TTFB median | Flutter first-frame | Flutter host | JS errors | Status |",
           "|---|---|---:|---:|---:|---:|---:|---:|---|"]
    def fmt(v): return str(v)+" ms" if v is not None else "UNKNOWN"
    for item in summary:
        lines.append("| "+ " | ".join([
            item["target"],item["phase"],
            str(item["flutter_bootstrap_pages"])+"/"+str(item["total"]),
            str(item["flutter_rendered_pages"])+"/"+str(item["total"]),
            fmt(item["ttfb_median_ms"]),fmt(item["flutter_first_frame_median_ms"]),
            fmt(item["flutter_host_median_ms"]),
            str(item["js_error_median_count"])+"/"+str(item["unhandled_rejection_median_count"]),
            ", ".join(k+"="+str(v) for k,v in item["classifications"].items())])+" |")
    lines.extend(["","**Django /api/v1/health**: "+", ".join(
        str(x.get("wall_ms"))+"ms (db="+str(x.get("db","?"))+
        ", cache="+str(x.get("cache","?"))+")" for x in health),
        "", "**Limitations:** "+ "; ".join(document["limitations"])])
    report="\n".join(lines)+"\n"
    Path("perf_web_summary.md").write_text(report,encoding="utf-8")
    if os.getenv("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"],"a",encoding="utf-8") as f:
            f.write(report)
    print(report)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
