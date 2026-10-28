#!/usr/bin/env python3
"""CI-only loopback WASM fixture server. Never serves patient data."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from functools import partial

_ROOT = Path(__file__).resolve().parents[1] / "frontend" / "web"

_ALLOWED = {
    "/sqlite3.wasm",
    "/iamina_w02_browser_bridge_probe.mjs",
    "/iamina_vault_envelope.mjs",
    "/iamina_vault_ciphertext_store.mjs",
}

_TEST_BRIDGE = Path(__file__).resolve().parent / "fixtures" / "iamina_w02_browser_bridge_probe.mjs"

class WasmFixtureHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        if path == "/iamina_w02_browser_bridge_probe.mjs":
            return str(_TEST_BRIDGE)
        return super().translate_path(path)

    def do_HEAD(self):
        if self.path not in _ALLOWED:
            self.send_error(404)
            return
        super().do_HEAD()
    def do_GET(self):
        if self.path not in _ALLOWED:
            self.send_error(404)
            return
        super().do_GET()

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cross-Origin-Resource-Policy", "cross-origin")
        super().end_headers()

    def guess_type(self, path):
        if path.endswith(".wasm"):
            return "application/wasm"
        if path.endswith(".mjs"):
            return "text/javascript"
        return super().guess_type(path)

if __name__ == "__main__":
    server = ThreadingHTTPServer(
        ("127.0.0.1", 7399),
        partial(WasmFixtureHandler, directory=str(_ROOT)),
    )
    print("W02_LOOPBACK_WASM_SERVER_READY 127.0.0.1:7399", flush=True)
    server.serve_forever()
