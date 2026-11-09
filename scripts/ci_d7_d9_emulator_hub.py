"""Test-only loopback server: both Android emulators reach SAME Ubuntu hub.
No medical values, remote auth, patient identifiers or clinical API endpoints.
"""
import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock

ALLOWED = {
    "device-one": "same-install-a-b-a-cold-restart",
    "device-two": "fresh-install-no-remote-restore",
}
HUB = "iamina-d7-d9-ubuntu-synthetic"

def serve(port, output):
    state, lock = {}, Lock()
    output.parent.mkdir(parents=True, exist_ok=True)
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            return  # Never log request bodies, user data, or IPs.
        def reply(self, status, data):
            raw = json.dumps(data).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
        def do_GET(self):
            if self.path == "/health":
                return self.reply(200, {"hub": HUB})
            return self.reply(404, {"error": "not_found"})
        def do_POST(self):
            if self.path != "/attest":
                return self.reply(404, {"error": "not_found"})
            length = self.headers.get("Content-Length", "")
            if not length.isdecimal() or int(length) > 300:
                return self.reply(400, {"error": "invalid_length"})
            try:
                data = json.loads(self.rfile.read(int(length)))
            except (ValueError, UnicodeError):
                return self.reply(400, {"error": "invalid_json"})
            if (not isinstance(data, dict)
                    or set(data) != {"role", "result", "scenario"}
                    or data.get("result") != "pass"
                    or data.get("scenario") != ALLOWED.get(data.get("role"))):
                return self.reply(400, {"error": "invalid_attestation"})
            with lock:
                if data["role"] in state:
                    return self.reply(409, {"error": "duplicate"})
                state[data["role"]] = data["scenario"]
                output.write_text(json.dumps({
                    "environment": "two distinct Android emulators on one Ubuntu runner",
                    "shared_hub": HUB,
                    "attestations": state,
                    "physical_devices_tested": False,
                    "remote_profile_restored": False,
                    "clinical_egress_certified": False,
                }, indent=2) + "\n")
            self.reply(200, {"accepted": True})
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    serve(args.port, args.output)
