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

    with tempfile.TemporaryDirectory(
        prefix="iamina-l01-legacy-origin-", ignore_cleanup_errors=True
    ) as tmp:
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
                runtime_errors = []

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
                        if event.get("method") == "Runtime.exceptionThrown":
                            details = event.get("params", {}).get(
                                "exceptionDetails", {})
                            runtime_errors.append(
                                str(details.get("text", "JS exception"))[:350]
                            )
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
                    limit = time.monotonic() + 50
                    last = {}
                    while time.monotonic() < limit:
                        response = cdp("Runtime.evaluate", {
                            "expression": """(() => ({
                              mounted: !!document.querySelector(
                                'flutter-view, flt-glass-pane, flt-scene-host'
                              ),
                              marker: document.documentElement?.getAttribute(
                                'data-l01-phase-result'
                              ) || '',
                              url: location.origin + location.pathname + location.search,
                              ready: document.readyState,
                            }))()""",
                            "returnByValue": True,
                        })
                        info = response.get("result", {}).get("value") or {}
                        last = info
                        if (info.get("mounted") and
                            info.get("ready") == "complete" and
                            info.get("url", "").endswith(f"?phase={name}") and
                            str(info.get("marker", "")).startswith("IAMINA_L01_")):
                            break
                        time.sleep(0.3)
                    else:
                        raise RuntimeError(
                            f"Flutter synthetic phase did not complete in {name}; "
                            f"last={last!r}, runtimeErrors={runtime_errors[-3:]!r}"
                        )
                    # The phase-specific DOM marker is emitted after awaited
                    # database operations; no arbitrary sleep is used as proof.
                    names = cdp("IndexedDB.requestDatabaseNames", {
                        "securityOrigin": ORIGIN,
                    }).get("databaseNames", [])
                    return {"names": names, "title": last["marker"]}

                before = phase("control")
                proof["steps"].append({
                    "phase": "control_no_database_code",
                    "indexeddb_names": before["names"],
                    "has_amina": "amina" in before["names"],
                })
                after = phase("legacy_probe")
                proof["steps"].append({
                    "phase": "AppDatabase_defaults_then_protected_rows_select",
                    "indexeddb_names": after["names"],
                    "has_amina": "amina" in after["names"],
                })

                # The next two phases use ONLY a self-created old-schema fixture
                # on this ephemeral Chrome profile. The v11 profile intentionally
                # contains a fake glucose row and no real patient identity.
                seeded = phase("seed_legacy_v11")
                proof["steps"].append({
                    "phase": "seed_synthetic_legacy_v11",
                    "status": seeded["title"],
                })
                probed = phase("probe_legacy_v11")
                proof["steps"].append({
                    "phase": "presence_only_probe_on_synthetic_v11",
                    "status": probed["title"],
                })
                proof["observed_business_api_paths"] = sorted(set(api_paths))

                causal = "amina" not in before["names"] and "amina" in after["names"]
                fixture = seeded["title"] == "IAMINA_L01_V11_SEEDED"
                v11_result = probed["title"]
                # This is an observational experiment: schema mutation is an
                # important finding, not proof that clinical storage is safe.
                migration_seen = v11_result.startswith(
                    "IAMINA_L01_PROBED_V12_ROWS_1_PROTECTED_true"
                )
                unchanged_version = v11_result.startswith(
                    "IAMINA_L01_PROBED_V11_ROWS_1_PROTECTED_true"
                )
                proof["legacy_v11_inspection"] = {
                    "valid_fixture": fixture,
                    "schema_migration_observed": migration_seen,
                    "schema_unchanged_observed": unchanged_version,
                    "sentinel_row_after_probe": 1 if migration_seen or unchanged_version else "UNKNOWN",
                    "clinical_safety": "NOT_CERTIFIED",
                    "old_database_byte_integrity": "NOT_TESTED",
                    "older_versions_or_opfs": "NOT_TESTED",
                }
                proof["result"] = (
                    "PASS_SYNTHETIC_CAUSALITY_AND_SCHEMA_MIGRATION_OBSERVED"
                    if causal and fixture and migration_seen and not api_paths else
                    "PASS_SYNTHETIC_CAUSALITY_NO_VERSION_CHANGE_OBSERVED"
                    if causal and fixture and unchanged_version and not api_paths else
                    "FAIL"
                )
                # Persist real observations *before* closing Chrome and
                # cleaning its private profile; cleanup must never hide proof.
                ARTIFACT_DIR.mkdir(exist_ok=True)
                (ARTIFACT_DIR / "phase-observations.json").write_text(
                    json.dumps(proof, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
                if not proof["result"].startswith("PASS_SYNTHETIC_CAUSALITY"):
                    raise RuntimeError(
                        "Synthetic legacy v11 verification inconclusive; "
                        f"observations={proof['steps'][-2:]}"
                    )
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
                # Diagnostic-only synthetic Chrome process log. Never a
                # user's profile; truncate to bounded size.
                log_path = Path(tmp, "chrome.log")
                if log_path.exists():
                    ARTIFACT_DIR.mkdir(exist_ok=True)
                    (ARTIFACT_DIR / "chrome-log-tail.txt").write_text(
                        log_path.read_text(encoding="utf-8", errors="replace")[-10000:],
                        encoding="utf-8",
                    )


if __name__ == "__main__":
    outcome = {"result": "FAIL", "scope": "synthetic local Chrome"}
    try:
        outcome = run()
    except Exception as exc:
        outcome["failure_class"] = type(exc).__name__
        outcome["diagnostic"] = str(exc)[:1700]
        raise
    finally:
        ARTIFACT_DIR.mkdir(exist_ok=True)
        (ARTIFACT_DIR / "proof.json").write_text(
            json.dumps(outcome, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
