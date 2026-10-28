"""D9 source guard only: not a claim of real-browser first-user certification."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
read = lambda p: (ROOT / p).read_text(encoding="utf8")


class D9W02CompatibilityContract(unittest.TestCase):
    def test_migration_order_does_not_collide_with_w01_or_w02(self):
        d9 = read("backend/core/migrations/0025_d9_first_use_completed_at.py")
        self.assertIn('("core", "0024_w02_vault_revision_anchor")', d9)
        self.assertIn('name="first_use_completed_at"', d9)
        self.assertNotIn('("core", "0019_auth_abuse_bucket")', d9)
        self.assertTrue((ROOT / "backend/core/migrations/0024_w02_vault_revision_anchor.py").exists())
        self.assertFalse((ROOT / "backend/core/migrations/0020_d9_first_use_completed_at.py").exists())

    def test_web_clinical_vault_still_fails_closed(self):
        db = read("frontend/lib/data/drift/database.dart")
        host = read("frontend/lib/services/patient_vault_app_host.dart")
        self.assertIn("encrypted_web_patient_vault_unavailable", db)
        self.assertIn("AppDatabase.guestAuditOnly()", host)
        self.assertIn("_D9FirstUseGate.unavailable", host)

    def test_first_use_never_auto_grants_clinical_profile_or_ai(self):
        consent = read("frontend/lib/features/auth/consent_screen.dart")
        transport = read("frontend/lib/services/d9_first_use_transport.dart")
        api = read("backend/diabetes/api/v1/profile.py")
        self.assertIn("getProfileForLocalUserId(db.activeProfileRowId) == null", consent)
        self.assertIn("request.user", api)
        self.assertIn('"/profile/first-use"', api)
        self.assertIn("expectedOwner", transport)
        self.assertIn("D9FirstUseCompletionCommand", api)

    def test_targeted_tests_present(self):
        for p in (
            "backend/diabetes/tests/test_d9_explicit_first_use_proof.py",
            "frontend/test/services/d9_first_use_transport_test.dart",
            "frontend/test/services/d9_vault_first_use_integration_test.dart",
            "frontend/test/d9_first_use_vault_wiring_contract_test.dart",
        ):
            self.assertTrue((ROOT / p).exists(), p)

if __name__ == "__main__":
    unittest.main()
