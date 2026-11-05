#!/usr/bin/env python3
"""Capture 21 distinct synthetic Flutter Web route-audit screenshots.

Uses pinned Playwright Chromium instead of a host Chrome DevTools TCP port.
No patient records or production services are required. Every frame is checked
for dimensions, minimum content size, and per-viewport surface uniqueness.
"""
import hashlib
import http.server
import json
import pathlib
import struct
import threading
from urllib.parse import quote

from playwright.sync_api import sync_playwright


ROOT = pathlib.Path(__file__).resolve().parents[1]
WEB = ROOT / "frontend" / "build" / "web"
OUT = ROOT / "ui-global-missing-routes-cert"
SURFACES = (
    "login", "reset-password", "consent", "onboarding",
    "companion-chat", "cgm", "edit-log",
)
VIEWPORTS = ((390, 844, True), (768, 1024, False), (1280, 900, False))


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB), **kwargs)

    def log_message(self, *_args):
        pass


def main():
    assert (WEB / "main.dart.js").is_file(), "Flutter audit release build missing"
    assert (WEB / "index.html").is_file(), "Flutter audit index missing"
    OUT.mkdir(parents=True, exist_ok=True)
    captures = []
    with http.server.ThreadingHTTPServer(("127.0.0.1", 0), QuietHandler) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        origin = f"http://127.0.0.1:{server.server_address[1]}"
        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                try:
                    for width, height, mobile in VIEWPORTS:
                        context = browser.new_context(
                            viewport={"width": width, "height": height},
                            device_scale_factor=1,
                            is_mobile=mobile,
                            service_workers="block",
                        )
                        hashes = set()
                        try:
                            for surface in SURFACES:
                                page = context.new_page()
                                errors = []
                                page.on("pageerror", lambda exc: errors.append(str(exc)))
                                try:
                                    response = page.goto(
                                        f"{origin}/?surface={quote(surface)}",
                                        wait_until="domcontentloaded",
                                        timeout=60000,
                                    )
                                    assert response and response.status == 200, (
                                        f"{surface}: audit app did not return HTTP 200"
                                    )
                                    page.wait_for_selector(
                                        "flutter-view, flt-glass-pane", timeout=60000
                                    )
                                    # Wait for Flutter's first rasterized frame, not just
                                    # the DOM host or a DevTools endpoint.
                                    page.wait_for_timeout(2000)
                                    assert not errors, (
                                        f"{surface}: browser error: {errors[:2]}"
                                    )
                                    name = f"{surface}-{width}x{height}.png"
                                    data = page.screenshot(
                                        full_page=False,
                                        animations="disabled",
                                        timeout=30000,
                                    )
                                    assert len(data) >= 10000, (
                                        f"{name}: suspiciously small PNG ({len(data)} B)"
                                    )
                                    assert data[:8] == bytes.fromhex(
                                        "89504e470d0a1a0a"
                                    ), f"{name}: invalid PNG signature"
                                    observed = struct.unpack(">II", data[16:24])
                                    assert observed == (width, height), (
                                        f"{name}: wrong PNG dimensions {observed}"
                                    )
                                    digest = hashlib.sha256(data).hexdigest()
                                    assert digest not in hashes, (
                                        f"{name}: duplicate/blank surface screenshot"
                                    )
                                    hashes.add(digest)
                                    (OUT / name).write_bytes(data)
                                    captures.append({
                                        "surface": surface,
                                        "viewport": f"{width}x{height}",
                                        "file": name,
                                        "sha256": digest,
                                        "bytes": len(data),
                                    })
                                    print("UI route captured:", name, flush=True)
                                finally:
                                    page.close()
                            assert len(hashes) == len(SURFACES)
                        finally:
                            context.close()
                finally:
                    browser.close()
        finally:
            server.shutdown()
            thread.join(timeout=5)

    assert len(captures) == len(SURFACES) * len(VIEWPORTS)
    (OUT / "proof.json").write_text(json.dumps({
        "result": "PASS",
        "fixture": "synthetic isolated Flutter Web route audit",
        "browser": "Playwright Chromium 1.58.0",
        "captures": captures,
    }, indent=2) + "\n", encoding="utf-8")
    print("UI missing-routes PASS: 21 actual Chromium PNGs", flush=True)


if __name__ == "__main__":
    main()
