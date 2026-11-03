#!/usr/bin/env python3
"""D22-B independent BEFORE evidence from D22-A exact SHA 3e55ff0.

Run only against a separately compiled, local synthetic Flutter release Web app.
Produces the pre-fail-closed profile's visible target editor at the same
viewports as D22-B AFTER. It never connects to hosted services or real patients.
"""
import hashlib
import http.server
import json
import os
from pathlib import Path
import re
import socketserver
import threading

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "d22-before" / "frontend" / "build" / "web"
OUT = ROOT / "d22-web-before-chrome"
VIEWPORTS = ((390, 844), (768, 1024), (1280, 900))
D22_A_SHA = "3e55ff069a4bc9601ea548390f78af48e8e003dd"


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB), **kwargs)

    def log_message(self, *_args):
        pass


class LocalServer(socketserver.TCPServer):
    allow_reuse_address = True


def main():
    assert (WEB / "main.dart.js").is_file(), "D22-A BEFORE Web build missing"
    OUT.mkdir(exist_ok=True)
    evidence = {
        "decision": "D22-B",
        "before_sha": D22_A_SHA,
        "scope": "D22-A independent BEFORE, local synthetic Chromium",
        "status": "NOT_RUN",
        "capture": [],
        "limitations": [
            "same synthetic user flow, not the same patient DB file",
            "no real patient or remote backend",
            "BEFORE screenshots are not proof that legacy numeric targets are safe",
        ],
    }
    blocked, pageerrors = [], []
    try:
        with LocalServer(("127.0.0.1", 0), QuietHandler) as server:
            threading.Thread(target=server.serve_forever, daemon=True).start()
            origin = f"http://localhost:{server.server_address[1]}"
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                try:
                    context = browser.new_context(
                        locale="en-US",
                        viewport={"width": 1180, "height": 860},
                        service_workers="block",
                        accept_downloads=False,
                    )
                    try:
                        page = context.new_page()
                        page.on("pageerror", lambda e: pageerrors.append(str(e)[:180]))

                        def local_only(route):
                            url = route.request.url
                            if url.startswith(origin + "/") or url.startswith(("data:", "blob:")):
                                route.continue_()
                            else:
                                blocked.append(url.split("?", 1)[0])
                                route.abort()

                        page.route("**/*", local_only)
                        cdp = context.new_cdp_session(page)
                        cdp.send("WebAuthn.enable", {"enableUI": False})
                        cdp.send("WebAuthn.addVirtualAuthenticator", {"options": {
                            "protocol": "ctap2",
                            "transport": "internal",
                            "hasResidentKey": True,
                            "hasUserVerification": True,
                            "isUserVerified": True,
                            "automaticPresenceSimulation": True,
                        }})

                        def activate_semantics():
                            semantics = page.locator("flt-semantics-placeholder")
                            if semantics.count():
                                semantics.evaluate("(el) => el.click()")

                        def open_profile():
                            page.goto(origin + "/#/profile", wait_until="domcontentloaded", timeout=60000)
                            page.wait_for_selector("flutter-view, flt-glass-pane", timeout=60000)
                            activate_semantics()
                            header = page.get_by_role(
                                "button", name=re.compile(r"^Medical tracking", re.I)
                            ).first
                            header.wait_for(state="visible", timeout=25000)
                            # Flutter exposes the two legacy inputs as anonymous
                            # textbox roles. Their preceding visible Min/Max
                            # labels do NOT become accessible names. Assert
                            # both the exact target-region sequence in the
                            # ARIA tree and two actual visible textbox nodes.
                            editors = page.get_by_role("textbox")
                            # Flutter may collapse adjacent Min/Max labels
                            # into ONE text semantics node or emit two nodes.
                            # In both layouts insist on the target heading,
                            # BOTH labels in order, and two actual textboxes.
                            target_region = re.compile(
                                r"- text: Glucose target \(mg/dL\) Min"
                                r"(?:\s+Max)?\s*\n"
                                r"\s*- textbox\s*\n"
                                r"(?:\s*- text: Max\s*\n)?"
                                r"\s*- textbox"
                            )
                            reopen_count, stable = 0, 0
                            for _ in range(90):
                                state = header.get_attribute("aria-description")
                                if state == "Collapsed" and reopen_count < 4:
                                    header.click(timeout=18000)
                                    reopen_count += 1
                                    stable = 0
                                    page.wait_for_timeout(350)
                                    continue
                                if state not in ("Collapsed", "Expanded"):
                                    raise AssertionError(f"BEFORE panel state invalid: {state!r}")
                                snapshot = page.locator("body").aria_snapshot()
                                ready = (
                                    state == "Expanded"
                                    and editors.count() == 2
                                    and bool(target_region.search(snapshot))
                                    and all(editors.nth(k).is_visible() for k in range(2))
                                )
                                if ready:
                                    stable += 1
                                    if stable >= 3:
                                        return header, editors
                                else:
                                    stable = 0
                                    # Flutter virtualizes offscreen semantics.
                                    # Unlike the AFTER warning, the old text
                                    # fields sit lower in the scrollable medical
                                    # panel, so scan the REAL rendered viewport
                                    # before judging the editor absent.
                                    if state == "Expanded":
                                        vp = page.viewport_size
                                        page.mouse.move(
                                            vp["width"] * 0.5, vp["height"] * 0.54
                                        )
                                        page.mouse.wheel(0, 190)
                                page.wait_for_timeout(220)
                            snapshot = page.locator("body").aria_snapshot()
                            raise AssertionError(
                                f"BEFORE editors not visible after bounded scroll: "
                                f"state={state!r}, reopens={reopen_count}, "
                                f"editors={editors.count()}, aria={snapshot[-2100:]!r}"
                            )

                        response = page.goto(origin, wait_until="domcontentloaded", timeout=60000)
                        assert response and response.status == 200
                        page.wait_for_selector("flutter-view, flt-glass-pane", timeout=60000)
                        activate_semantics()
                        page.get_by_role(
                            "button",
                            name=re.compile(
                                r"Continue without an account|Continuer sans compte|المتابعة بدون حساب",
                                re.I,
                            ),
                        ).click(timeout=18000)
                        page.get_by_role(
                            "button",
                            name=re.compile(
                                r"Enable secure lock|Activer le verrou sécurisé|تفعيل القفل الآمن",
                                re.I,
                            ),
                        ).click(timeout=18000)
                        page.wait_for_url(re.compile(r"/onboarding"), timeout=30000)
                        page.get_by_role("checkbox", name="English").click(timeout=15000)
                        country = page.get_by_role("textbox", name="Search for a country")
                        country.click()
                        country.press_sequentially("Morocco", delay=110)
                        page.get_by_role("button", name="Morocco").click(timeout=18000)
                        page.get_by_role("button", name="Start", exact=True).click(timeout=18000)
                        page.wait_for_url(re.compile(r"/dashboard"), timeout=30000)

                        for width, height in VIEWPORTS:
                            page.set_viewport_size({"width": width, "height": height})
                            header, editors = open_profile()
                            assert header.get_attribute("aria-description") == "Expanded"
                            # Align clinical region to the visible viewport, not
                            # a Playwright full-page HTML screenshot that misses
                            # Flutter's internal scroll. Do not crop the result.
                            bottom_safe = height - (95 if width < 700 else 12)
                            for _ in range(25):
                                first = editors.first.bounding_box()
                                last = editors.last.bounding_box()
                                if (first is not None and last is not None
                                        and first["y"] >= 75
                                        and last["y"] >= 75
                                        and first["y"] + first["height"] < bottom_safe
                                        and last["y"] + last["height"] < bottom_safe):
                                    break
                                page.mouse.move(width * 0.5, height * 0.50)
                                direction = -160 if first and first["y"] < 75 else 200
                                page.mouse.wheel(0, direction)
                                page.wait_for_timeout(180)
                            else:
                                raise AssertionError(
                                    f"BEFORE both legacy editors not in {width}x{height}: "
                                    f"first={first!r}, last={last!r}"
                                )
                            assert editors.count() == 2
                            assert not page.get_by_text(
                                "Targets unverified. No medical classification before review."
                            ).count(), "BEFORE accidentally points to D22-B instead of D22-A"
                            target = OUT / f"before-unverified-target-{width}x{height}.png"
                            page.screenshot(
                                path=str(target), full_page=True,
                                animations="disabled", timeout=30000,
                            )
                            data = target.read_bytes()
                            assert data.startswith(bytes.fromhex("89504e470d0a1a0a"))
                            evidence["capture"].append({
                                "viewport": f"{width}x{height}",
                                "file": target.name,
                                "sha256": hashlib.sha256(data).hexdigest(),
                            })
                        # Google Fonts may be attempted by Flutter but are not
                        # permitted to leave the isolated browser process.
                        unexpected = [x for x in blocked if "fonts.gstatic.com" not in x.lower()]
                        assert not unexpected, f"BEFORE external request attempted: {unexpected[:3]}"
                        assert not pageerrors, f"BEFORE Flutter page error: {pageerrors[:3]}"
                        evidence["status"] = "PASS_BEFORE_BASELINE"
                    finally:
                        context.close()
                finally:
                    browser.close()
    finally:
        (OUT / "proof.json").write_text(
            json.dumps(evidence, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    assert evidence["status"] == "PASS_BEFORE_BASELINE", "D22-A BEFORE failed"


if __name__ == "__main__":
    main()
