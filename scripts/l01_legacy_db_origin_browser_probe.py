#!/usr/bin/env python3
"""CI-only synthetic L01: demonstrate whether the legacy Drift read creates amina.

Two phases on the SAME fresh private Chrome profile and local origin:
 - control: Flutter app with no AppDatabase constructor or query
 - legacy_probe: exact AppDatabase.defaults() + hasProtectedMedicalVaultRows()
Never opens a real user's profile or connects to a backend. This is NOT a
schema-migration, encryption, historical-vault or Safari certification.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import time
import urllib.parse
import urllib.request
from pathlib import Path

from websocket import create_connection

ORIGIN = "http://127.0.0.1:7391"
DEVTOOLS = "http://127.0.0.1:9240/json/list"
ARTIFACT_DIR = Path("l01-legacy-db-origin-proof")


def get_page():
    until = time.monotonic() + 40
    while time.monotonic() < until:
        try:
            with urllib.request.urlopen(DEVTOOLS, timeout=2) as response:
                pages = json.load(response)
            return next(item for item in pages if item.get("type") == "page")
        except (OSError, ValueError, StopIteration):
            time.sleep(0.2)
    raise RuntimeError("Chrome DevTools unavailable")


def run():
    chrome = next((shutil.which(name) for name in
                   ("google-chrome", "chromium", "chromium-browser")
                   if shutil.which(name)), None)
    if not chrome:
        raise RuntimeError("Chrome unavailable")

    proof = {
        "scope": "L01 CI-only synthetic local Chrome, no patient data",
        "clinical_or_legacy_vault_certification": "NOT_DONE",
        "prior_legacy_schema_mutation": "NOT_TESTED",
        "safari_webkit": "NOT_RUN",
        "hosted_backend": "NOT_USED",
        "steps": [],
    }

    with tempfile.TemporaryDirectory(prefix="iamina-l01-legacy-origin-") as tmp:
        with Path(tmp, "chrome.log").open("w", encoding="utf-8") as logfile:
            p = subprocess.Popen(
                [
                    chrome, "--headless=new", "--no-sandbox",
                    "--disable-dev-shm-usage", "--enable-unsafe-swiftshader",
                    "--disable-background-networking", "--remote-allow-origins=*",
                    "--remote-debugging-port=9240",
                    f"--user-data-dir={tmp}/chrome-profile", "about:blank",
                ],
                stdout=logfile, stderr=subprocess.STDOUT, start_new_session=True,
            )
            ws = None
            try:
                page = get_page()
                ws = create_connection(page["webSocketDebuggerUrl"], timeout=30)
                ws.settimeout(35)
                next_id = 0
                api_paths = []

                def cdp(method, params=None):
                    nonlocal next_id
                    next_id += 1
                    ident = next_id
                    ws.send(json.dumps({"id": ident, "method": method,
                                        "params": params or {}}))
                    while True:
                        event = json.loads(ws.recv())
                        if event.get("method") == "Network.requestWillBeSent":
                            raw_url = event.get("params", {}).get("request", {}).get("url", "")
                            path = urllib.parse.urlsplit(raw_url).path
                            if path.startswith("/api/"):
                                api_paths.append(path)
                        if event.get("id") == ident:
                            if "error" in event:
                                raise RuntimeError(
                                    f"Chrome CDP command {method} failed")
                            return event.get("result", {})

                cdp("Page.enable")
                cdp("Runtime.enable")
                cdp("Network.enable")
                cdp("IndexedDB.enable")

                def phase(name):
                    cdp("Page.navigate", {"url": f"{ORIGIN}/?phase={name}"})
                    limit = time.monotonic() + 100
                    mounted = False
                    while time.monotonic() < limit:
                        response = cdp("Runtime.evaluate", {
                            "expression": """(() => ({
                              mounted: !!document.querySelector(
                                'flutter-view, flt-glass-pane, flt-scene-host'
                              ),
                              title: document.title,
                            }))()""",
                            "returnByValue": True,
                        })
                        info = response.get("result", {}).get("value") or {}
                        mounted = bool(info.get("mounted")) and (
                            str(info.get("title", "")).casefold() == "iamina")
                        if mounted:
                            break
                        time.sleep(0.3)
                    if not mounted:
                        raise RuntimeError(f"Flutter did not mount in {name}")
                    # Allow deferred Drift worker/IndexedDB operations to settle
                    # after the actual Flutter app has mounted.
                    time.sleep(1.5)
                    return cdp("IndexedDB.requestDatabaseNames", {
                        "securityOrigin": ORIGIN,
                    }).get("databaseNames", [])

                before = phase("control")
                proof["steps"].append({
                    "phase": "control_no_database_code",
                    "indexeddb_names": before,
                    "has_amina": "amina" in before,
                })
                after = phase("legacy_probe")
                proof["steps"].append({
                    "phase": "AppDatabase_defaults_then_protected_rows_select",
                    "indexeddb_names": after,
                    "has_amina": "amina" in after,
                })
                proof["observed_business_api_paths"] = sorted(set(api_paths))
                proof["result"] = (
                    "PASS_CAUSAL_SYNTHETIC_CONTROL"
                    if "amina" not in before and "amina" in after
                    and not api_paths else "FAIL"
                )
                if proof["result"] != "PASS_CAUSAL_SYNTHETIC_CONTROL":
                    raise RuntimeError("Legacy open vs control did not isolate amina")
                return proof
            finally:
                if ws:
                    ws.close()
                p.terminate()
                try:
                    p.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    p.kill()
                    p.wait(timeout=8)


if __name__ == "__main__":
    outcome = {"result": "FAIL", "scope": "synthetic local Chrome"}
    try:
        outcome = run()
    except Exception as exc:
        outcome["failure_class"] = type(exc).__name__
        raise
    finally:
        ARTIFACT_DIR.mkdir(exist_ok=True)
        (ARTIFACT_DIR / "proof.json").write_text(
            json.dumps(outcome, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
