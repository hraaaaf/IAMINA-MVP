"""Read-only D30 Flutter Web Chromium smoke. No patient data, remote APIs or deployment."""
import contextlib
import http.server
import pathlib
import socketserver
import threading
import time

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
    if not (WEB / "index.html").exists():
        raise SystemExit("D30 Web smoke: missing build/web/index.html")
    with ReusableServer(("127.0.0.1", 0), QuietHandler) as server:
        threading.Thread(target=server.serve_forever, daemon=True).start()
        origin = f"http://127.0.0.1:{server.server_address[1]}"
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                context = browser.new_context(service_workers="block")
                page = context.new_page()
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                response = page.goto(origin, wait_until="domcontentloaded", timeout=60000)
                if response is None or response.status != 200:
                    raise AssertionError(f"Flutter Web HTML not served: {response}")
                page.wait_for_function(
                    "() => !!document.querySelector('flutter-view, flt-glass-pane')",
                    timeout=60000,
                )
                page.screenshot(path="/tmp/d30-flutter-web-boot.png")
                if errors:
                    raise AssertionError(f"Flutter Web uncaught errors: {errors[:3]}")
                print("D30 Chrome smoke PASS: Web booted locally; no clinical interaction executed.")
                context.close()
            finally:
                browser.close()
                server.shutdown()


if __name__ == "__main__":
    main()
