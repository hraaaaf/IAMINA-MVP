"""D30 Chromium PWA offline shell regression: real Service Worker, no network.

Uses a localhost release build, never a backend, clinical data or remote account.
The production review Preview intentionally unregisters SW and cannot certify offline.
"""
import http.server
import pathlib
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
    assert (WEB / "iamina_service_worker.js").is_file()
    assert (WEB / "iamina_app_lock.js").is_file()
    with ReusableServer(("127.0.0.1", 0), QuietHandler) as server:
        threading.Thread(target=server.serve_forever, daemon=True).start()
        origin = f"http://localhost:{server.server_address[1]}"
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            context = None
            try:
                context = browser.new_context(
                    viewport={"width": 1180, "height": 860},
                    service_workers="allow",
                )
                page = context.new_page()
                errors, blocked_external = [], []
                page.on("pageerror", lambda e: errors.append(str(e)))

                def local_only(route):
                    u = route.request.url
                    if u.startswith(origin + "/") or u.startswith(("data:", "blob:")):
                        route.continue_()
                    else:
                        blocked_external.append(u)
                        route.abort()
                page.route("**/*", local_only)

                response = page.goto(origin, wait_until="domcontentloaded", timeout=60000)
                assert response is not None and response.status == 200
                page.wait_for_selector("flutter-view, flt-glass-pane", timeout=60000)
                page.wait_for_function(
                    "() => navigator.serviceWorker && navigator.serviceWorker.controller != null",
                    timeout=45000,
                )

                # Prime dynamic CanvasKit/assets with a normal controlled reload.
                page.reload(wait_until="domcontentloaded", timeout=60000)
                page.wait_for_selector("flutter-view, flt-glass-pane", timeout=60000)
                page.wait_for_function(
                    """async () => {
                      const names = await caches.keys();
                      const shell = names.find(n => n.startsWith('iamina-app-shell-'));
                      if (!shell) return false;
                      const cache = await caches.open(shell);
                      return !!(await cache.match('./iamina_app_lock.js')) &&
                        !!(await cache.match('./main.dart.js')) &&
                        !!(await cache.match('./index.html'));
                    }""",
                    timeout=30000,
                )
                cache_meta = page.evaluate(
                    """async () => {
                      const key = (await caches.keys()).find(n => n.startsWith('iamina-app-shell-'));
                      const cache = await caches.open(key);
                      const urls = (await cache.keys()).map(r => r.url);
                      return { name:key, count:urls.length,
                               hasLock:urls.some(u => u.endsWith('/iamina_app_lock.js')),
                               hasCanvasKit:urls.some(u => u.includes('/canvaskit/')),
                               fontAssets: ['Inter.ttf', 'InterTight.ttf', 'Roboto.ttf',
                                 'NotoSansArabic.ttf', 'NotoSansSymbols.ttf',
                                 'NotoSansSymbols2.ttf'].filter(n =>
                                 urls.some(u => u.endsWith('/assets/assets/fonts/' + n))) };
                    }"""
                )
                print("D30 offline cache:", cache_meta, flush=True)
                assert cache_meta["hasLock"], "Offline WebAuthn verifier not precached"
                assert cache_meta["hasCanvasKit"], "CanvasKit assets not cached during online prime"
                assert len(cache_meta["fontAssets"]) == 6, (
                    "Multilingual offline fonts missing from PWA cache: " +
                    repr(cache_meta["fontAssets"])
                )

                context.set_offline(True)
                page.reload(wait_until="domcontentloaded", timeout=60000)
                page.wait_for_selector("flutter-view, flt-glass-pane", timeout=60000)
                page.wait_for_timeout(900)
                assert not errors, f"Offline Flutter uncaught JS errors: {errors[:4]}"
                page.screenshot(path="/tmp/d30-web-offline-shell.png")
                print(
                    "D30 OFFLINE SHELL PASS: service worker serves boot, "
                    "local app-lock verifier and CanvasKit with network disabled. "
                    f"Blocked remote font attempts: {len(blocked_external)}",
                    flush=True,
                )
            except Exception:
                if context is not None:
                    try:
                        page.screenshot(path="/tmp/d30-web-offline-failure.png")
                        print("D30 offline failure URL:", page.url, flush=True)
                        print("D30 offline JS errors:", errors[:6], flush=True)
                    except Exception:
                        pass
                raise
            finally:
                if context:
                    context.close()
                browser.close()
                server.shutdown()


if __name__ == "__main__":
    main()
