"""D30 read-only local enrollment transition in a real headless Chromium.

The test is intentionally limited to the first local-only button. It never
creates a clinical record, invokes backend login or bypasses WebAuthn.
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
    assert (WEB / "index.html").is_file(), "Missing release Web bundle"
    with ReusableServer(("127.0.0.1", 0), QuietHandler) as server:
        threading.Thread(target=server.serve_forever, daemon=True).start()
        origin = f"http://127.0.0.1:{server.server_address[1]}"
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            try:
                context = browser.new_context(service_workers="block")
                page = context.new_page()
                js_errors = []
                external = []
                page.on("pageerror", lambda exc: js_errors.append(str(exc)))

                def block_external(route):
                    url = route.request.url
                    if url.startswith(origin + "/") or url.startswith(("data:", "blob:")):
                        route.continue_()
                    else:
                        external.append(url)
                        route.abort()

                page.route("**/*", block_external)
                try:
                    page.goto(origin + "/#/login", wait_until="domcontentloaded", timeout=60000)
                    page.wait_for_function(
                        "() => !!document.querySelector('flutter-view, flt-glass-pane')",
                        timeout=60000,
                    )
                    # Flutter Web does not expose semantic text nodes until
                    # accessibility is activated in some renderer variants.
                    placeholder = page.locator("flt-semantics-placeholder")
                    if placeholder.count() > 0 and placeholder.is_visible():
                        placeholder.click(timeout=10000)
                    button = page.get_by_role(
                        "button", name=re.compile(r"Set up this device", re.I)
                    )
                    button.wait_for(state="visible", timeout=30000)
                    button.click(timeout=20000)
                    page.wait_for_url(re.compile(r"/app-lock/setup"), timeout=30000)
                    page.wait_for_function(
                        "() => !!document.querySelector('flutter-view, flt-glass-pane')",
                        timeout=30000,
                    )
                    if js_errors:
                        raise AssertionError(f"Uncaught JavaScript errors: {js_errors[:4]}")
                    if any("/api/" in url.lower() for url in external):
                        raise AssertionError(f"Unexpected remote API attempts: {external[:4]}")
                    print("D30 ENROLLMENT TRANSITION PASS: local button navigates to app-lock/setup")
                except Exception:
                    print(f"D30 first-use URL: {page.url}")
                    print(f"D30 Web JS errors: {js_errors[:5]}")
                    print(f"D30 blocked non-local URLs: {external[:8]}")
                    print(
                        "D30 accessibility buttons:",
                        page.get_by_role("button").all_text_contents()[:12],
                    )
                    raise
                finally:
                    page.screenshot(
                        path="/tmp/d30-local-enrollment-transition.png",
                        full_page=True,
                    )
                    context.close()
            finally:
                browser.close()
                server.shutdown()


if __name__ == "__main__":
    main()
