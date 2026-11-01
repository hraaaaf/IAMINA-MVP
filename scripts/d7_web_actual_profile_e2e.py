#!/usr/bin/env python3
"""D7 actual IAMINA Web ProfileScreen clicks + browser persistence.

Synthetic LOCAL patient; actual Flutter release app, real Chrome, WebAuthn,
IndexedDB. Does not test SSO Vercel, remote account, real clinical consent, or
production patient records. Fails closed on unexpected network egress.
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
EVIDENCE = ROOT / "d7-web-real-profile-chrome-proof.json"
CAPTURE_DIR = ROOT / "d7-web-real-profile-captures"
VIEWPORTS = ((390, 844), (768, 1024), (1280, 900))


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB), **kwargs)

    def log_message(self, *_args):
        pass


class ReusableServer(socketserver.TCPServer):
    allow_reuse_address = True


def main():
    assert (WEB / "main.dart.js").is_file(), "Missing actual Flutter Web build"
    proof = {
        "scope": "actual Flutter ProfileScreen + real Chrome + local WebAuthn + IndexedDB",
        "fixture": "single synthetic LOCAL patient; no SSO, backend or real patients",
        "result": "NOT_RUN",
        "phases": [],
        "captures": [],
        "real_app_locale": "en-US",
        "real_app_fr_ar_rtl": "NOT_RUN",
        "hosted_preview": "NOT_RUN",
        "remote_sync": "NOT_RUN",
        "clinical_privacy_signoff": "NOT_RUN",
    }
    phase = "bootstrap"
    browser = None
    context = None
    page = None
    blocked = []
    errors = []
    try:
        with ReusableServer(("127.0.0.1", 0), QuietHandler) as server:
            threading.Thread(target=server.serve_forever, daemon=True).start()
            origin = f"http://localhost:{server.server_address[1]}"
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                context = browser.new_context(
                    viewport={"width": 1180, "height": 860},
                    locale="en-US",
                    service_workers="block", accept_downloads=False,
                )
                page = context.new_page()
                page.on("pageerror", lambda error: errors.append(type(error).__name__))
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

                def step(name):
                    nonlocal phase
                    phase = name
                    proof["phases"].append(name)
                    print("D7 actual-app phase:", name, flush=True)

                def activate_semantics():
                    placeholder = page.locator("flt-semantics-placeholder")
                    if placeholder.count():
                        placeholder.evaluate("(el) => el.click()")

                def app_route():
                    return page.url.split("#", 1)[-1] if "#" in page.url else ""

                def medical_summary_contains(*parts):
                    # Only the profile summary reflects saved data. Checking
                    # the entire accessibility tree gives false positives:
                    # Type 1 and Type 2 are always present as choice buttons.
                    summary = page.get_by_role(
                        "button", name=re.compile(r"^Medical tracking", re.I)
                    ).first
                    for attempt in range(55):
                        rendered = summary.aria_snapshot()
                        if all(part in rendered for part in parts):
                            return rendered
                        page.wait_for_timeout(200)
                    print("D7 actual profile persisted summary:", rendered[:1200],
                          flush=True)
                    raise AssertionError(
                        "D7 saved medical summary lacks " + repr(parts)
                    )

                def medical_panel_physically_expanded():
                    # Flutter semantics may expose children of a visually
                    # collapsed ExpansionTile. Use rendered card geometry.
                    medical = page.get_by_role(
                        "button", name=re.compile(r"^Medical tracking", re.I)
                    ).first
                    ramadan = page.get_by_role(
                        "button", name=re.compile(r"^Ramadan period", re.I)
                    ).first
                    medical_box = medical.bounding_box()
                    next_box = ramadan.bounding_box()
                    return bool(
                        medical_box and next_box
                        and next_box["y"] - medical_box["y"] > 160
                    )

                def profile_open():
                    page.goto(origin + "/#/profile",
                              wait_until="domcontentloaded", timeout=60000)
                    page.wait_for_selector("flutter-view, flt-glass-pane", timeout=60000)
                    activate_semantics()
                    assert app_route() == "/profile", "Profile route redirected"
                    section = page.get_by_role(
                        "button", name=re.compile(r"^Medical tracking", re.I)
                    ).first
                    section.wait_for(state="visible", timeout=25000)
                    # The Flutter ExpansionTile may rebuild in a collapsed
                    # state *after* the first click, especially following a
                    # physical reload and responsive screenshot series. D7
                    # observed exactly this on explicit_none (a8ca3c5).
                    # Re-open only when genuinely Collapsed; never accept a
                    # stale semantic child or silently skip a failed panel.
                    choice = page.get_by_role(
                        "button", name=re.compile(r"^Type 2 Diabetes$", re.I)
                    ).first
                    open_attempts = 0
                    consecutive_ready = 0
                    for _ in range(80):
                        state = section.get_attribute("aria-description")
                        if state == "Collapsed" and open_attempts < 4:
                            section.click(timeout=18000)
                            open_attempts += 1
                            consecutive_ready = 0
                            page.wait_for_timeout(350)
                            continue
                        if state not in ("Expanded", "Collapsed"):
                            raise AssertionError(
                                f"D7 medical section has no accessible expansion state: {state!r}"
                            )
                        ready = (
                            state == "Expanded" and choice.count() > 0
                            and choice.is_visible()
                            and medical_panel_physically_expanded()
                        )
                        if ready:
                            consecutive_ready += 1
                            if consecutive_ready >= 3:
                                return
                        else:
                            consecutive_ready = 0
                        page.wait_for_timeout(220)
                    print("D7 medical panel state:", state,
                          "open_attempts:", open_attempts, flush=True)
                    print("D7 medical panel ARIA:",
                          page.locator("body").aria_snapshot()[:3800], flush=True)
                    raise AssertionError("D7 medical section not physically expanded in Chrome")

                def click_choice(label):
                    # Flutter InkWell choices aren't HTML form labels.
                    # Match real accessibility roles first, then a semantic
                    # aria-label fallback. Never assume a painted text node.
                    # Playwright's internal role selector parser treats '/'
                    # as a regex delimiter even in escaped patterns. A literal
                    # string avoids InvalidSelectorError for "Not sure / later".
                    # Preserve the already-proven regex path for other choices.
                    role_name = (label if "/" in label
                                 else re.compile(re.escape(label), re.I))
                    options = (
                        page.get_by_role("button", name=role_name),
                        page.get_by_role("checkbox", name=role_name),
                        page.locator('[aria-label*="' + label + '"]'),
                    )
                    # A filter chip only enters Flutter's semantics tree
                    # after its "Report another treatment" expansion animates.
                    # Wait for actual readiness rather than treating the first
                    # render after clicking as the final UI state.
                    for attempt in range(55):
                        for choice in options:
                            if choice.count():
                                choice.first.click(timeout=12000)
                                return
                        page.wait_for_timeout(200)
                    snapshot = page.locator("body").aria_snapshot()
                    print("D7 missing choice:", repr(label), flush=True)
                    print("D7 synthetic accessibility:", snapshot[:3100], flush=True)
                    raise AssertionError("D7 choice missing in real Chrome semantics")

                def save():
                    page.get_by_role("button", name="Save", exact=True).last.click(
                        timeout=18000
                    )
                    # Flutter emits both an ARIA live announcement and a
                    # visible snackbar with identical text. A strict generic
                    # text locator is ambiguous. Assert the visible status;
                    # do not treat the announcement as proof of persistence.
                    page.get_by_text(
                        re.compile("Offline pilot.*saved on this device", re.I)
                    ).last.wait_for(state="visible", timeout=15000)

                def capture_viewports(stage, *expected):
                    assert stage in ("type2", "unknown", "explicit_none")
                    baseline = page.viewport_size
                    CAPTURE_DIR.mkdir(exist_ok=True)
                    try:
                        for width, height in VIEWPORTS:
                            page.set_viewport_size({"width": width, "height": height})
                            # A responsive rebuild can preserve a stale
                            # ExpansionTile semantics node while the real
                            # medical panel is visually collapsed. Reload and
                            # unlock at the target viewport, then open the
                            # medical panel through the same real app journey.
                            reload_and_unlock()
                            medical_summary_contains(*expected)
                            page.get_by_role(
                                "button", name=re.compile(r"^Type 2 Diabetes$", re.I)
                            ).first.wait_for(state="visible", timeout=18000)
                            page.get_by_role(
                                "button", name="Save", exact=True
                            ).first.wait_for(state="visible", timeout=18000)
                            page.wait_for_timeout(250)
                            # Fail closed if desktop shows only the header,
                            # regardless of stale Flutter accessibility nodes.
                            if width >= 1100:
                                assert medical_panel_physically_expanded(), (
                                    "FUE-03 desktop screenshot: medical form "
                                    "is visually collapsed"
                                )
                            name = f"{stage}-{width}x{height}.png"
                            target = CAPTURE_DIR / name
                            page.screenshot(path=str(target), full_page=True,
                                            animations="disabled", timeout=30000)
                            data = target.read_bytes()
                            assert len(data) > 1000, "Empty local D7 screenshot"
                            proof["captures"].append({
                                "stage": stage, "viewport": f"{width}x{height}",
                                "file": name,
                                "sha256": hashlib.sha256(data).hexdigest(),
                            })
                    finally:
                        page.set_viewport_size(baseline)

                def reload_and_unlock():
                    page.reload(wait_until="domcontentloaded", timeout=60000)
                    page.wait_for_selector("flutter-view, flt-glass-pane", timeout=60000)
                    activate_semantics()
                    page.get_by_role("button", name=re.compile("Unlock", re.I)).click(
                        timeout=18000
                    )
                    page.wait_for_url(re.compile("/dashboard"), timeout=30000)
                    profile_open()

                step("genuine_local_webauthn_enrollment")
                response = page.goto(origin, wait_until="domcontentloaded", timeout=60000)
                assert response and response.status == 200
                page.wait_for_selector("flutter-view, flt-glass-pane", timeout=60000)
                activate_semantics()
                page.get_by_role(
                    "button",
                    name=re.compile(
                        r"Continue without an account|Continuer sans compte|المتابعة بدون حساب", re.I
                    ),
                ).click(timeout=18000)
                page.get_by_role(
                    "button",
                    name=re.compile(
                        r"Enable secure lock|Activer le verrou sécurisé|تفعيل القفل الآمن", re.I
                    ),
                ).click(timeout=18000)
                page.wait_for_url(re.compile("/onboarding"), timeout=30000)
                page.get_by_role("checkbox", name="English").click(timeout=15000)
                country = page.get_by_role("textbox", name="Search for a country")
                country.click()
                country.press_sequentially("Morocco", delay=110)
                page.get_by_role("button", name="Morocco").click(timeout=18000)
                page.get_by_role("button", name="Start", exact=True).click(
                    timeout=18000
                )
                page.wait_for_url(re.compile("/dashboard"), timeout=30000)

                step("profile_type2_and_patient_declared_treatments")
                profile_open()
                click_choice("Type 2 Diabetes")
                click_choice("Oral medicines I take")
                extra = page.get_by_role(
                    "button", name="Report another treatment", exact=True
                )
                extra.click(timeout=18000)
                click_choice("Insulin")
                save()

                step("physical_reload_type2_and_treatments_preserved")
                reload_and_unlock()
                medical_summary_contains("Type 2 Diabetes", "Oral medicines", "Insulin")
                capture_viewports("type2", "Type 2 Diabetes", "Oral medicines", "Insulin")
                # Viewport changes rebuild/collapse Flutter ExpansionTile.
                # Navigate and explicitly expand again before another choice.
                profile_open()

                step("patient_type1_without_automatic_treatment_change")
                click_choice("Type 1 Diabetes")
                save()
                reload_and_unlock()
                medical_summary_contains("Type 1 Diabetes", "Oral medicines", "Insulin")

                step("patient_unknown_without_automatic_treatment_change")
                click_choice("Not sure / later")
                save()
                reload_and_unlock()
                medical_summary_contains("Diagnosis not specified", "Oral medicines", "Insulin")
                capture_viewports("unknown", "Diagnosis not specified", "Oral medicines", "Insulin")
                profile_open()

                step("explicit_no_treatment_then_physical_reload")
                click_choice("No treatment to report")
                save()
                reload_and_unlock()
                medical_summary_contains("Diagnosis not specified", "No treatment reported")
                capture_viewports("explicit_none", "Diagnosis not specified", "No treatment reported")
                profile_open()

                step("explicit_treatment_reentry_then_physical_reload")
                click_choice("Insulin")
                save()
                reload_and_unlock()
                medical_summary_contains("Diagnosis not specified", "Insulin")

                step("responsive_390_768_1280_and_egress_check")
                assert len(proof["captures"]) == 9
                page.set_viewport_size({"width": 390, "height": 844})
                medical_summary_contains("Diagnosis not specified", "Insulin")
                non_font = [u for u in blocked if "fonts.gstatic.com" not in u.lower()]
                assert not non_font, "Unexpected outbound network attempted"
                assert not errors, "Uncaught browser JS exception"
                proof["result"] = "PASS"
    except Exception:
        proof["result"] = "FAIL"
        proof["failed_phase"] = phase
        if page is not None:
            try:
                print("D7 failing route:", page.url.split("?", 1)[0], flush=True)
                print("D7 synthetic ARIA:",
                      page.locator("body").aria_snapshot()[:1700], flush=True)
            except Exception:
                pass
        raise
    finally:
        # Playwright's context manager has already exited here. Never mask
        # the original browser failure with a secondary closed-loop error.
        if context:
            try:
                context.close()
            except Exception:
                pass
        if browser:
            try:
                browser.close()
            except Exception:
                pass
        EVIDENCE.write_text(json.dumps(proof, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
