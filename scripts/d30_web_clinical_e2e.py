"""D30 synthetic-only Web clinical E2E: local vault, WebAuthn and persistence.

No real patient, backend account, deployment or remote clinical request.
CDP virtual authenticator exercises the genuine WebAuthn API without bypassing it.
Service workers are blocked to eliminate stale cache from this controlled pass;
offline PWA caching requires its own separate test.
"""
import http.server
import pathlib
import re
import socketserver
import threading

from playwright.sync_api import sync_playwright

WEB = pathlib.Path(__file__).resolve().parents[1] / "frontend" / "build" / "web"


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB), **kwargs)

    def log_message(self, *_args):
        pass


class ReusableServer(socketserver.TCPServer):
    allow_reuse_address = True


def main():
    assert (WEB / "index.html").exists(), "Missing compiled Flutter Web release"
    with ReusableServer(("127.0.0.1", 0), QuietHandler) as server:
        threading.Thread(target=server.serve_forever, daemon=True).start()
        # WebAuthn requires an approved RP ID; localhost is a secure context.
        origin = f"http://localhost:{server.server_address[1]}"
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            context = None
            page = None
            external = []
            errors = []
            try:
                context = browser.new_context(
                    viewport={"width": 1180, "height": 860},
                    service_workers="block",
                )
                page = context.new_page()
                def record_pageerror(error):
                    # Report exact browser exception stack without suppressing it.
                    stack = getattr(error, "stack", None) or ""
                    errors.append(f"route={page.url} message={error}\\nstack={stack}")
                    print("D30 UNCAUGHT JS:", errors[-1][:2500], flush=True)

                page.on("pageerror", record_pageerror)

                def local_only(route):
                    method = route.request.method
                    url = route.request.url
                    clinical = ("/api/v1/logs", "/api/v1/profile", "/api/v1/ai",
                                "/api/v1/chat", "/api/v1/medical")
                    if method not in ("GET", "HEAD", "OPTIONS") and any(
                        endpoint in url.lower() for endpoint in clinical
                    ):
                        external.append((method, url))
                        route.abort()
                    elif url.startswith(origin + "/") or url.startswith(("data:", "blob:")):
                        route.continue_()
                    else:
                        external.append((method, url))
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

                response = page.goto(origin, wait_until="domcontentloaded", timeout=60000)
                assert response is not None and response.status == 200
                page.wait_for_selector("flutter-view, flt-glass-pane", timeout=60000)

                def activate_semantics():
                    placeholder = page.locator("flt-semantics-placeholder")
                    if placeholder.count():
                        placeholder.evaluate("(element) => element.click()")

                def route():
                    return page.url.split("#", 1)[-1] if "#" in page.url else ""

                activate_semantics()
                page.get_by_role("button", name=re.compile("Set up this device", re.I)).click(timeout=18000)
                page.get_by_role("button", name=re.compile("Enable secure lock", re.I)).click(timeout=18000)
                page.wait_for_timeout(1100)
                assert route() == "/onboarding", f"App-lock setup did not reach onboarding: {route()}"
                print("D30 PASS local enrollment -> genuine WebAuthn -> onboarding", flush=True)

                page.get_by_role("checkbox", name="English").click(timeout=12000)
                page.wait_for_timeout(2000)
                country = page.get_by_role("textbox", name="Search for a country")
                country.click()
                country.press_sequentially("Morocco", delay=110)
                page.get_by_role("button", name="Morocco").click(timeout=18000)
                page.get_by_role("button", name="Start", exact=True).click(timeout=18000)
                page.wait_for_timeout(850)
                assert route() == "/dashboard", (
                    f"Local-only account must reach dashboard without mandatory AI "
                    f"consent: {route()}"
                )
                print("D30 PASS minimum local onboarding -> dashboard, no AI gate", flush=True)

                page.get_by_role("button", name="Add my first reading").click(timeout=18000)
                glucose = page.get_by_role("textbox", name=re.compile("GLUCOSE"))
                glucose.click()
                glucose.press_sequentially("112", delay=110)
                page.wait_for_timeout(650)
                print("D30 actual textbox contents:", repr(glucose.input_value()), flush=True)
                save = page.get_by_role("button", name="Save reading")
                assert save.is_enabled(), "112 did not enable local Save reading"
                save.click(timeout=18000)
                page.wait_for_timeout(950)
                saved = page.locator("body").aria_snapshot()
                assert "Reading saved" in saved and "112" in saved, saved[:1900]
                page.screenshot(path="/tmp/d30-clinical-web-saved.png")
                print("D30 PASS synthetic 112 mg/dL saved on local device", flush=True)

                page.reload(wait_until="domcontentloaded", timeout=60000)
                page.wait_for_selector("flutter-view, flt-glass-pane", timeout=60000)
                activate_semantics()
                page.wait_for_timeout(1000)
                assert route() == "/app-lock/unlock", f"Vault did not lock on reload: {route()}"
                page.get_by_role("button", name=re.compile("Unlock", re.I)).click(timeout=18000)
                page.wait_for_timeout(1100)
                assert route() == "/dashboard", (
                    f"D30 must not re-prompt remote AI consent for local-only "
                    f"account after WebAuthn unlock: {route()}"
                )
                reopened = page.locator("body").aria_snapshot()
                assert "112" in reopened, f"Local glucose missing after reload: {reopened[:1600]}"
                page.screenshot(path="/tmp/d30-clinical-web-reopened.png")

                non_font_external = [
                    (method, url) for method, url in external
                    if "fonts.gstatic.com" not in url.lower()
                ]
                assert not non_font_external, f"Unexpected non-font outbound request: {non_font_external[:5]}"
                assert not errors, "Flutter Web page errors with stack: " + repr(errors[:4])
                print(
                    "D30 PASS clinical E2E: 112 survives reload + actual WebAuthn unlock; "
                    f"zero non-font outbound requests; {len(external)} blocked font fallback requests",
                    flush=True,
                )
            except Exception:
                if page is not None:
                    print("D30 failing URL:", page.url.split("?", 1)[0], flush=True)
                    try:
                        print("D30 failure ARIA:", page.locator("body").aria_snapshot()[:1700], flush=True)
                        page.screenshot(path="/tmp/d30-clinical-web-failure.png")
                    except Exception:
                        pass
                print("D30 blocked external attempts:", repr(external[:8]), flush=True)
                raise
            finally:
                if context:
                    context.close()
                browser.close()
                server.shutdown()


if __name__ == "__main__":
    main()
