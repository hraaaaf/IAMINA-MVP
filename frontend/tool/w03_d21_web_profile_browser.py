#!/usr/bin/env python3
"""D21 synthetic Chrome proof: two locales, three viewports, keyboard trace."""
import argparse
import base64
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from contextlib import closing
from urllib.parse import urlencode

from websocket import create_connection

PORT = 7391
DEBUG_PORT = 9291
VIEWS = ((390, 844, True), (768, 1024, False), (1280, 900, False))
LOCALES = ("fr", "ar")


def wait_http(url, timeout=45):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status == 200:
                    return
        except Exception:
            time.sleep(0.3)
    raise RuntimeError("HTTP or DevTools unavailable: " + url)


class CDP:
    def __init__(self, url):
        with urllib.request.urlopen(url, timeout=5) as response:
            pages = json.load(response)
        page = next(p for p in pages if p.get("type") == "page")
        self.ws = create_connection(page["webSocketDebuggerUrl"], timeout=30)
        self.counter = 0

    def call(self, method, params=None):
        self.counter += 1
        self.ws.send(json.dumps({"id": self.counter, "method": method, "params": params or {}}))
        while True:
            response = json.loads(self.ws.recv())
            if response.get("id") == self.counter:
                if "error" in response:
                    raise RuntimeError(f"{method}: {response['error']}")
                return response.get("result", {})

    def evaluate(self, expression):
        result = self.call("Runtime.evaluate", {
            "expression": expression,
            "returnByValue": True,
            "awaitPromise": False,
        })
        return result.get("result", {}).get("value")

    def close(self):
        self.ws.close()


def ax_snapshot(cdp):
    nodes = cdp.call("Accessibility.getFullAXTree").get("nodes", [])
    names = []
    focused = []
    for node in nodes:
        name = node.get("name", {}).get("value", "")
        if isinstance(name, str) and name.strip():
            names.append(name.strip())
        if any(prop.get("name") == "focused"
               and prop.get("value", {}).get("value") is True
               for prop in node.get("properties", [])):
            focused.append(name or node.get("role", {}).get("value", ""))
    return names, focused


def capture(cdp, target):
    result = cdp.call("Page.captureScreenshot", {
        "format": "png", "captureBeyondViewport": False, "fromSurface": True,
    })
    data = base64.b64decode(result["data"])
    if len(data) < 10000:
        raise AssertionError(f"Suspiciously small screenshot: {target} ({len(data)} B)")
    target.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def keyboard_focus_trace(cdp):
    trace = []
    for index in range(16):
        shift = index >= 12
        modifiers = 8 if shift else 0
        for kind in ("rawKeyDown", "keyUp"):
            cdp.call("Input.dispatchKeyEvent", {
                "type": kind, "key": "Tab", "code": "Tab",
                "windowsVirtualKeyCode": 9, "nativeVirtualKeyCode": 9,
                "modifiers": modifiers,
            })
        names, focused = ax_snapshot(cdp)
        dom_focus = cdp.evaluate(
            "(function(){let n=document.activeElement;"
            "while(n && n.shadowRoot && n.shadowRoot.activeElement)"
            " n=n.shadowRoot.activeElement;"
            "return n ? (n.getAttribute('aria-label') || n.outerHTML.slice(0,180)) : null;})()"
        )
        trace.append({"key": "Shift+Tab" if shift else "Tab",
                      "ax_focus": focused, "dom_focus": dom_focus,
                      "ax_node_count": len(names)})
    return trace


def run_one(stage, locale, viewport, output):
    width, height, mobile = viewport
    chrome = next((p for name in ("google-chrome", "chromium", "chromium-browser")
                   if (p := shutil.which(name))), None)
    if not chrome:
        raise RuntimeError("No Chrome executable in runner")
    profile = tempfile.mkdtemp(prefix="iamina-d21-chrome-")
    url = f"http://127.0.0.1:{PORT}/?" + urlencode(
        {"surface": "profile", "locale": locale})
    args = [chrome, "--headless=new", "--no-sandbox", "--disable-dev-shm-usage",
            "--enable-unsafe-swiftshader", "--hide-scrollbars",
            "--force-renderer-accessibility", "--remote-allow-origins=*",
            f"--remote-debugging-port={DEBUG_PORT}",
            f"--user-data-dir={profile}", f"--window-size={width},{height}", url]
    chrome_proc = subprocess.Popen(args, stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL)
    cdp = None
    try:
        wait_http(f"http://127.0.0.1:{DEBUG_PORT}/json/list")
        cdp = CDP(f"http://127.0.0.1:{DEBUG_PORT}/json/list")
        cdp.call("Page.enable")
        cdp.call("Accessibility.enable")
        cdp.call("Emulation.setDeviceMetricsOverride", {
            "width": width, "height": height, "mobile": mobile,
            "deviceScaleFactor": 1,
        })
        cdp.call("Page.reload", {"ignoreCache": True})
        # Same stable audit fixture for both sides, allow Flutter WASM/Drift init.
        time.sleep(12)
        title = f"profile-{locale}-{width}x{height}"
        names, focused = ax_snapshot(cdp)
        png = output / f"{stage}-{title}.png"
        digest = capture(cdp, png)
        scroll_width = cdp.evaluate("document.documentElement.scrollWidth")
        trace = keyboard_focus_trace(cdp) if stage == "after" else []
        text = " ".join(names).lower()
        ramadan = ("رمضان" in text or "ramadan" in text)
        ar_copy = "البيانات والأجهزة" in text
        fr_copy = "données & appareils" in text
        focus_targets = sorted(set(
            str(x) for row in trace
            for x in row["ax_focus"] if x
        ))
        report = {"stage": stage, "locale": locale, "viewport": [width, height],
                  "png": png.name, "sha256": digest, "bytes": png.stat().st_size,
                  "ax_node_count": len(names), "ramadan_in_ax": ramadan,
                  "expected_locale_copy_in_ax": ar_copy if locale == "ar" else fr_copy,
                  "document_scroll_width": scroll_width,
                  "focused_before": focused, "keyboard_trace": trace,
                  "distinct_ax_focus_targets": focus_targets,
                  "ax_names_preview": names[:90]}
        (output / f"{stage}-{title}.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n")
        problems = []
        if stage == "before" and not ramadan:
            problems.append("Historical Ramadan card not found in AX tree")
        if stage == "after" and ramadan:
            problems.append("Ramadan remains in Web accessible UI")
        if len(names) < 10:
            problems.append("Accessibility tree unexpectedly empty")
        if not report["expected_locale_copy_in_ax"]:
            problems.append("Expected locale copy absent in AX tree")
        if scroll_width is not None and scroll_width > width + 8:
            problems.append(f"Horizontal browser overflow {scroll_width}>{width}")
        if stage == "after" and not focus_targets:
            problems.append("Tab/Shift+Tab never reached an AX focus target")
        if problems:
            raise AssertionError(f"{title} {stage}: " + "; ".join(problems))
        print(json.dumps({key: report[key] for key in
              ("stage", "locale", "viewport", "ramadan_in_ax",
               "distinct_ax_focus_targets", "sha256")}, ensure_ascii=False),
              flush=True)
    finally:
        if cdp:
            cdp.close()
        chrome_proc.terminate()
        try:
            chrome_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            chrome_proc.kill()
            chrome_proc.wait()
        shutil.rmtree(profile, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("before", "after"), required=True)
    parser.add_argument("--build", type=pathlib.Path, required=True)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    server = subprocess.Popen([sys.executable, "-m", "http.server", str(PORT),
                               "--bind", "127.0.0.1", "--directory", str(args.build)],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        wait_http(f"http://127.0.0.1:{PORT}/")
        for locale in LOCALES:
            for viewport in VIEWS:
                run_one(args.stage, locale, viewport, args.output)
    finally:
        server.terminate()
        server.wait(timeout=5)


if __name__ == "__main__":
    main()
