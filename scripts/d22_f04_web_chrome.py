#!/usr/bin/env python3
"""D22 F04 real local Flutter Web + IndexedDB preservation FUE.

Synthetic patient vault only; actual EditLogScreen. Never hosted network.
"""
import hashlib
import http.server
import json
import pathlib
import re
import socketserver
import struct
import threading

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[1]
WEB = ROOT / "frontend" / "build" / "web"
OUT = ROOT / "d22-f04-web-proof"
VIEWS = ((390, 844), (1280, 900))


class Quiet(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB), **kwargs)

    def log_message(self, *_):
        pass


class Local(socketserver.TCPServer):
    allow_reuse_address = True


def choose(page, label):
    choices = (
        page.get_by_role("checkbox", name=label, exact=True),
        page.get_by_role("button", name=label, exact=True),
        page.get_by_text(label, exact=True),
    )
    for _ in range(20):
        for locator in choices:
            if locator.count() and locator.first.is_visible():
                locator.first.scroll_into_view_if_needed(timeout=20000)
                locator.first.click(timeout=20000)
                return
        page.wait_for_timeout(200)
    raise AssertionError(f"F04 synthetic browser control absent: {label}")


def main():
    assert (WEB / "main.dart.js").is_file(), "Missing Flutter Web F04 probe build"
    OUT.mkdir(exist_ok=True)
    report = {"decision": "D22 F04", "result": "NOT_RUN",
              "scope": "local actual Flutter EditLogScreen + Drift IndexedDB",
              "no_patient_data": True, "screens": [],
              "checks": [], "not_certified": ["G4 conversion policy",
              "normal product login and remote sync", "clinical deployment"]}
    errors = []
    blocked = []
    try:
        with Local(("127.0.0.1", 0), Quiet) as server:
            threading.Thread(target=server.serve_forever, daemon=True).start()
            origin = f"http://localhost:{server.server_address[1]}"
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                try:
                    for width, height in VIEWS:
                        context = browser.new_context(
                            viewport={"width": width, "height": height},
                            locale="fr-FR", service_workers="block",
                            accept_downloads=False,
                        )
                        try:
                            page = context.new_page()
                            page.on("pageerror", lambda e: errors.append(str(e)[:200]))

                            def local_only(route):
                                u = route.request.url
                                if u.startswith(origin + "/") or u.startswith(("blob:", "data:")):
                                    route.continue_()
                                else:
                                    blocked.append(u.split("?", 1)[0])
                                    route.abort()

                            page.route("**/*", local_only)
                            response = page.goto(origin, wait_until="domcontentloaded",
                                                 timeout=60000)
                            assert response and response.status == 200
                            page.wait_for_selector("flutter-view, flt-glass-pane",
                                                   timeout=60000)
                            placeholder = page.locator("flt-semantics-placeholder")
                            if placeholder.count():
                                placeholder.first.evaluate("(el) => el.click()")
                            page.get_by_text("GLYCÉMIE", exact=True).wait_for(
                                state="visible", timeout=30000)
                            glucose_fields = page.get_by_role("textbox")
                            assert glucose_fields.count() >= 1
                            first = glucose_fields.first.aria_snapshot()
                            assert "5.7" in first or glucose_fields.first.get_attribute(
                                "aria-valuenow") == "5.7", (
                                f"F04 synthetic raw 103.25 must show rounded mmol 5.7, "
                                f"got {first[:220]!r}"
                            )
                            before = OUT / f"before-edit-{width}x{height}.png"
                            page.screenshot(path=str(before), full_page=False,
                                            animations="disabled")
                            choose(page, "Stress inhabituel")
                            save = page.get_by_role("button", name="Sauvegarder", exact=True)
                            save.last.scroll_into_view_if_needed(timeout=15000)
                            save.last.click(timeout=20000)
                            page.get_by_text(re.compile(r"^F04_WEB_PASS RAW=103.25 STRESS=TRUE$")).wait_for(
                                state="visible", timeout=30000)
                            assert "/journal" in page.url
                            after = OUT / f"after-edit-{width}x{height}.png"
                            page.screenshot(path=str(after), full_page=False,
                                            animations="disabled")
                            for image in (before, after):
                                png = image.read_bytes()
                                assert png[:8] == bytes.fromhex("89504e470d0a1a0a")
                                assert struct.unpack(">II", png[16:24]) == (width, height)
                                report["screens"].append({
                                    "viewport": f"{width}x{height}",
                                    "file": image.name,
                                    "sha256": hashlib.sha256(png).hexdigest(),
                                })
                            report["checks"].append({
                                "viewport": f"{width}x{height}",
                                "input_display": "5.7 mmol/L",
                                "raw_before": 103.25, "raw_after": 103.25,
                                "stress_after": True,
                                "result": "PASS",
                            })
                        finally:
                            context.close()
                finally:
                    browser.close()
        assert not blocked, f"Unauthorized browser network: {blocked[:3]}"
        assert not errors, f"Flutter Web page errors: {errors[:3]}"
        report["result"] = "PASS_BOUNDED_SYNTHETIC_WEB"
    finally:
        (OUT / "proof.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
