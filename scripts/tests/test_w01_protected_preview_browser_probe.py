"""W01 protected Preview probe: false-green denial and target safety tests."""
from __future__ import annotations

import unittest

from scripts.w01_protected_preview_browser_probe import (
    API_HEALTH_URL,
    FRONT_URL,
    _js_case,
    deny_is_proven,
    health_is_success,
)


class W01ProtectedPreviewProbeContract(unittest.TestCase):
    def test_exact_synthetic_targets_not_stable_or_production(self):
        self.assertIn("iamina-review-goowsfx8j-", FRONT_URL)
        self.assertIn("iamina-certified-n3g9na2ou-", API_HEALTH_URL)
        self.assertEqual(API_HEALTH_URL.count("/api/v1/health"), 1)
        self.assertNotIn("iamina-certified.vercel.app/", API_HEALTH_URL)

    def test_browser_request_has_no_bypass_or_patient_data(self):
        for name in ("no_cookies", "with_cookies", "preflight_with_cookies"):
            expression = _js_case(name)
            self.assertIn("/api/v1/health", expression)
            self.assertNotIn("x-vercel-protection-bypass", expression.lower())
            self.assertNotIn("Authorization", expression)
            self.assertNotIn("POST", expression)
        self.assertIn("X-Iamina-W01-Synthetic-Probe", _js_case("preflight_with_cookies"))

    def test_only_json_health_success_counts(self):
        self.assertTrue(health_is_success({
            "kind": "http", "http_status": 200, "json": True,
            "status": "ok", "db": "ok",
        }))
        self.assertFalse(health_is_success({
            "kind": "http", "http_status": 200, "json": False,
            "status": "ok", "db": "ok",
        }))
        self.assertFalse(health_is_success({"kind": "fetch_error", "error_type": "TypeError"}))

    def test_rejects_silent_false_green(self):
        cases = [
            {"case": "no_cookies", "kind": "fetch_error"},
            {"case": "with_cookies", "kind": "fetch_error"},
            {"case": "preflight_with_cookies", "kind": "fetch_error"},
        ]
        self.assertFalse(deny_is_proven(cases, []))
        self.assertTrue(deny_is_proven(cases, [
            {"method": "GET"}, {"method": "GET"}, {"method": "OPTIONS"},
        ]))
        cases[1] = {
            "case": "with_cookies", "kind": "http", "http_status": 200,
            "json": True, "status": "ok", "db": "ok",
        }
        self.assertFalse(deny_is_proven(cases, [
            {"method": "GET"}, {"method": "GET"}, {"method": "OPTIONS"},
        ]))


if __name__ == "__main__":
    unittest.main()
