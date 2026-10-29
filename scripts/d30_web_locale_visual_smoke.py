"""D30 Web localized first-use visual smoke at identical 1180x860 viewport.

Read-only: no auth, patient profiles, backend, clinical writes or deployment.
All non-loopback resources are blocked to validate local font availability.
"""
import http.server
import pathlib
import socketserver
import threading
from playwright.sync_api import sync_playwright

WEB = pathlib.Path(__file__).resolve().parents[1] / "frontend" / "build" / "web"


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB), **kwargs)

    def log_message(self, *_args):
        pass


class Server(socketserver.TCPServer):
    allow_reuse_address = True


def main():
    assert (WEB / "index.html").is_file(), "Missing compiled Web bundle"
    with Server(("127.0.0.1", 0), Handler) as server:
        threading.Thread(target=server.serve_forever, daemon=True).start()
        origin = f"http://localhost:{server.server_address[1]}"
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                for language, cta in (
                    ("fr-FR", "Configurer cet appareil"),
                    ("ar-MA", "إعداد هذا الجهاز"),
                ):
                    context = browser.new_context(
                        locale=language,
                        viewport={"width": 1180, "height": 860},
                        service_workers="block",
                    )
                    page = context.new_page()
                    unexpected = []
                    errors = []
                    page.on("pageerror", lambda err: errors.append(str(err)))

                    def local_only(route):
                        url = route.request.url
                        if url.startswith(origin + "/") or url.startswith(("data:", "blob:")):
                            route.continue_()
                        else:
                            unexpected.append((route.request.method, url))
                            route.abort()

                    page.route("**/*", local_only)
                    try:
                        response = page.goto(
                            origin, wait_until="domcontentloaded", timeout=60000
                        )
                        assert response and response.status == 200
                        page.wait_for_selector(
                            "flutter-view, flt-glass-pane", timeout=60000
                        )
                        placeholder = page.locator("flt-semantics-placeholder")
                        if placeholder.count():
                            placeholder.evaluate("(element) => element.click()")
                        button = page.get_by_role("button", name=cta)
                        button.wait_for(state="visible", timeout=30000)
                        page.wait_for_timeout(500)
                        filename = language[:2]
                        page.screenshot(
                            path=f"/tmp/d30-web-offline-fonts-{filename}.png",
                            full_page=False,
                        )
                        assert not errors, errors[:4]
                        assert not any(
                            method not in ("GET", "HEAD", "OPTIONS") or
                            "/api/" in url.lower()
                            for method, url in unexpected
                        ), unexpected[:5]
                        print(
                            f"D30 LOCAL FONT {language} PASS: localized CTA visible, "
                            f"no external write; blocked font attempts "
                            f"{len(unexpected)}"
                        )
                    except Exception:
                        page.screenshot(
                            path=f"/tmp/d30-web-offline-fonts-failure-{language[:2]}.png",
                            full_page=False,
                        )
                        print(
                            f"D30 {language} route={page.url} "
                            f"snapshot={page.locator('body').aria_snapshot()[:850]}"
                        )
                        raise
                    finally:
                        context.close()
            finally:
                browser.close()
                server.shutdown()


if __name__ == "__main__":
    main()
