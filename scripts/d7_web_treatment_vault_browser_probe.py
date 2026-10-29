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


def main() -> None:
    from websocket import create_connection

    with tempfile.TemporaryDirectory(prefix="iamina-d7-indexeddb-") as tmp:
        with Path(tmp, "chrome.log").open("w", encoding="utf-8") as logfile:
            proc = subprocess.Popen(
                [
                    _chrome(), "--headless=new", "--no-sandbox",
                    "--disable-dev-shm-usage", "--enable-unsafe-swiftshader",
                    "--remote-allow-origins=*", "--remote-debugging-port=9237",
                    f"--user-data-dir={tmp}/user",
                    f"{ORIGIN}/?phase=seed_a",
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

                for phase in PHASES:
                    command("Page.navigate", {"url": f"{ORIGIN}/?phase={phase}"})
                    observe(phase)

                # Reload A after B changes. The same Chrome profile must retain
                # physical databases and the owner-scoped, pending declaration.
                command("Page.reload", {"ignoreCache": True})
                observe("verify_a_edited")

                output = {
                    "result": "PASS",
                    "type": "real Chrome, sqlite3.wasm, IndexedDB",
                    "fixture": "synthetic-only",
                    "sequence": PHASES,
                    "hard_reload": "verify_a_edited",
                    "claim_limit": (
                        "Physical patient vault persistence/isolation and "
                        "declaration state only; NOT full UI/auth/offline/clinical FUE"
                    ),
                }
                Path("d7-web-indexeddb-proof.json").write_text(
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
