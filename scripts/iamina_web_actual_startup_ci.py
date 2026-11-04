#!/usr/bin/env python3
"""Real Flutter Web anonymous startup in a disposable Chromium profile.

No synthetic vault, patient records, credentials or production backend.
BEFORE (normal page) vs AFTER (optional timing readout), same viewports.
iPhone Safari is NOT tested in this CI job.
"""
import json
import os
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path("frontend/build/web").resolve()
OUT = Path("perf_web_actual_startup")
SIZES = ((390, 844), (430, 932), (768, 1024), (1280, 900))
REQUIRED = {
    "iamina.startup.main_enter",
    "iamina.startup.auth_ready",
    "iamina.startup.legacy_probe_ready",
    "iamina.startup.scoped_probe_ready",
    "iamina.startup.lock_ready",
    "iamina.startup.vault_reconcile_ready",
    "iamina.startup.runapp_begin",
    "iamina.startup.user_marked_usable",
}


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        return


@contextmanager
def server():
    if not (ROOT / "main.dart.js").is_file():
        raise RuntimeError("Real Flutter release Web build missing")
    httpd = ThreadingHTTPServer(
        ("127.0.0.1", 0), partial(QuietHandler, directory=str(ROOT))
    )
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield "http://127.0.0.1:" + str(httpd.server_port)
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=5)


def timings(page):
    return page.evaluate("""() => ({
      milestones: performance.getEntriesByType('mark')
        .filter(m => m.name.startsWith('iamina.startup.'))
        .map(m => ({name:m.name,ms:Math.round(m.startTime)})),
      has_flutter_host: !!document.querySelector('flutter-view, flt-glass-pane'),
      has_opt_in_panel: !!document.getElementById('iamina-startup-perf-tool')
    })""")


def run():
    OUT.mkdir(exist_ok=True)
    evidence = []
    with server() as base, sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        try:
            for width, height in SIZES:
                context = browser.new_context(
                    locale="fr-FR",
                    viewport={"width": width, "height": height},
                    device_scale_factor=1,
                    service_workers="block",
                )
                try:
                    page = context.new_page()
                    errors = []
                    page.on("pageerror", lambda e: errors.append(type(e).__name__))

                    baseline = page.goto(base + "/", wait_until="domcontentloaded",
                                         timeout=45000)
                    assert baseline is not None and baseline.status == 200
                    page.wait_for_selector("flutter-view, flt-glass-pane",
                                           timeout=60000)
                    page.wait_for_timeout(350)
                    assert page.locator("#iamina-startup-perf-tool").count() == 0
                    page.screenshot(path=str(OUT / ("before_%d.png" % width)))

                    result = page.goto(base + "/?startup_perf=1",
                                       wait_until="domcontentloaded", timeout=45000)
                    assert result is not None and result.status == 200
                    page.wait_for_function("""() =>
                      performance.getEntriesByType('mark')
                        .some(m => m.name === 'iamina.startup.runapp_begin')
                      && !!document.querySelector('flutter-view, flt-glass-pane')
                    """, timeout=60000)

                    root = page.locator("#iamina-startup-perf-tool")
                    assert root.count() == 1
                    root.locator("#toggle").click()
                    assert root.locator("#panel").get_attribute("open") is not None
                    root.locator("#ready").click()
                    reading = timings(page)
                    names = {item["name"] for item in reading["milestones"]}
                    missing = REQUIRED - names
                    if missing:
                        raise AssertionError("Missing safe performance milestones: "+
                                             repr(sorted(missing)))
                    assert reading["has_flutter_host"]
                    assert reading["has_opt_in_panel"]
                    assert not errors, "Browser page errors occurred"
                    text = root.locator("#result").inner_text()
                    assert "local_only_no_patient_data" in text
                    assert "milestone_ms_since_navigation" in text
                    assert "iamina.startup." not in text or "main_enter" in text
                    page.screenshot(path=str(OUT / ("after_%d.png" % width)))

                    evidence.append({
                        "viewport": "%dx%d" % (width, height),
                        "normal_page_no_overlay": True,
                        "optional_overlay_visible": True,
                        "flutter_host": reading["has_flutter_host"],
                        "marks": reading["milestones"],
                        "page_error_count": len(errors),
                    })
                finally:
                    context.close()
        finally:
            browser.close()
    proof = {
        "result": "PASS",
        "source": "Actual compiled Flutter Web, guest flow only",
        "privacy": "disposable sessions, numeric allowlisted marks, no patient data",
        "real_iphone_safari": "NOT_RUN",
        "returning_patient_vault": "NOT_RUN",
        "hosted_preview": "NOT_DEPLOYED",
        "sha": os.getenv("GITHUB_SHA", "unknown"),
        "at_utc": datetime.now(timezone.utc).isoformat(),
        "viewports": evidence,
    }
    (OUT / "proof.json").write_text(json.dumps(proof, indent=2), encoding="utf-8")
    print(json.dumps({
        "result": proof["result"],
        "viewports_passed": len(evidence),
        "iphone_safari": proof["real_iphone_safari"],
    }))


if __name__ == "__main__":
    run()
