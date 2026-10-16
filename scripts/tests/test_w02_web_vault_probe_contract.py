"""Static/no-network W02 synthetic browser harness guardrails."""
from __future__ import annotations

import sys
import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from w02_web_local_vault_browser_probe import ORIGIN, PHASES  # noqa: E402


class W02SyntheticProbeContractTests(unittest.TestCase):
    def test_script_locks_to_loopback(self) -> None:
        self.assertEqual(ORIGIN, "http://127.0.0.1:7368")

    def test_exact_account_scope_sequence(self) -> None:
        self.assertEqual(PHASES, ("seed_a", "seed_b", "verify_a", "verify_b"))

    def test_both_fixture_scopes_are_real_distinct_uuid_v4(self) -> None:
        content = (
            ROOT / "frontend/lib/ui_w02_synthetic_vault_scope_probe_main.dart"
        ).read_text(encoding="utf-8")
        a, b = (
            "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
            "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
        )
        self.assertNotEqual(a, b)
        self.assertEqual(uuid.UUID(a).version, 4)
        self.assertEqual(uuid.UUID(b).version, 4)
        self.assertIn(a, content)
        self.assertIn(b, content)

    def test_dart_uses_real_scoped_vault_not_legacy_default(self) -> None:
        content = (
            ROOT / "frontend/lib/ui_w02_synthetic_vault_scope_probe_main.dart"
        ).read_text(encoding="utf-8")
        self.assertIn("AppDatabase.forPatientVault(scope)", content)
        self.assertNotIn("AppDatabase.defaults()", content)

    def test_fixture_never_contains_external_cloud_credentials(self) -> None:
        content = (
            ROOT / "frontend/lib/ui_w02_synthetic_vault_scope_probe_main.dart"
        ).read_text(encoding="utf-8")
        self.assertNotIn("DATABASE_URL", content)
        self.assertNotIn("iamina-certified.vercel.app", content)
        self.assertNotIn("https://", content)


if __name__ == "__main__":
    unittest.main()
