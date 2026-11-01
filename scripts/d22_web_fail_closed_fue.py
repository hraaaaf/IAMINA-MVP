#!/usr/bin/env python3
"""D22-B bounded real-Chrome Web evidence; LOCAL synthetic patient only.

Implements only F01 unit preference/reload, F03 unknown legacy target hiding,
and F07 viewport rendering in English. F02 approved-target conversion, F04
source unit edits, F05 CGM/report parity, F06 A/B and FR/AR RTL F07 remain
NOT_RUN until the clinical/data contract allows those workflows.
Never calls hosted preview, production API or real patient records.
"""
import hashlib
import http.server
import json
import pathlib
import re
import socketserver
import threading

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[1]
WEB = ROOT / "frontend" / "build" / "web"
OUT = ROOT / "d22-web-real-chrome"
VIEWPORTS = ((390, 844), (768, 1024), (1280, 900))


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB), **kwargs)

    def log_message(self, *_args):
        pass


class LocalServer(socketserver.TCPServer):
    allow_reuse_address = True


def main():
    assert (WEB / "main.dart.js").is_file(), "Missing actual Flutter Web build"
    OUT.mkdir(exist_ok=True)
    evidence = {
        "decision": "D22-B",
        "scope": "local actual Flutter release Web + real Playwright Chromium",
        "fixture": "one synthetic local account, isolated browser context, no patient records",
        "result": "NOT_RUN",
        "verified_scenarios": [],
        "captures": [],
        "not_run": [
            "F02 approved clinician target conversion",
            "F04 raw measurement/source edit + remote persistence",
            "F05 approved target and CGM PDF/CSV consistency",
            "F06 real A/B account and remote privacy",
            "F07 FR/AR RTL and 200pct zoom / native-language audit",
            "D22 BEFORE screenshots from an independently captured reference",
            "clinical approval and production/SSO deployment",
        ],
    }
    errors = []
    blocked = []
    try:
        with LocalServer(("127.0.0.1", 0), QuietHandler) as server:
            threading.Thread(target=server.serve_forever, daemon=True).start()
            origin = f"http://localhost:{server.server_address[1]}"
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                try:
                    context = browser.new_context(
                        viewport={"width": 1180, "height": 860},
                        locale="en-US",
                        service_workers="block",
                        accept_downloads=False,
                    )
                    try:
                        page = context.new_page()
                        page.on("pageerror", lambda err: errors.append(str(err)[:180]))

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
                            "protocol": "ctap2", "transport": "internal",
                            "hasResidentKey": True, "hasUserVerification": True,
                            "isUserVerified": True, "automaticPresenceSimulation": True,
                        }})

                        def activate_semantics():
                            pl = page.locator("flt-semantics-placeholder")
                            if pl.count():
                                pl.evaluate("(el) => el.click()")

                        def profile_open():
                            page.goto(origin + "/#/profile", wait_until="domcontentloaded", timeout=60000)
                            page.wait_for_selector("flutter-view, flt-glass-pane", timeout=60000)
                            activate_semantics()
                            section = page.get_by_role(
                                "button", name=re.compile(r"^Medical tracking", re.I)
                            ).first
                            section.wait_for(state="visible", timeout=25000)
                            state = section.get_attribute("aria-description")
                            if state == "Collapsed":
                                section.click(timeout=18000)
                            elif state != "Expanded":
                                raise AssertionError("D22 profile tile has no accessible expansion state")
                            # Verify visible, rendered children; do not infer success
                            # from a click, a stale semantic node or whitespace geometry.
                            page.get_by_role(
                                "button", name=re.compile(r"^Type 2 Diabetes$", re.I)
                            ).first.wait_for(state="visible", timeout=18000)
                            page.get_by_text(
                                "Targets unverified. No medical classification before review."
                            ).first.wait_for(state="visible", timeout=18000)
                            return section

                        def save_profile():
                            page.get_by_role(
                                "button", name="Save", exact=True
                            ).last.click(timeout=18000)
                            page.get_by_text(
                                re.compile("Offline pilot.*saved on this device", re.I)
                            ).last.wait_for(state="visible", timeout=15000)

                        def reload_and_unlock():
                            page.reload(wait_until="domcontentloaded", timeout=60000)
                            page.wait_for_selector("flutter-view, flt-glass-pane", timeout=60000)
                            activate_semantics()
                            page.get_by_role(
                                "button", name=re.compile(r"Unlock", re.I)
                            ).click(timeout=18000)
                            page.wait_for_url(re.compile(r"/dashboard"), timeout=30000)

                        def assert_profile_unit(unit):
                            # Unlocking returns to /dashboard, not /profile.
                            # Navigate to the real profile before inspecting
                            # persisted state. Child choice buttons always
                            # contain both units, so a whole subtree snapshot
                            # would be a false-positive persistence oracle.
                            profile_open()
                            section = page.get_by_role(
                                "button", name=re.compile(r"^Medical tracking", re.I)
                            ).first
                            for _ in range(55):
                                label = section.get_attribute("aria-label") or ""
                                if unit in label:
                                    break
                                page.wait_for_timeout(200)
                            else:
                                raise AssertionError(
                                    f"Persisted profile header has no {unit}: {label[:300]!r}"
                                )
                            other_unit = "mg/dL" if unit == "mmol/L" else "mmol/L"
                            assert other_unit not in label, (
                                f"Profile summary unexpectedly contains both units: {label!r}"
                            )

                        # Actual local account, onboarding, local WebAuthn and
                        # IndexedDB; same setup as the already-certified D7 FUE.
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
                        page.get_by_role(
                            "button", name="Start", exact=True
                        ).click(timeout=18000)
                        page.wait_for_url(re.compile(r"/dashboard"), timeout=30000)
                        evidence["verified_scenarios"].append("local onboarding and route")

                        profile_open()
                        page.get_by_role(
                            "button", name="mmol/L", exact=True
                        ).first.click(timeout=15000)
                        save_profile()
                        reload_and_unlock()
                        assert_profile_unit("mmol/L")
                        evidence["verified_scenarios"].append(
                            "F01: display preference mmol/L persists after real reload"
                        )

                        page.get_by_role(
                            "button", name="mg/dL", exact=True
                        ).first.click(timeout=15000)
                        save_profile()
                        reload_and_unlock()
                        assert_profile_unit("mg/dL")
                        evidence["verified_scenarios"].append(
                            "F01: display preference return mg/dL persists after real reload"
                        )

                        for width, height in VIEWPORTS:
                            page.set_viewport_size({"width": width, "height": height})
                            section = profile_open()
                            # A stored numerical legacy target never becomes a
                            # visible editable target in the medically unapproved UI.
                            assert section.get_attribute("aria-description") == "Expanded"
                            tree = page.locator("body").aria_snapshot()
                            assert "Targets unverified." in tree
                            # Negative F03 oracle: an explanatory banner by
                            # itself is not proof that legacy target bounds
                            # cannot be edited. Reject accessible min/max
                            # target input controls on the real profile.
                            target_editors = page.get_by_role(
                                "textbox", name=re.compile(
                                    r"\b(minimum|maximum)\b", re.I
                                )
                            )
                            assert target_editors.count() == 0, (
                                "Unverified glucose target still exposes editable bounds"
                            )
                            # These are only post-change English captures, not a
                            # BEFORE/AFTER score or a clinical target migration.
                            target = OUT / f"f03-unknown-target-{width}x{height}.png"
                            page.screenshot(
                                path=str(target), full_page=True,
                                animations="disabled", timeout=30000,
                            )
                            data = target.read_bytes()
                            assert data.startswith(bytes.fromhex("89504e470d0a1a0a"))
                            assert len(data) > 1000
                            evidence["captures"].append({
                                "viewport": f"{width}x{height}",
                                "file": target.name,
                                "sha256": hashlib.sha256(data).hexdigest(),
                            })
                        evidence["verified_scenarios"].append(
                            "F03 limited: unverified legacy-style target not editable at 3 viewports"
                        )
                        evidence["verified_scenarios"].append(
                            "F07 partial: English real-Chrome 390x844, 768x1024, 1280x900"
                        )
                        unexpected = [x for x in blocked if "fonts.gstatic.com" not in x.lower()]
                        assert not unexpected, f"Unexpected network egress: {unexpected[:3]}"
                        assert not errors, f"Uncaught JS errors: {errors[:3]}"
                        evidence["result"] = "PASS_PARTIAL"
                    finally:
                        context.close()
                finally:
                    browser.close()
    finally:
        (OUT / "proof.json").write_text(
            json.dumps(evidence, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    assert evidence["result"] == "PASS_PARTIAL", "D22 real Chrome partial FUE failed"


if __name__ == "__main__":
    main()
