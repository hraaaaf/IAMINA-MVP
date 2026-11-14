#!/usr/bin/env python3
"""L01/D37 synthetic real-Chrome guest bootstrap egress evidence.

Actual Flutter Web entrypoint served only from 127.0.0.1. No backend, no
credentials, no patient data, no clinical certification. Captures BEFORE
viewport images for a later D37 guest-shell design and CDP network requests.
"""
from __future__ import annotations

import base64
import json
import shutil
import struct
import subprocess
import tempfile
import time
import urllib.parse
import urllib.request
from pathlib import Path

from websocket import create_connection

ORIGIN = "http://127.0.0.1:7387"
DEVTOOLS = "http://127.0.0.1:9239/json/list"
OUTPUT = Path("l01-guest-locale-browser-proof")


def chrome_binary() -> str:
    for name in ("google-chrome", "chromium", "chromium-browser"):
        executable = shutil.which(name)
        if executable:
            return executable
    raise RuntimeError("Chrome not installed")


def page_descriptor() -> dict:
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(DEVTOOLS, timeout=2) as response:
                pages = json.load(response)
            return next(page for page in pages if page.get("type") == "page")
        except (OSError, ValueError, StopIteration):
            time.sleep(0.25)
    raise RuntimeError("Chrome DevTools page missing")


def run_probe() -> dict:
    proof = {
        "scope": "L01 actual Flutter Web guest bootstrap, fresh synthetic Chrome profile",
        "source": "local HTTP build of exact pull-request SHA",
        "patient_data": "none",
        "backend": "disabled (API_BASE_URL points to 127.0.0.1:9)",
        "clinical_safety": "NOT_CERTIFIED",
        "D37_shell": "NOT_IMPLEMENTED_OR_CERTIFIED",
        "D18_legacy": "NOT_TESTED",
        "browser": "Chrome; Safari/WebKit NOT_RUN",
        "checks": [],
    }
    OUTPUT.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="iamina-l01-guest-chrome-") as tmp:
        with Path(tmp, "chrome.log").open("w", encoding="utf-8") as log:
            browser = subprocess.Popen([
                chrome_binary(), "--headless=new", "--no-sandbox",
                "--disable-dev-shm-usage", "--enable-unsafe-swiftshader",
                "--disable-background-networking", "--remote-allow-origins=*",
                "--remote-debugging-port=9239",
                f"--user-data-dir={tmp}/profile", "about:blank",
            ], stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            ws = None
            try:
                page = page_descriptor()
                ws = create_connection(page["webSocketDebuggerUrl"], timeout=30)
                ws.settimeout(30)
                requests = []
                seq = 0

                def cdp(method: str, params: dict | None = None) -> dict:
                    nonlocal seq
                    seq += 1
                    wanted_id = seq
                    ws.send(json.dumps({
                        "id": wanted_id, "method": method, "params": params or {},
                    }))
                    while True:
                        data = json.loads(ws.recv())
                        if data.get("method") == "Network.requestWillBeSent":
                            request = data.get("params", {}).get("request", {})
                            raw_url = request.get("url", "")
                            url = urllib.parse.urlsplit(raw_url)
                            # Do not log identifiers, query parameters or request bodies.
                            requests.append({
                                "origin": f"{url.scheme}://{url.netloc}",
                                "path": url.path,
                                "method": request.get("method", ""),
                            })
                        if data.get("id") == wanted_id:
                            if "error" in data:
                                raise RuntimeError(f"CDP {method}: {data['error']}")
                            return data.get("result", {})

                cdp("Page.enable")
                cdp("Runtime.enable")
                cdp("Network.enable")
                cdp("Page.navigate", {"url": ORIGIN + "/"})

                def mounted() -> bool:
                    result = cdp("Runtime.evaluate", {
                        "expression": """(() => ({
                          title: document.title,
                          mounted: !!document.querySelector(
                            'flutter-view, flt-glass-pane, flt-scene-host'
                          ),
                        }))()""",
                        "returnByValue": True,
                    })
                    obj = result.get("result", {}).get("value") or {}
                    return obj.get("mounted") and str(obj.get("title", "")).casefold() == "iamina"

                deadline = time.monotonic() + 100
                while time.monotonic() < deadline and not mounted():
                    time.sleep(0.5)
                if not mounted():
                    raise RuntimeError("Flutter Web did not mount in local Chrome")
                proof["checks"].append({"name": "real_web_boot", "result": "PASS"})

                # Flush delayed startup request events after Flutter has mounted.
                time.sleep(2)
                cdp("Runtime.evaluate", {
                    "expression": "document.readyState", "returnByValue": True,
                })

                for width, height in ((390, 844), (430, 932), (768, 1024), (1280, 900)):
                    cdp("Emulation.setDeviceMetricsOverride", {
                        "width": width, "height": height, "deviceScaleFactor": 1,
                        "mobile": width <= 430,
                    })
                    time.sleep(1)
                    image = cdp("Page.captureScreenshot", {
                        "format": "png", "fromSurface": True,
                        "captureBeyondViewport": False,
                    })
                    pixels = base64.b64decode(image["data"])
                    if pixels[:8] != bytes.fromhex("89504e470d0a1a0a"):
                        raise RuntimeError("Chrome did not return PNG")
                    observed = struct.unpack(">II", pixels[16:24])
                    if observed != (width, height):
                        raise RuntimeError(
                            f"Wrong screenshot dimensions: expected {(width, height)}, got {observed}"
                        )
                    (OUTPUT / f"before-{width}x{height}.png").write_bytes(pixels)
                    proof["checks"].append({
                        "name": f"before_viewport_{width}x{height}",
                        "result": "CAPTURED_NOT_VISUALLY_CERTIFIED",
                    })

                # CDP IndexedDB inventory is advisory only: D18/W01 proof needs
                # controlled old-profile fixtures and cannot be inferred here.
                try:
                    cdp("IndexedDB.enable")
                    names = cdp("IndexedDB.requestDatabaseNames", {
                        "securityOrigin": ORIGIN,
                    }).get("databaseNames", [])
                    proof["synthetic_fresh_browser_idb_names"] = names
                except (RuntimeError, KeyError):
                    proof["synthetic_fresh_browser_idb_names"] = "NOT_AVAILABLE"

                # Reload must not start a patient-profile locale fetch either.
                cdp("Page.reload", {"ignoreCache": True})
                deadline = time.monotonic() + 100
                while time.monotonic() < deadline and not mounted():
                    time.sleep(0.5)
                if not mounted():
                    raise RuntimeError("Flutter Web did not mount on reload")
                time.sleep(2)
                cdp("Runtime.evaluate", {
                    "expression": "document.readyState", "returnByValue": True,
                })

                business = [request for request in requests
                            if request["path"].startswith("/api/")]
                profile_locale = [request for request in requests
                                  if request["path"] == "/api/v1/profile/locale"]
                proof["api_requests_observed"] = business
                proof["profile_locale_request_count"] = len(profile_locale)
                proof["checks"].append({
                    "name": "guest_profile_locale_no_network_boot_and_reload",
                    "result": "PASS" if not profile_locale else "FAIL",
                    "observed_count": len(profile_locale),
                })
                if profile_locale:
                    raise RuntimeError("Real guest Web bootstrap emitted profile-locale request")
                proof["result"] = "PASS_BOUNDED_TO_GUEST_PROFILE_LOCALE"
                return proof
            finally:
                if ws is not None:
                    ws.close()
                browser.terminate()
                try:
                    browser.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    browser.kill()
                    browser.wait(timeout=8)


def main():
    proof = {"result": "FAIL", "scope": "L01 bounded synthetic Chrome"}
    try:
        proof = run_probe()
    except Exception as error:
        proof["failure"] = type(error).__name__
        raise
    finally:
        OUTPUT.mkdir(exist_ok=True)
        (OUTPUT / "proof.json").write_text(
            json.dumps(proof, indent=2, ensure_ascii=False), encoding="utf-8",
        )


if __name__ == "__main__":
    main()
