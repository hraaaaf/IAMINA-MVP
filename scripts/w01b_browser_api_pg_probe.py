#!/usr/bin/env python3
"""Real Chromium check for the CI-only Flutter Web -> Django -> PG16 flow.

All destinations must be loopback; no Vercel, Neon or patient records accessed.
"""
from __future__ import annotations

import json
import os
import signal
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

APP_URL = "http://127.0.0.1:7364/"
DEVTOOLS_URL = "http://127.0.0.1:9229/json/list"
EXPECTED_TITLE = "IAMINA_W01B_WEB_API_POSTGRES_PASS"
FAILED_PREFIX = "IAMINA_W01B_WEB_API_POSTGRES_FAIL:"


def _get_pages(deadline: float) -> list:
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(DEVTOOLS_URL, timeout=2) as response:
                return json.load(response)
        except (OSError, ValueError):
            time.sleep(0.25)
    raise RuntimeError("Chrome DevTools never became available")


def _chrome_binary() -> str:
    for name in ("google-chrome", "chromium", "chromium-browser"):
        chrome = shutil.which(name)
        if chrome:
            return chrome
    raise RuntimeError("No Chromium installation found on CI runner")


def _confirm_title(page: dict, deadline: float) -> str:
    from websocket import create_connection

    # Same bounded Chrome CDP mechanism as existing P5-4A PWA proof.
    ws = create_connection(page["webSocketDebuggerUrl"], timeout=20)
    try:
        next_id = 0

        def call(method: str, params: dict | None = None) -> dict:
            nonlocal next_id
            next_id += 1
            ws.send(json.dumps({"id": next_id, "method": method, "params": params or {}}))
            while True:
                response = json.loads(ws.recv())
                if response.get("id") == next_id:
                    if "error" in response:
                        raise RuntimeError(f"{method} failed: {response['error']}")
                    return response.get("result", {})

        call("Runtime.enable")
        while time.monotonic() < deadline:
            result = call("Runtime.evaluate", {
                "expression": "document.title",
                "returnByValue": True,
            })
            title = result.get("result", {}).get("value", "")
            if title == EXPECTED_TITLE:
                return title
            if title.startswith(FAILED_PREFIX):
                raise RuntimeError(f"Flutter cross-origin API probe failed: {title}")
            time.sleep(0.25)
        raise RuntimeError("Timed out waiting for Flutter Web -> API -> PG proof")
    finally:
        ws.close()


def _stop_chrome(process: subprocess.Popen) -> None:
    """Tear down a dedicated Chrome process group; already-exited is success.

    Chromium may exit after DevTools reports success while child processes still
    write the ephemeral browser profile. This cleanup must never turn a genuine
    successful browser assertion into an infrastructure failure.
    """
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait(timeout=5)


def main() -> int:
    # Each GitHub Actions runner is ephemeral and uses only synthetic browser data.
    # Suppress Linux Chrome profile-deletion races, never assertion failures.
    with tempfile.TemporaryDirectory(
        prefix="iamina-w01b-chrome-", ignore_cleanup_errors=True
    ) as directory:
        logpath = Path(directory) / "chrome.log"
        chrome = _chrome_binary()
        with logpath.open("w", encoding="utf-8") as logfile:
            process = subprocess.Popen(
                [
                    chrome,
                    "--headless=new",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--enable-unsafe-swiftshader",
                    "--remote-allow-origins=*",
                    "--remote-debugging-port=9229",
                    f"--user-data-dir={directory}/profile",
                    APP_URL,
                ],
                stdout=logfile,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            try:
                pages = _get_pages(time.monotonic() + 30)
                page = next(page for page in pages if page.get("type") == "page")
                title = _confirm_title(page, time.monotonic() + 90)
                print(json.dumps({
                    "result": "PASS",
                    "evidence_type": "CI-only synthetic real browser",
                    "browser_origin": "http://127.0.0.1:7364",
                    "api_origin": "http://127.0.0.1:8000",
                    "postgresql": "16, local GitHub Actions service",
                    "title": title,
                    "limits": "No Vercel/Neon cloud, no patient data, no auth or production CORS certification",
                }, indent=2))
                return 0
            finally:
                _stop_chrome(process)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        # Prevent leaking page content, any body or credentials in logs.
        print(f"W01B browser proof failed: {type(exc).__name__}", file=sys.stderr)
        raise SystemExit(1) from exc
