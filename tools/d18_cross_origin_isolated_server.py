#!/usr/bin/env python3
"""Isolated D18 localhost server: cross-origin isolation required by OPFS sync APIs."""
import http.server
import sys

class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        super().end_headers()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: d18_cross_origin_isolated_server.py ROOT")
    import os
    os.chdir(sys.argv[1])
    http.server.ThreadingHTTPServer(("127.0.0.1", 7398), Handler).serve_forever()
