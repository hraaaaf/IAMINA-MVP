"""Bounded, test-only unit proofs for #7/#9 emulator hub.
No patient data or real credentials; no external network calls.
"""
import json
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
HUB = ROOT / "scripts" / "ci_d7_d9_emulator_hub.py"
CLIENT = ROOT / "frontend" / "integration_test" / "d7_d9_ubuntu_two_emulators_test.dart"


class EmulatorHubContractTest(unittest.TestCase):
    def test_dart_client_sends_exact_content_length_not_chunked(self):
        source = CLIENT.read_text(encoding="utf-8")
        self.assertIn("final payload = utf8.encode(jsonEncode(body));", source)
        self.assertIn("request.contentLength = payload.length;", source)
        self.assertIn("request.add(payload);", source)
        self.assertNotIn("request.write(jsonEncode(body));", source)

    def test_two_roles_share_one_bounded_test_only_hub(self):
        with tempfile.TemporaryDirectory() as directory:
            evidence = Path(directory) / "evidence.json"
            with socket.socket() as s:
                s.bind(("127.0.0.1", 0))
                port = s.getsockname()[1]
            process = subprocess.Popen(
                [sys.executable, str(HUB), "--port", str(port),
                 "--output", str(evidence)],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            base = f"http://127.0.0.1:{port}"
            try:
                for attempt in range(40):
                    if process.poll() is not None:
                        self.fail("Synthetic hub terminated during boot")
                    try:
                        with urlopen(f"{base}/health", timeout=1) as response:
                            self.assertEqual(json.loads(response.read())["hub"],
                                             "iamina-d7-d9-ubuntu-synthetic")
                        break
                    except (URLError, TimeoutError):
                        time.sleep(.05)
                else:
                    self.fail("Synthetic hub not listening on loopback")

                def post(body):
                    payload = json.dumps(body).encode()
                    request = Request(
                        f"{base}/attest", data=payload,
                        headers={"Content-Type": "application/json",
                                 "Content-Length": str(len(payload))},
                        method="POST",
                    )
                    return urlopen(request, timeout=2)

                roles = {
                    "device-one": "same-install-a-b-a-cold-restart",
                    "device-two": "fresh-install-no-remote-restore",
                }
                for role, scenario in roles.items():
                    with post({"role": role, "scenario": scenario,
                               "result": "pass"}) as response:
                        self.assertEqual(response.status, 200)
                        self.assertTrue(json.loads(response.read())["accepted"])
                attested = json.loads(evidence.read_text())
                self.assertEqual(attested["attestations"], roles)
                self.assertFalse(attested["physical_devices_tested"])
                self.assertFalse(attested["remote_profile_restored"])
                self.assertFalse(attested["clinical_egress_certified"])
                self.assertNotIn("medical", evidence.read_text().lower())
                with self.assertRaises(HTTPError) as duplicate:
                    post({"role": "device-one", "result": "pass",
                          "scenario": roles["device-one"]})
                self.assertEqual(duplicate.exception.code, 409)
                with self.assertRaises(HTTPError) as invalid:
                    post({"role": "device-three", "result": "pass",
                          "scenario": "fabricated"})
                self.assertEqual(invalid.exception.code, 400)
                self.assertEqual(json.loads(evidence.read_text())["attestations"],
                                 roles)
            finally:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=3)


if __name__ == "__main__":
    unittest.main()
