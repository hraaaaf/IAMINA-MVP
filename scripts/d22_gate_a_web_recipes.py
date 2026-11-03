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
import os
import pathlib
import re
import socketserver
import struct
import threading

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[1]
WEB = ROOT / "frontend" / "build" / "web"
LOCALE = os.environ.get("D22_FUE_LOCALE", "en")
assert LOCALE in ("en", "fr", "ar"), "Unsupported Web fixture locale"
COPIES = {
    "en": dict(medical="Medical tracking", type2="Type 2 Diabetes",
               banner="Targets unverified. No medical classification before review.",
               target_title="Glucose targets unverified",
               old_target_title="Glucose target (mg/dL)",
               saved_prefix="Offline pilot", language="English",
               country_search="Search for a country", country="Morocco",
               start="Start", save="Save", unlock="Unlock IAmina"),
    "fr": dict(medical="Suivi médical", type2="Diabète Type 2",
               banner="Objectifs non vérifiés. Aucun classement médical avant validation.",
               target_title="Objectifs non vérifiés",
               old_target_title="Cible glycémique (mg/dL)",
               saved_prefix="Pilote local", language="Français",
               country_search="Rechercher un pays", country="Maroc",
               start="Commencer", save="Enregistrer", unlock="Déverrouiller IAmina"),
    "ar": dict(medical="المتابعة الطبية", type2="السكري النوع 2",
               banner="الأهداف غير مؤكدة. لا تصنيف طبي قبل التحقق.",
               target_title="أهداف سكر الدم غير مؤكدة",
               old_target_title="الهدف الجلوكوزي (mg/dL)",
               saved_prefix="الوضع المحلي", language="العربية",
               country_search="ابحث عن بلد", country="المغرب",
               start="ابدأ", save="حفظ", unlock="فتح IAmina"),
}
COPY = COPIES[LOCALE]
OUT = ROOT / ("d22-web-real-chrome" if LOCALE == "en"
              else f"d22-web-real-chrome-{LOCALE}")
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
        "decision": "D22 Gate A",
        "locale": LOCALE,
        "scope": "local actual Flutter release Web + real Playwright Chromium",
        "fixture": "one synthetic local account, isolated browser context, no patient records",
        "result": "NOT_RUN",
        "verified_scenarios": [],
        "captures": [],
        "accessibility": {"status": "NOT_RUN", "checks": [], "captures": []},
        "unit_heading_checks": [],
        "unit_label_captures": [],
        "not_run": [
            "F02 approved clinician target conversion",
            "F04 raw measurement/source edit + remote persistence",
            "F05 approved target and CGM PDF/CSV consistency",
            "F06 real A/B account and remote privacy",
            "F07 native Chrome toolbar zoom 200pct and native RTL language review",
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
                        locale={"en": "en-US", "fr": "fr-FR", "ar": "ar-MA"}[LOCALE],
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
                                "button", name=re.compile(r"^" + re.escape(COPY["medical"]), re.I)
                            ).first
                            section.wait_for(state="visible", timeout=25000)
                            # Flutter localizes its expansion aria-description:
                            # EN "Collapsed", FR "Réduit", and AR uses localized
                            # semantics. Never treat a non-English string as an
                            # invalid state; the actual visible medical choice
                            # AND clinical notice must be present three times.
                            # Reopen by a genuine click only while still closed;
                            # fail after bounded retries, never force a click.
                            choice = page.get_by_role(
                                "button", name=re.compile(r"^" + re.escape(COPY["type2"]) + r"$", re.I)
                            ).first
                            banner = page.get_by_text(
                                COPY["banner"]
                            ).first
                            reopen_count = 0
                            stable = 0
                            missing = 0
                            # Only this narrow set is used as a click hint;
                            # success always requires rendered medical content.
                            collapsed_labels = ("Collapsed", "Réduit", "مطوي", "منهار")
                            for _ in range(80):
                                state = section.get_attribute("aria-description")
                                ready = (
                                    choice.count() > 0 and choice.is_visible()
                                    and banner.count() > 0 and banner.is_visible()
                                )
                                if ready:
                                    stable += 1
                                    missing = 0
                                    if stable >= 3:
                                        return section
                                else:
                                    stable = 0
                                    missing += 1
                                    if reopen_count < 4 and (
                                        state in collapsed_labels or missing >= 7
                                    ):
                                        section.click(timeout=18000)
                                        reopen_count += 1
                                        missing = 0
                                        page.wait_for_timeout(350)
                                        continue
                                page.wait_for_timeout(220)
                            raise AssertionError(
                                f"D22 profile medical panel never rendered open: "
                                f"state={state!r} reopen_count={reopen_count}"
                            )

                        def save_profile():
                            page.get_by_role(
                                "button", name=COPY["save"], exact=True
                            ).last.click(timeout=18000)
                            page.get_by_text(
                                re.compile(re.escape(COPY["saved_prefix"]), re.I)
                            ).last.wait_for(state="visible", timeout=15000)

                        def reload_and_unlock():
                            page.reload(wait_until="domcontentloaded", timeout=60000)
                            page.wait_for_selector("flutter-view, flt-glass-pane", timeout=60000)
                            activate_semantics()
                            page.get_by_role(
                                "button", name=re.compile(re.escape(COPY["unlock"]), re.I)
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
                                "button", name=re.compile(r"^" + re.escape(COPY["medical"]), re.I)
                            ).first
                            # Flutter's semantic header is exposed through
                            # the computed accessible name, but not through an
                            # HTML aria-label attribute. Inspect only the
                            # header line of the widget's ARIA snapshot:
                            # descendants contain both unit choice buttons.
                            for _ in range(55):
                                snapshot = section.aria_snapshot()
                                header = next(
                                    (line.strip() for line in snapshot.splitlines()
                                     if "button" in line and COPY["medical"] in line),
                                    "",
                                )
                                if unit in header:
                                    break
                                page.wait_for_timeout(200)
                            else:
                                raise AssertionError(
                                    f"Persisted profile summary has no {unit}: "
                                    f"{snapshot[:350]!r}"
                                )
                            other_unit = "mg/dL" if unit == "mmol/L" else "mmol/L"
                            assert other_unit not in header, (
                                f"Profile header unexpectedly contains both units: {header!r}"
                            )
                            # The title must never retain the implicit old-unit
                            # claim regardless of this display preference.
                            title = page.get_by_text(COPY["target_title"], exact=True)
                            title.first.wait_for(state="visible", timeout=15000)
                            assert page.get_by_text(
                                COPY["old_target_title"], exact=True
                            ).count() == 0, (
                                f"Hard-coded mg/dL target heading visible with {unit}"
                            )
                            evidence["unit_heading_checks"].append({
                                "selected_unit": unit, "locale": LOCALE,
                                "title": COPY["target_title"],
                                "stale_title_absent": True,
                            })

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
                        page.get_by_role("checkbox", name=COPY["language"]).click(timeout=15000)
                        country = page.get_by_role("textbox", name=COPY["country_search"])
                        country.click()
                        country.press_sequentially(COPY["country"], delay=110)
                        page.get_by_role("button", name=COPY["country"]).click(timeout=18000)
                        page.get_by_role(
                            "button", name=COPY["start"], exact=True
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

                        # BEFORE/AFTER fixture: render exactly the same three
                        # viewports with mmol/L selected, showing the newly
                        # neutral target heading and the fail-closed notice.
                        for width, height in VIEWPORTS:
                            page.set_viewport_size({"width": width, "height": height})
                            profile_open()
                            title = page.get_by_text(COPY["target_title"], exact=True)
                            title.first.wait_for(state="visible", timeout=15000)
                            banner_mmol = page.get_by_text(COPY["banner"]).first
                            for _ in range(16):
                                box = banner_mmol.bounding_box()
                                safe = height - (95 if width < 700 else 12)
                                if box and box["y"] >= 80 and box["y"] + box["height"] < safe:
                                    break
                                page.mouse.move(width * 0.5, height * 0.52)
                                page.mouse.wheel(0, 260)
                                page.wait_for_timeout(180)
                            else:
                                raise AssertionError(
                                    f"F01 mmol/L notice not visible at {width}x{height}: {box}"
                                )
                            target_mmol = OUT / f"f01-neutral-target-mmol-{width}x{height}.png"
                            page.screenshot(path=str(target_mmol), full_page=False,
                                            animations="disabled", timeout=30000)
                            png = target_mmol.read_bytes()
                            assert struct.unpack(">II", png[16:24]) == (width, height)
                            evidence["unit_label_captures"].append({
                                "viewport": f"{width}x{height}",
                                "state": "mmol/L",
                                "file": target_mmol.name,
                                "sha256": hashlib.sha256(png).hexdigest(),
                            })
                        page.set_viewport_size({"width": 1180, "height": 860})
                        profile_open()
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
                            assert page.get_by_text(COPY["banner"]).first.is_visible()
                            tree = page.locator("body").aria_snapshot()
                            assert COPY["banner"] in tree
                            # Negative F03 oracle: an explanatory banner by
                            # itself is not proof that legacy target bounds
                            # cannot be edited. Reject accessible min/max
                            # target input controls on the real profile.
                            # Flutter did not associate old Min/Max text
                            # labels with its textbox accessible names. The
                            # negative oracle must count actual textbox roles
                            # in the fully expanded profile, NOT match a name
                            # those legacy widgets never carried.
                            target_editors = page.get_by_role("textbox")
                            assert target_editors.count() == 0, (
                                "Unverified glucose target still exposes "
                                f"{target_editors.count()} editable textboxes"
                            )
                            assert "- textbox" not in tree, (
                                "Unverified target exposes a textbox in the "
                                "expanded Flutter accessibility tree"
                            )
                            # Flutter scrolls its own profile content inside
                            # the canvas. A full_page Playwright screenshot
                            # does NOT capture offscreen Flutter scroll items.
                            # Ensure the clinical fail-closed banner itself is
                            # visibly inside every captured viewport, including
                            # mobile above the fixed bottom navigation.
                            banner = page.get_by_text(
                                COPY["banner"]
                            ).first
                            bottom_safe = height - (95 if width < 700 else 12)
                            for _ in range(16):
                                rect = banner.bounding_box()
                                if (rect is not None and rect["y"] >= 80
                                        and rect["y"] + rect["height"] < bottom_safe):
                                    break
                                page.mouse.move(width * 0.5, height * 0.52)
                                page.mouse.wheel(0, 260)
                                page.wait_for_timeout(180)
                            else:
                                raise AssertionError(
                                    f"F03 banner outside visible {width}x{height} screenshot: {rect}"
                                )
                            # CanvasKit scrolls within Flutter's own view. Playwright
                            # full_page=True temporarily resizes the document to
                            # document.body.scrollWidth. In Arabic 1280, this
                            # falsely captures 6px of blank WHITE body outside
                            # the 1280px Flutter view (checked in the PNG).
                            # Capture the exact, unresized viewport instead.
                            # Keep strict pixel dimensions AND a separate root
                            # document overflow oracle; don't crop/clip a genuine
                            # horizontal user-scrollable element.
                            target = OUT / f"f03-unknown-target-{width}x{height}.png"
                            page.screenshot(
                                path=str(target), full_page=False,
                                animations="disabled", timeout=30000,
                            )
                            data = target.read_bytes()
                            assert data.startswith(bytes.fromhex("89504e470d0a1a0a"))
                            assert len(data) > 1000
                            pixels = struct.unpack(">II", data[16:24])
                            assert pixels == (width, height), (
                                f"F07 screenshot pixels {pixels} differ from {width}x{height}"
                            )
                            rect_after = banner.bounding_box()
                            assert (
                                rect_after is not None
                                and rect_after["y"] >= 80
                                and rect_after["y"] + rect_after["height"] < bottom_safe
                            ), f"F03 banner lost visibility during viewport capture: {rect_after}"
                            geometry = page.evaluate("""() => {
                                const viewport = window.innerWidth;
                                const overflowNodes = [...document.querySelectorAll('body *')]
                                    .map((el) => {
                                        const rect = el.getBoundingClientRect();
                                        const protrusion = Math.max(0, rect.right - viewport);
                                        if (protrusion < 1 || rect.height <= 0 || rect.width <= 0) return null;
                                        const style = getComputedStyle(el);
                                        return {
                                            tag: el.tagName.toLowerCase(),
                                            id: (el.id || '').slice(0, 72),
                                            cls: String(el.className || '').slice(0, 72),
                                            left: Math.round(rect.left * 10)/10,
                                            right: Math.round(rect.right * 10)/10,
                                            width: Math.round(rect.width * 10)/10,
                                            protrusion: Math.round(protrusion * 10)/10,
                                            position: style.position,
                                            overflowX: style.overflowX,
                                            direction: style.direction,
                                        };
                                    })
                                    .filter(Boolean)
                                    .sort((a,b) => b.protrusion-a.protrusion)
                                    .slice(0, 25);
                                return {
                                    innerWidth: viewport,
                                    htmlScrollWidth: document.documentElement.scrollWidth,
                                    bodyScrollWidth: document.body.scrollWidth,
                                    flutterViewWidth: Math.round(
                                        document.querySelector('flutter-view')?.getBoundingClientRect().width || 0
                                    ),
                                    overflowNodes,
                                };
                            }""")
                            assert geometry["innerWidth"] == width, (
                                f"Unexpected browser viewport: {geometry}"
                            )
                            assert geometry["flutterViewWidth"] == width, (
                                f"Flutter view exceeds or undershoots viewport: {geometry}"
                            )
                            assert geometry["htmlScrollWidth"] <= width, (
                                f"Actual document horizontal overflow: {geometry}"
                            )
                            # Preserve bodyScrollWidth in the evidence. A body
                            # intrinsic width differing from HTML scroll width
                            # is a diagnostic, not permission to hide overflow.
                            evidence["captures"].append({
                                "viewport": f"{width}x{height}",
                                "file": target.name,
                                "sha256": hashlib.sha256(data).hexdigest(),
                                "geometry": geometry,
                            })
                        evidence["verified_scenarios"].append(
                            "F03 limited: unverified legacy-style target not editable at 3 viewports"
                        )
                        evidence["verified_scenarios"].append(
                            f"F07 partial: {LOCALE} real-Chrome 390x844, 768x1024, 1280x900"
                        )

                        # F07 Web accessibility evidence: physical keyboard
                        # Tab/Shift+Tab/Enter on actual Flutter unit controls.
                        # 640x450 CSS px at DPR 2 models a 200% zoomed
                        # 1280x900 desktop. It is NOT toolbar zoom certification.
                        if LOCALE in ("fr", "ar"):
                            page.set_viewport_size({"width": 768, "height": 1024})
                            profile_open()

                            def current_unit_summary():
                                section = page.get_by_role(
                                    "button",
                                    name=re.compile(r"^" + re.escape(COPY["medical"]), re.I)
                                ).first
                                snap = section.aria_snapshot()
                                return next(
                                    (line.strip() for line in snap.splitlines()
                                     if "button" in line and COPY["medical"] in line), ""
                                )

                            mg_button = page.get_by_role("button", name="mg/dL", exact=True).first
                            mg_button.focus()
                            page.keyboard.press("Tab")
                            keyboard_forward_focus = page.evaluate("""() => ({
                                tag: document.activeElement?.tagName || '',
                                label: document.activeElement?.getAttribute('aria-label') || '',
                                text: (document.activeElement?.textContent || '').slice(0, 120),
                            })""")
                            page.keyboard.press("Enter")
                            for _ in range(35):
                                if "mmol/L" in current_unit_summary():
                                    break
                                page.wait_for_timeout(180)
                            else:
                                raise AssertionError(
                                    f"F07 Tab+Enter failed mmol/L: "
                                    f"{keyboard_forward_focus}, {current_unit_summary()}"
                                )
                            page.keyboard.press("Shift+Tab")
                            keyboard_back_focus = page.evaluate("""() => ({
                                tag: document.activeElement?.tagName || '',
                                label: document.activeElement?.getAttribute('aria-label') || '',
                                text: (document.activeElement?.textContent || '').slice(0, 120),
                            })""")
                            page.keyboard.press("Enter")
                            for _ in range(35):
                                if "mg/dL" in current_unit_summary():
                                    break
                                page.wait_for_timeout(180)
                            else:
                                raise AssertionError(
                                    f"F07 Shift+Tab+Enter failed mg/dL: "
                                    f"{keyboard_back_focus}, {current_unit_summary()}"
                                )
                            evidence["accessibility"]["checks"].append({
                                "name": "real-Tab-Enter-ShiftTab-Enter-unit-control",
                                "viewport": "768x1024", "locale": LOCALE,
                                "forward_focus": keyboard_forward_focus,
                                "back_focus": keyboard_back_focus, "result": "PASS",
                            })

                            # Keep Playwright's screenshot viewport in sync
                            # with the CDP CSS layout viewport; an override
                            # alone leaves Playwright at prior 768x1024.
                            page.set_viewport_size({"width": 640, "height": 450})
                            cdp.send("Emulation.setDeviceMetricsOverride", {
                                "width": 640, "height": 450,
                                "deviceScaleFactor": 2, "mobile": False,
                            })
                            profile_open()
                            zoom_state = page.evaluate("""() => ({
                                cssWidth: window.innerWidth,
                                cssHeight: window.innerHeight,
                                dpr: window.devicePixelRatio,
                                rootScrollWidth: document.documentElement.scrollWidth,
                                flutterViewWidth: Math.round(
                                  document.querySelector('flutter-view')?.getBoundingClientRect().width || 0
                                ),
                            })""")
                            assert (
                                zoom_state["cssWidth"] == 640
                                and zoom_state["cssHeight"] == 450
                                and zoom_state["dpr"] == 2
                                and zoom_state["rootScrollWidth"] <= 640
                                and zoom_state["flutterViewWidth"] == 640
                            ), f"F07 equivalent zoom overflow/scale: {zoom_state}"
                            page.get_by_text(
                                COPY["target_title"], exact=True
                            ).first.wait_for(state="visible", timeout=15000)
                            zoom_banner = page.get_by_text(COPY["banner"]).first
                            for _ in range(20):
                                bounds = zoom_banner.bounding_box()
                                if bounds and bounds["y"] >= 0 and bounds["y"] + bounds["height"] < 450 - 75:
                                    break
                                page.mouse.move(300, 230)
                                page.mouse.wheel(0, 230)
                                page.wait_for_timeout(200)
                            else:
                                raise AssertionError(
                                    f"F07 zoom equivalent notice obscured: {bounds}"
                                )
                            assert page.get_by_role("textbox").count() == 0, (
                                "F07 zoom exposed unapproved target editor"
                            )
                            zoom_path = OUT / "f07-zoom200-equivalent-640x450.png"
                            page.screenshot(path=str(zoom_path), full_page=False,
                                            animations="disabled", timeout=30000)
                            zoom_png = zoom_path.read_bytes()
                            zoom_pixels = struct.unpack(">II", zoom_png[16:24])
                            assert zoom_pixels == (640, 450), (
                                f"F07 equivalent zoom pixels must be exact 640x450: {zoom_pixels}"
                            )
                            evidence["accessibility"]["captures"].append({
                                "file": zoom_path.name, "viewport_css": "640x450",
                                "device_pixel_ratio": 2,
                                "pixels": list(zoom_pixels),
                                "sha256": hashlib.sha256(zoom_png).hexdigest(),
                            })
                            evidence["accessibility"]["checks"].append({
                                "name": "desktop-200pct-equivalent-CSS-reflow-DPR2",
                                "locale": LOCALE, "result": "PASS",
                                "geometry": zoom_state,
                                "native_browser_toolbar_zoom": "NOT_RUN",
                            })
                            evidence["accessibility"]["status"] = "PASS_PARTIAL"
                            evidence["verified_scenarios"].append(
                                "F07 partial: keyboard + 200pct-equivalent reflow"
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
