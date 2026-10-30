#!/usr/bin/env python3
"""D7 Web: physical Chrome IndexedDB treatment declarations A/B/A.

Synthetic fixture only. Does not prove auth, UI save, encryption, clinical
accuracy, browser offline mode, or lawful patient-data processing.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from contextlib import contextmanager
import time
import urllib.request
from pathlib import Path

ORIGIN = "http://127.0.0.1:7377"
DEVTOOLS = "http://127.0.0.1:9237/json/list"
PHASES = (
    "seed_a", "seed_b", "verify_a", "verify_b",
    "edit_a", "verify_a_edited", "none_b", "verify_b_none",
    "verify_a_edited",
)

# Decision-specific synthetic returning patient, no account-switch itinerary.
SINGLE_PATIENT_PHASES = (
    "single_seed", "single_verify_seed", "single_type1",
    "single_verify_type1", "single_none", "single_verify_none",
)


def _chrome() -> str:
    for name in ("google-chrome", "chromium", "chromium-browser"):
        value = shutil.which(name)
        if value:
            return value
    raise RuntimeError("Chrome executable unavailable")


def _tab():
    until = time.monotonic() + 35
    while time.monotonic() < until:
        try:
            with urllib.request.urlopen(DEVTOOLS, timeout=2) as response:
                entries = json.load(response)
            return next(x for x in entries if x.get("type") == "page")
        except (OSError, ValueError, StopIteration):
            time.sleep(0.25)
    raise RuntimeError("Synthetic Chrome tab did not start")


@contextmanager
def _ephemeral_chrome_profile():
    # Chrome can keep asynchronously-created Default/* files briefly alive
    # even after the PID exits. Test result must not be mistaken for an I/O
    # permission regression during temporary profile cleanup.
    temp = tempfile.mkdtemp(prefix="iamina-d7-indexeddb-")
    try:
        yield temp
    finally:
        shutil.rmtree(temp, ignore_errors=True)


def main() -> None:
    from websocket import create_connection

    single_patient = len(sys.argv) > 1 and sys.argv[1] == "--single-patient"
    if len(sys.argv) > 1 and not single_patient:
        raise ValueError("Unsupported D7 Chrome probe option")
    phases = SINGLE_PATIENT_PHASES if single_patient else PHASES
    reload_phase = "single_verify_none" if single_patient else "verify_a_edited"
    proof_file = (
        "d7-web-single-patient-proof.json" if single_patient
        else "d7-web-indexeddb-proof.json"
    )

    with _ephemeral_chrome_profile() as tmp:
        with Path(tmp, "chrome.log").open("w", encoding="utf-8") as logfile:
            proc = subprocess.Popen(
                [
                    _chrome(), "--headless=new", "--no-sandbox",
                    "--disable-dev-shm-usage", "--enable-unsafe-swiftshader",
                    "--remote-allow-origins=*", "--remote-debugging-port=9237",
                    f"--user-data-dir={tmp}/user",
                    f"{ORIGIN}/?phase={phases[0]}",
                ],
                stdout=logfile, stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            ws = None
            try:
                tab = _tab()
                ws = create_connection(tab["webSocketDebuggerUrl"], timeout=25)
                index = 0

                def command(method: str, params: dict | None = None) -> dict:
                    nonlocal index
                    index += 1
                    ws.send(json.dumps({
                        "id": index, "method": method, "params": params or {}
                    }))
                    while True:
                        response = json.loads(ws.recv())
                        if response.get("id") == index:
                            if "error" in response:
                                raise RuntimeError(f"CDP command failed: {method}")
                            return response.get("result", {})

                command("Page.enable")
                command("Runtime.enable")

                def observe(phase: str) -> None:
                    expected = f"IAMINA_D7_{phase.upper()}_PASS"
                    until = time.monotonic() + 80
                    last = ""
                    while time.monotonic() < until:
                        current = command("Runtime.evaluate", {
                            "expression": "document.title",
                            "returnByValue": True,
                        })
                        last = current.get("result", {}).get("value", "")
                        if last == expected:
                            return
                        if last.startswith("IAMINA_D7_FAIL:"):
                            raise RuntimeError(f"D7 physical vault phase {phase} failed: {last}")
                        time.sleep(0.25)
                    raise RuntimeError(f"D7 phase {phase} timed out: {last}")

                for phase in phases:
                    command("Page.navigate", {"url": f"{ORIGIN}/?phase={phase}"})
                    observe(phase)

                # Reload A after B changes. The same Chrome profile must retain
                # physical databases and the owner-scoped, pending declaration.
                command("Page.reload", {"ignoreCache": True})
                observe(reload_phase)

                output = {
                    "result": "PASS",
                    "type": "real Chrome, sqlite3.wasm, IndexedDB",
                    "fixture": "synthetic-only",
                    "decision": (
                        "D7 single returning patient declared type/treatment"
                        if single_patient else "legacy physical vault boundary"
                    ),
                    "sequence": phases,
                    "hard_reload": reload_phase,
                    "claim_limit": (
                        "Physical patient vault persistence/isolation and "
                        "declaration state only; NOT full UI/auth/offline/clinical FUE"
                    ),
                }
                Path(proof_file).write_text(
                    json.dumps(output, sort_keys=True, indent=2) + "\n",
                    encoding="utf-8",
                )
                print(json.dumps(output, sort_keys=True, indent=2))
            finally:
                if ws is not None:
                    ws.close()
                proc.terminate()
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=5)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"D7 IndexedDB proof failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
