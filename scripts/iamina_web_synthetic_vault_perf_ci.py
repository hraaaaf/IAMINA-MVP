#!/usr/bin/env python3
"""PERF-WEB synthetic Drift SQLite/IndexedDB benchmark, no patient records.

This times only a subset of app pre-runApp: legacy protected-state probe,
scoped database open, protected-state scan, and real vault controller reconcile
with fake principal. No real AuthService, AppLockService or clinical UI.
"""
import json
import os
import statistics
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright

BUILD = Path("frontend/build/web").resolve()
BROWSERS = ("chromium", "webkit")
PHASES = ("seed", "empty", "populated", "populated", "empty")
METRICS = ("legacy_probe_ms", "scoped_db_open_ms",
           "protected_scan_ms", "controller_reconcile_ms",
           "local_startup_subset_ms", "first_frame_ms")
N_RUNS = 3
TRACK_FIRST_FRAME = """
(() => {
  window.__firstFrame = null;
  window.__rejections = 0;
  window.addEventListener('flutter-first-frame',
    () => { window.__firstFrame = performance.now(); }, {once:true});
  window.addEventListener('unhandledrejection',
    () => { window.__rejections++; });
})();
"""

class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

@contextmanager
def local_server():
    if not (BUILD / "main.dart.js").is_file():
        raise RuntimeError("Synthetic Flutter bundle is missing")
    server = ThreadingHTTPServer(("127.0.0.1", 0),
        partial(QuietHandler, directory=str(BUILD)))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

def navigate(page, base, phase):
    response = page.goto(f"{base}/?phase={phase}",
                         wait_until="domcontentloaded", timeout=45000)
    page.wait_for_function(
        "(x) => document.title.startsWith('IAMINA_PERF_WEB_FAIL:') "
        "|| document.title === 'IAMINA_PERF_WEB_' + x + '_PASS'",
        arg=phase.upper(), timeout=90000)
    title = page.title()
    if title != f"IAMINA_PERF_WEB_{phase.upper()}_PASS":
        raise AssertionError(f"Synthetic startup failed during {phase}: {title}")
    page.wait_for_function("() => window.__firstFrame !== null", timeout=30000)
    result = page.evaluate("""() => ({
      metrics: JSON.parse(localStorage.getItem('iamina_perf_web_synthetic_v1')),
      frame: Math.round(window.__firstFrame),
      rejections: window.__rejections,
      hasFlutter: !!document.querySelector('flutter-view, flt-glass-pane')
    })""")
    if result["metrics"] is None or result["metrics"]["phase"] != phase:
        raise AssertionError("Missing or stale synthetic evidence")
    if result["rejections"] or not result["hasFlutter"]:
        raise AssertionError("Synthetic Flutter app did not render cleanly")
    if response is None or response.status != 200:
        raise AssertionError("Local fixture HTTP response not 200")
    return {**result["metrics"], "first_frame_ms": result["frame"]}

def median(rows, field):
    return round(statistics.median(x[field] for x in rows), 2)

def main():
    samples = []
    with local_server() as origin, sync_playwright() as p:
        for browser_name in BROWSERS:
            browser = getattr(p, browser_name).launch(headless=True)
            try:
                for run in range(1, N_RUNS + 1):
                    context = browser.new_context(
                        locale="en-US", service_workers="block",
                        viewport={"width":390,"height":844})
                    context.add_init_script(script=TRACK_FIRST_FRAME)
                    try:
                        page = context.new_page()
                        for order,phase in enumerate(PHASES):
                            item = navigate(page, origin, phase)
                            if phase == "seed":
                                if item["seeded_rows"] != 300:
                                    raise AssertionError("Synthetic seed not 300 rows")
                                continue
                            item.update({"browser":browser_name, "run":run,
                                         "sequence_index":order})
                            samples.append(item)
                            print(json.dumps({key:item[key] for key in (
                                "browser","run","phase","rows",
                                "local_startup_subset_ms","protected_scan_ms",
                                "controller_reconcile_ms","first_frame_ms"
                            )},sort_keys=True),flush=True)
                    finally:
                        context.close()
            finally:
                browser.close()
    summary=[]
    for browser in BROWSERS:
        for phase in ("empty","populated"):
            subset=[x for x in samples
                    if x["browser"]==browser and x["phase"]==phase]
            if len(subset)!=N_RUNS*2:
                raise AssertionError("Missing browser/phase measurements")
            expected=300 if phase=="populated" else 0
            if any(x["rows"]!=expected or x["protected"]!=(expected>0)
                   or x["legacy_protected"] or not x["controller_has_vault"]
                   for x in subset):
                raise AssertionError("Physical synthetic vault isolation mismatch")
            summary.append({"browser":browser,"phase":phase,"n":len(subset),
                            **{key+"_median_ms":median(subset,key)
                               for key in METRICS}})
    data={
        "timestamp_utc":datetime.now(timezone.utc).isoformat(),
        "head_sha":os.getenv("GITHUB_SHA","unknown"),
        "scope":"Synthetic real Drift Web SQLite/IndexedDB + protected guard + controller",
        "limitations":[
          "This is only part of pre-runApp; AuthService and AppLockService not measured.",
          "Synthetic-only data and fake principal; no patient data or credentials.",
          "Linux Playwright WebKit is not a physical iPhone Safari device.",
          "Measured in fresh browser contexts with two repeats per local vault state.",
          "No real clinical UI, backend latency, or network variability measured."
        ],
        "summary":summary,"samples":samples
    }
    Path("perf_web_synthetic_vault.json").write_text(
        json.dumps(data,indent=2,ensure_ascii=False),encoding="utf-8")
    lines=["## IAMINA PERF-WEB — synthetic IndexedDB startup subset",
           "Real Drift/IndexedDB and controller with synthetic-only content.",
           "", "| Browser | Vault | n | Legacy check | DB open | Guard | Reconcile | Subset | First frame |",
           "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for x in summary:
        def ms(key):
            return str(x[key+"_median_ms"])+" ms"
        lines.append("| "+" | ".join([
            x["browser"],x["phase"],str(x["n"]),ms("legacy_probe"),
            ms("scoped_db_open"),ms("protected_scan"),
            ms("controller_reconcile"),ms("local_startup_subset"),ms("first_frame")
        ])+" |")
    lines.extend(["","**Limitations:** "+"; ".join(data["limitations"])])
    result="\n".join(lines)+"\n"
    Path("perf_web_synthetic_vault.md").write_text(result,encoding="utf-8")
    if os.getenv("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"],"a",encoding="utf-8") as f:
            f.write(result)
    print(result,flush=True)

if __name__=="__main__":
    main()
