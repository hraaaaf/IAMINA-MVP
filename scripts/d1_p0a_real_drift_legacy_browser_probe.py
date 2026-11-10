#!/usr/bin/env python3
"""D1P0A browser-only A/B physical IndexedDB separation using synthetic fixtures.

Not a real login/session, encryption, multi-tab or production clinical proof.
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

from w01b_browser_api_pg_probe import _stop_chrome

ORIGIN = "http://127.0.0.1:7388"
DEVTOOLS = "http://127.0.0.1:9238/json/list"
PHASES = ("seed_legacy", "seed_a", "late_legacy_write", "seed_b",
          "verify_a", "verify_b", "verify_legacy", "verify_a")


def _chrome_binary() -> str:
    for name in ("google-chrome", "chromium", "chromium-browser"):
        found = shutil.which(name)
        if found:
            return found
    raise RuntimeError("Chrome unavailable")


def _get_page(deadline: float) -> dict:
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(DEVTOOLS, timeout=2) as f:
                pages = json.load(f)
            return next(p for p in pages if p.get("type") == "page")
        except (OSError, ValueError, StopIteration):
            time.sleep(0.25)
    raise RuntimeError("Chrome DevTools not ready")


def run_browser() -> dict:
    from websocket import create_connection

    proof = None
    with tempfile.TemporaryDirectory(
        prefix="iamina-d1-p0a-vault-chrome-", ignore_cleanup_errors=True
    ) as directory:
        with (Path(directory) / "chrome.log").open("w", encoding="utf-8") as logfile:
            chrome = subprocess.Popen(
                [
                    _chrome_binary(), "--headless=new", "--no-sandbox",
                    "--disable-dev-shm-usage", "--enable-unsafe-swiftshader",
                    "--remote-allow-origins=*", "--remote-debugging-port=9231",
                    f"--user-data-dir={directory}/profile", f"{ORIGIN}/?phase=seed_a",
                ],
                stdout=logfile, stderr=subprocess.STDOUT, start_new_session=True,
            )
            try:
                try:
                    page = _get_page(time.monotonic() + 30)
                except Exception as exc:
                    logfile.flush()
                    diagnostic = Path(directory, "chrome.log").read_text(
                        encoding="utf-8", errors="replace"
                    )[-1800:]
                    raise RuntimeError(
                        f"Chrome CDP startup failed: {exc}; chrome_tail={diagnostic!r}"
                    ) from exc
                websocket = create_connection(page["webSocketDebuggerUrl"], timeout=20)
                try:
                    command_id = 0

                    def command(method: str, params: dict | None = None) -> dict:
                        nonlocal command_id
                        command_id += 1
                        websocket.send(json.dumps({
                            "id": command_id, "method": method, "params": params or {},
                        }))
                        while True:
                            response = json.loads(websocket.recv())
                            if response.get("id") == command_id:
                                if "error" in response:
                                    raise RuntimeError(f"Chrome CDP {method} error")
                                return response.get("result", {})

                    command("Page.enable")
                    command("Runtime.enable")

                    def wait_phase(phase: str) -> None:
                        expected = f"IAMINA_D1P0A_{phase.upper()}_PASS"
                        deadline = time.monotonic() + 70
                        while time.monotonic() < deadline:
                            result = command("Runtime.evaluate", {
                                "expression": "document.title", "returnByValue": True,
                            })
                            title = result.get("result", {}).get("value", "")
                            if title == expected:
                                return
                            if title.startswith("IAMINA_D1P0A_FAIL:"):
                                raise RuntimeError("D1P0A synthetic physical vault probe error")
                            time.sleep(0.25)
                        raise RuntimeError("D1P0A scoped vault phase timeout")

                    for phase in PHASES:
                        command("Page.navigate", {"url": f"{ORIGIN}/?phase={phase}"})
                        wait_phase(phase)
                    # Navigate once more to A after B, then hard reload the A view.
                    command("Page.navigate", {"url": f"{ORIGIN}/?phase=verify_a"})
                    wait_phase("verify_a")
                    command("Page.reload", {"ignoreCache": True})
                    wait_phase("verify_a")
                    proof = {
                        "result": "PASS",
                        "type": "CI-only Chrome / real Drift SQLite WASM (backend not independently asserted)",
                        "sequence": "legacy seed -> A seed -> late legacy write -> B seed -> A/B/legacy reopen -> A hard reload",
                        "data": "synthetic only",
                        "limit": "Only v12 current-bundle persistence/isolation/integrity; NOT old bundle, v1 upgrade, stale-tab fence, recovery, encryption, offline crash, or patient cutover",
                    }
                finally:
                    websocket.close()
            finally:
                _stop_chrome(chrome)
    if proof is None:
        raise RuntimeError("No browser proof")
    return proof


if __name__ == "__main__":
    try:
        print(json.dumps(run_browser(), indent=2))
    except Exception as exc:
        print(f"D1P0A physical-vault probe failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
