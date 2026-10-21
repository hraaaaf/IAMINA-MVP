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
    # A populated AX tree does not prove working keyboard navigation.
    # Explicit shift key events and a settling delay are required to
    # distinguish meaningful forward traversal from a trapped focus.
    cdp.call("Page.bringToFront")
    cdp.call("Emulation.setFocusEmulationEnabled", {"enabled": True})
    # Record keys that actually arrive in the DOM, not only CDP dispatches.
    # This differentiates an event-delivery failure from Flutter focus traversal.
    cdp.evaluate(
        "window.__d21Keys=[];"
        "document.addEventListener('keydown',function(e){"
        "window.__d21Keys.push({key:e.key,shift:e.shiftKey,"
        "target:e.target && e.target.getAttribute('aria-label'),"
        "trusted:e.isTrusted});},true);"
    )
    trace = []
    for index in range(28):
        # Twelve forward probes, then sixteen reverse probes. The browser
        # focus ring can include non-AX stops between Flutter semantics nodes.
        shift = index >= 12
        modifiers = 8 if shift else 0
        if shift:
            cdp.call("Input.dispatchKeyEvent", {
                "type": "rawKeyDown", "key": "Shift", "code": "ShiftLeft",
                "windowsVirtualKeyCode": 16, "nativeVirtualKeyCode": 16,
                "modifiers": 8,
            })
        for kind in ("rawKeyDown", "keyUp"):
            cdp.call("Input.dispatchKeyEvent", {
                "type": kind, "key": "Tab", "code": "Tab",
                "windowsVirtualKeyCode": 9, "nativeVirtualKeyCode": 9,
                "modifiers": modifiers,
            })
        if shift:
            cdp.call("Input.dispatchKeyEvent", {
                "type": "keyUp", "key": "Shift", "code": "ShiftLeft",
                "windowsVirtualKeyCode": 16, "nativeVirtualKeyCode": 16,
                "modifiers": 0,
            })
        time.sleep(0.18)
        names, focused = ax_snapshot(cdp)
        dom_focus = cdp.evaluate(
            "(function(){let n=document.activeElement;"
            "while(n && n.shadowRoot && n.shadowRoot.activeElement)"
            " n=n.shadowRoot.activeElement;"
            "return n ? (n.getAttribute('aria-label') || n.outerHTML.slice(0,180)) : null;})()"
        )
        received = cdp.evaluate("window.__d21Keys.slice(-4)")
        trace.append({"key": "Shift+Tab" if shift else "Tab",
                      "ax_focus": focused, "dom_focus": dom_focus,
                      "ax_node_count": len(names),
                      "received_dom_keys": received})
    return trace


def keyboard_navigation_verdict(trace):
    # Chromium may retain the root IAMINA label in the focused AX list.
    def target(entry):
        selected = [x for x in entry["ax_focus"] if x and x != "IAMINA"]
        return selected[-1] if selected else None

    forward = [target(x) for x in trace[:12]]
    backward = [target(x) for x in trace[12:]]
    forward_names = {name for name in forward if name is not None}
    reverse_step = next((
        index + 1 for index, name in enumerate(backward)
        if name is not None
        and name != forward[-1]
        and name in forward_names
    ), None)
    reversed_to_earlier = reverse_step is not None
    return {
        "forward_unique_targets": len(forward_names),
        "reverse_to_earlier_target": reversed_to_earlier,
        "reverse_first_return_step": reverse_step,
        "reverse_stagnation_first_four": all(
            name == forward[-1] for name in backward[:4]
        ),
        "forward_target_sequence": forward,
        "reverse_target_sequence": backward,
    }


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
        trace = keyboard_focus_trace(cdp)
        text = " ".join(names).lower()
        ramadan = ("رمضان" in text or "ramadan" in text)
        ar_copy = "البيانات والأجهزة" in text
        fr_copy = "données & appareils" in text
        focus_targets = sorted(set(
            str(x) for row in trace
            for x in row["ax_focus"] if x
        ))
        keyboard_verdict = keyboard_navigation_verdict(trace)
        report = {"stage": stage, "locale": locale, "viewport": [width, height],
                  "png": png.name, "sha256": digest, "bytes": png.stat().st_size,
                  "ax_node_count": len(names), "ramadan_in_ax": ramadan,
                  "expected_locale_copy_in_ax": ar_copy if locale == "ar" else fr_copy,
                  "document_scroll_width": scroll_width,
                  "focused_before": focused, "keyboard_trace": trace,
                  "distinct_ax_focus_targets": focus_targets,
                  "keyboard_navigation": keyboard_verdict,
                  "ax_names_preview": names[:90]}
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
        if keyboard_verdict["forward_unique_targets"] < 3:
            problems.append("Tab failed to visit at least three distinct Profile targets")
        if not keyboard_verdict["reverse_to_earlier_target"]:
            problems.append("Shift+Tab did not return to a previously focused Profile target")
        # Chromium consumes Tab at its focus-navigation layer; neither the
        # historical baseline nor candidate emits Tab DOM keydowns. Shift
        # keydowns do arrive, so require those rather than treating the
        # absent Tab event as an application failure.
        received_shift = any(
            event.get("key") == "Shift" and event.get("shift") is True
            for item in trace[12:]
            for event in item.get("received_dom_keys", [])
        )
        if not received_shift:
            problems.append("Shift keydown was not observed by document")
        report["problems"] = problems
        (output / f"{stage}-{title}.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n")
        print(json.dumps({
            "stage": stage, "locale": locale, "viewport": [width, height],
            "ramadan_in_ax": ramadan, "reverse_pass": keyboard_verdict["reverse_to_earlier_target"],
            "received_shift_keydown": received_shift, "problems": problems,
            "sha256": digest,
        }, ensure_ascii=False), flush=True)
        return report
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
        print("D21 diagnostic: all 6 locale/viewports captured; the final workflow step enforces assertions")
    finally:
        server.terminate()
        server.wait(timeout=5)


if __name__ == "__main__":
    main()
