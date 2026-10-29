#!/usr/bin/env python3
"""D7 Chrome real controller / IndexedDB integration with synthetic A-B-A.

No real login, UI clicks, Vercel access, secrets or real patient data.
"""
import json
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path
from websocket import create_connection

ORIGIN = "http://127.0.0.1:7381"
DEVTOOLS = "http://127.0.0.1:9239/json/list"
PHASES = (
    "seed_a", "seed_b", "verify_a", "verify_b", "edit_a",
    "verify_a_edited", "switch_a_b_a", "verify_b", "verify_a_edited",
)


def executable():
    for name in ("google-chrome", "chromium", "chromium-browser"):
        path = shutil.which(name)
        if path:
            return path
    raise RuntimeError("Chrome unavailable")


def page():
    end = time.monotonic() + 35
    while time.monotonic() < end:
        try:
            with urllib.request.urlopen(DEVTOOLS, timeout=2) as response:
                pages = json.load(response)
            return next(x for x in pages if x.get("type") == "page")
        except (OSError, ValueError, StopIteration):
            time.sleep(0.25)
    raise RuntimeError("CDP unavailable")


def run():
    proof = {
        "result": "FAIL",
        "scope": "real PatientVaultSessionController + Web SQLite/IndexedDB + real treatment store",
        "principal": "FAKE notifier with synthetic IDs 734/812; NOT AuthService credential login",
        "ui": "NOT_RUN: no ProfileScreen interaction",
        "hosted_vercel": "NOT_RUN",
        "clinical_privacy": "NOT_RUN",
        "phases": list(PHASES),
        "passed_phases": [],
    }
    with tempfile.TemporaryDirectory(prefix="iamina-d7-aba-",
                                     ignore_cleanup_errors=True) as directory:
        with (Path(directory) / "chrome.log").open("w") as logfile:
            proc = subprocess.Popen([
                executable(), "--headless=new", "--no-sandbox",
                "--disable-dev-shm-usage", "--enable-unsafe-swiftshader",
                "--remote-allow-origins=*", "--remote-debugging-port=9239",
                f"--user-data-dir={directory}/profile",
                f"{ORIGIN}/?phase=seed_a",
            ], stdout=logfile, stderr=subprocess.STDOUT, start_new_session=True)
            ws = None
            try:
                info = page()
                ws = create_connection(info["webSocketDebuggerUrl"], timeout=25)
                seq = 0

                def command(method, params=None):
                    nonlocal seq
                    seq += 1
                    ws.send(json.dumps({"id": seq, "method": method,
                                        "params": params or {}}))
                    while True:
                        response = json.loads(ws.recv())
                        if response.get("id") == seq:
                            if "error" in response:
                                raise RuntimeError(f"CDP command {method} failed")
                            return response.get("result", {})

                command("Page.enable")
                command("Runtime.enable")

                def check(phase):
                    expected = f"IAMINA_D7_CTRL_{phase.upper()}_PASS"
                    end = time.monotonic() + 90
                    last = ""
                    while time.monotonic() < end:
                        r = command("Runtime.evaluate", {
                            "expression": "document.title", "returnByValue": True,
                        })
                        last = r.get("result", {}).get("value", "")
                        if last == expected:
                            proof["passed_phases"].append(phase)
                            return
                        if last.startswith("IAMINA_D7_CTRL_FAIL:"):
                            raise RuntimeError(f"controller phase {phase}: {last}")
                        time.sleep(0.25)
                    raise RuntimeError(f"controller phase {phase} timed out: {last}")

                for phase in PHASES:
                    command("Page.navigate", {"url": f"{ORIGIN}/?phase={phase}"})
                    check(phase)
                command("Page.reload", {"ignoreCache": True})
                check("verify_a_edited")
                proof["result"] = "PASS"
            finally:
                if ws is not None:
                    ws.close()
                proc.terminate()
                try:
                    proc.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=8)
    return proof


if __name__ == "__main__":
    target = Path("d7-web-controller-aba-proof.json")
    try:
        data = run()
        target.write_text(json.dumps(data, indent=2), encoding="utf-8")
        print(json.dumps(data, indent=2))
    except Exception as exc:
        target.write_text(json.dumps({
            "result": "FAIL", "error_type": type(exc).__name__,
            "scope": "synthetic A-B-A controller with real Chrome IndexedDB",
        }), encoding="utf-8")
        print(f"D7 controller-browser failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
