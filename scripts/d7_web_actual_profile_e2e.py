#!/usr/bin/env python3
"""D7 actual IAMINA Web ProfileScreen clicks + browser persistence.

Synthetic LOCAL patient; actual Flutter release app, real Chrome, WebAuthn,
IndexedDB. Does not test SSO Vercel, remote account, real clinical consent, or
production patient records. Fails closed on unexpected network egress.
"""
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
                    # Read Flutter's real browser accessibility tree, never
                    # treat unselected chips that merely exist as proof.
                    snapshot = page.locator("body").aria_snapshot()
                    for part in parts:
                        assert part in snapshot, (
                            "Medical state did not survive reload: missing " + repr(part)
                        )
                    return snapshot

                def profile_open():
                    page.goto(origin + "/#/profile",
                              wait_until="domcontentloaded", timeout=60000)
                    page.wait_for_selector("flutter-view, flt-glass-pane", timeout=60000)
                    activate_semantics()
                    page.get_by_role("button", name=re.compile("Medical tracking", re.I)).first.wait_for(
                        state="visible", timeout=25000
                    )
                    assert app_route() == "/profile", "Profile route redirected"
                    section = page.get_by_role(
                        "button", name=re.compile(r"^Medical tracking", re.I)
                    ).first
                    section.click(timeout=18000)
                    # Flutter's ExpansionTile uses an animated semantics tree:
                    # a successful click does not mean its children have
                    # become accessible at the exact same instant.
                    for attempt in range(55):
                        snapshot = page.locator("body").aria_snapshot()
                        if "Type 2 Diabetes" in snapshot:
                            break
                        page.wait_for_timeout(200)
                    else:
                        print("D7 medical section did not expose choices:", flush=True)
                        print("D7 medical section ARIA:", snapshot[:3800], flush=True)
                        print("D7 medical section DOM:", section.evaluate(
                            "(el) => el.outerHTML.slice(0, 1400)"
                        ), flush=True)
                        raise AssertionError("D7 medical section not expanded in Chrome")

                def click_choice(label):
                    # Flutter InkWell choices aren't HTML form labels.
                    # Match real accessibility roles first, then a semantic
                    # aria-label fallback. Never assume a painted text node.
                    pattern = re.compile(re.escape(label), re.I)
                    options = (
                        page.get_by_role("button", name=pattern),
                        page.get_by_role("checkbox", name=pattern),
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
                    page.get_by_text(
                        re.compile("Offline pilot.*saved on this device", re.I)
                    ).wait_for(state="visible", timeout=15000)

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

                step("patient_type1_without_automatic_treatment_change")
                click_choice("Type 1 Diabetes")
                save()
                reload_and_unlock()
                medical_summary_contains("Type 1 Diabetes", "Oral medicines", "Insulin")

                step("explicit_no_treatment_then_physical_reload")
                click_choice("No treatment to report")
                save()
                reload_and_unlock()
                medical_summary_contains("Type 1 Diabetes", "No treatment reported")

                step("responsive_390_and_egress_check")
                page.set_viewport_size({"width": 390, "height": 844})
                medical_summary_contains("Type 1 Diabetes", "No treatment reported")
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
