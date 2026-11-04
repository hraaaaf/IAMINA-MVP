#!/usr/bin/env python3
"""D18 synthetic-only HTTP host with fail-closed candidate CSP.

No changes to the deployed frontend or Vercel headers. Browser CI evaluates
this policy on actual Flutter Web + dedicated sqlite3mc workers.
"""
import argparse
import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

CSP = "; ".join((
    "default-src 'none'",
    "base-uri 'self'",
    "object-src 'none'",
    "frame-ancestors 'none'",
    "form-action 'self'",
    "script-src 'self' 'wasm-unsafe-eval'",
    "script-src-attr 'none'",
    "worker-src 'self'",
    "child-src 'self'",
    "connect-src 'self'",
    "img-src 'self' data: blob:",
    "font-src 'self' data:",
    "style-src 'self' 'unsafe-inline'",
    "manifest-src 'self'",
    "media-src 'self' blob:",
))


class D18CspHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Content-Security-Policy", CSP)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        super().end_headers()

    def log_message(self, format, *args):
        # No request URLs or query strings in CI logs.
        pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", required=True)
    parser.add_argument("--port", type=int, default=7398)
    args = parser.parse_args()
    # No 'unsafe-eval' or 'unsafe-inline' in SCRIPT policy.
    script_directive = next(d for d in CSP.split("; ") if d.startswith("script-src "))
    assert "'unsafe-eval'" not in script_directive
    assert "'unsafe-inline'" not in script_directive
    handler = functools.partial(D18CspHandler, directory=args.directory)
    with ThreadingHTTPServer(("127.0.0.1", args.port), handler) as server:
        server.serve_forever()


if __name__ == "__main__":
    main()
