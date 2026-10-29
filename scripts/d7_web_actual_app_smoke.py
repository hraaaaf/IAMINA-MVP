#!/usr/bin/env python3
"""D7 free actual IAMINA Web app Chrome smoke.

Does NOT prove hosted SSO, authenticated A/B, clinical consent, encrypted vault,
patient treatment save in a deployed session, or full offline app workflows.
This smoke deliberately uses an isolated browser profile and synthetic/no data.
"""
import base64
import json
import struct
import shutil
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path
from websocket import create_connection

ORIGIN = "http://127.0.0.1:7378"
DEVTOOLS = "http://127.0.0.1:9238/json/list"


def chrome_exe():
    for cmd in ("google-chrome", "chromium", "chromium-browser"):
        found = shutil.which(cmd)
        if found:
            return found
    raise RuntimeError("Chrome not installed")


def tab():
    for _ in range(100):
        try:
            with urllib.request.urlopen(DEVTOOLS, timeout=2) as response:
                pages = json.load(response)
            return next(p for p in pages if p.get("type") == "page")
        except (ValueError, OSError, StopIteration):
            time.sleep(0.25)
    raise RuntimeError("Chrome DevTools not available")


def main():
    profile = tempfile.mkdtemp(prefix="iamina-d7-free-fue-")
    proof = {
        "scope": "actual local Flutter Web app smoke, not hosted FUE",
        "origin": ORIGIN,
        "backend_access": "none (offline demo compile flag)",
        "patient_data": "none",
        "hosted_sso": "NOT_RUN",
        "hosted_patient_A_B_A": "NOT_RUN",
        "clinical_privacy_review": "NOT_RUN",
        "checks": [],
        "responsive": "screenshots only; visual review pending",
        "locale_coverage": "default app locale only; FR/AR covered by separate widget checks",
    }
    try:
        with Path(profile, "chrome.log").open("w") as log:
            proc = subprocess.Popen([
                chrome_exe(), "--headless=new", "--no-sandbox",
                "--disable-dev-shm-usage", "--enable-unsafe-swiftshader",
                "--remote-allow-origins=*", "--remote-debugging-port=9238",
                f"--user-data-dir={profile}/user", ORIGIN,
            ], stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            ws = None
            try:
                page = tab()
                ws = create_connection(page["webSocketDebuggerUrl"], timeout=30)
                seq = 0

                def cdpmethod(name, params=None):
                    nonlocal seq
                    seq += 1
                    ws.send(json.dumps({"id": seq, "method": name, "params": params or {}}))
                    while True:
                        item = json.loads(ws.recv())
                        if item.get("id") == seq:
                            if "error" in item:
                                raise RuntimeError(f"Chrome CDP error at {name}: {item['error']}")
                            return item.get("result", {})

                cdpmethod("Page.enable")
                cdpmethod("Runtime.enable")
                cdpmethod("Network.enable")

                expression = """(() => ({
                  title: document.title,
                  flutterHost: !!document.querySelector('flutter-view, flt-glass-pane, flt-scene-host'),
                  bootstrap: !!document.querySelector('script[src*="flutter_bootstrap"]'),
                  hasCanvas: !!document.querySelector('canvas, flt-canvas-container'),
                  ready: document.readyState,
                  url: location.origin + location.pathname
                }))()"""

                def check(phase):
                    end = time.monotonic() + 90
                    last = {}
                    while time.monotonic() < end:
                        result = cdpmethod("Runtime.evaluate", {
                            "expression": expression, "returnByValue": True,
                        })
                        last = result.get("result", {}).get("value") or {}
                        if last.get("title", "").casefold() == "iamina" and last.get("flutterHost"):
                            proof["checks"].append({"phase": phase, "result": "PASS",
                                                    "observed": last})
                            return
                        time.sleep(1)
                    proof["checks"].append({"phase": phase, "result": "FAIL", "observed": last})
                    raise RuntimeError(f"Actual Flutter app did not mount on {phase}: {last}")

                check("boot")
                cdpmethod("Page.reload", {"ignoreCache": True})
                check("hard_reload")
                # Actual production entrypoint (not a synthetic probe): capture
                # three physical Chrome viewport screenshots for later human
                # BEFORE/AFTER review. These are not automatic pixel-match PASSes.
                # No credentials or patient data are ever entered.
                Path("d7-web-viewport-captures").mkdir(exist_ok=True)
                for width, height in ((390, 844), (768, 1024), (1280, 900)):
                    cdpmethod("Emulation.setDeviceMetricsOverride", {
                        "width": width, "height": height, "deviceScaleFactor": 1,
                        "mobile": width == 390,
                    })
                    # Give Flutter a real render frame after resize; do not
                    # mistake a mounted host element for responsive QA.
                    time.sleep(3)
                    result = cdpmethod("Runtime.evaluate", {
                        "expression": "({innerWidth: innerWidth, innerHeight: innerHeight, host: !!document.querySelector('flutter-view, flt-glass-pane, flt-scene-host')})",
                        "returnByValue": True,
                    })
                    observed = result.get("result", {}).get("value") or {}
                    if (observed.get("innerWidth") != width or
                            observed.get("innerHeight") != height or
                            not observed.get("host")):
                        raise RuntimeError(f"Real app viewport failed: {width}x{height} {observed}")
                    captured = cdpmethod("Page.captureScreenshot", {
                        "format": "png", "captureBeyondViewport": False,
                        "fromSurface": True,
                    })
                    data = base64.b64decode(captured["data"])
                    if data[:8] != b"\\x89PNG\\r\\n\\x1a\\n":
                        raise RuntimeError(f"Missing PNG screenshot {width}x{height}")
                    png_width, png_height = struct.unpack(">II", data[16:24])
                    if (png_width, png_height) != (width, height):
                        raise RuntimeError(
                            f"Screenshot geometry mismatch {width}x{height}: "
                            f"{png_width}x{png_height}"
                        )
                    Path(f"d7-web-viewport-captures/app-{width}x{height}.png").write_bytes(data)
                    proof["checks"].append({
                        "phase": f"viewport_{width}x{height}",
                        "result": "CAPTURED_NOT_VISUALLY_CERTIFIED",
                        "pixel_dimensions": [png_width, png_height],
                        "actual_flutter_host": True,
                    })

                # Network offline *after* app boot only: demonstrates shell already
                # in memory; not full PWA offline restoration from a cold start.
                cdpmethod("Network.emulateNetworkConditions", {
                    "offline": True, "latency": 0,
                    "downloadThroughput": 0, "uploadThroughput": 0,
                })
                result = cdpmethod("Runtime.evaluate", {
                    "expression": "({offline: !navigator.onLine, title: document.title, flutterHost: !!document.querySelector('flutter-view, flt-glass-pane, flt-scene-host')})",
                    "returnByValue": True,
                })
                val = result.get("result", {}).get("value") or {}
                if not (val.get("offline") and val.get("title", "").casefold() == "iamina" and val.get("flutterHost")):
                    raise RuntimeError(f"Offline in-memory app shell unavailable: {val}")
                proof["checks"].append({"phase": "offline_after_boot",
                                        "result": "PASS", "observed": val})
                proof["overall"] = "PASS"
            finally:
                if ws is not None:
                    ws.close()
                proc.terminate()
                try:
                    proc.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=8)
    finally:
        Path("d7-web-app-smoke-proof.json").write_text(
            json.dumps(proof, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        shutil.rmtree(profile, ignore_errors=True)

if __name__ == "__main__":
    main()
