"""D10↔D11 integrated SOURCE tripwires; run with real Flutter/Django tests.

This cannot certify real device owner isolation, encryption or external consent.
"""
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]

def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")

class D10D11IntegratedSourceContract(unittest.TestCase):
    def test_d11_patient_demo_seed_denied_without_data_writes(self):
        demo = read("backend/diabetes/api/v1/demo.py")
        method = demo.split("def seed_demo_data(request):", 1)
        self.assertEqual(len(method), 2, "D11 HTTP route is missing")
        body = method[1].split("\n@", 1)[0]
        self.assertIn('raise HttpError(403,', body)
        self.assertNotIn("LogEntry.objects.create", body)
        self.assertNotIn("bulk_create", body)

    def test_d11_audit_only_vault_direct_and_indirect_seed_guards(self):
        helper = read("frontend/lib/services/offline_demo_audit_seed.dart")
        db = read("frontend/lib/data/drift/database.dart")
        self.assertIn("PatientVaultScope.auditOnly().databaseName", helper)
        self.assertIn("scope?.databaseName ==", helper)
        self.assertIn("patientVaultScope != null", db.split("Future<void> seedDemoData() async", 1)[1])
        self.assertIn("Demo seeding forbidden inside a patient vault", db)

    def test_d10_lock_and_clinical_transport_cannot_be_conflated(self):
        host = read("frontend/lib/services/patient_vault_app_host.dart")
        transport = read("frontend/lib/services/api_client.dart")
        self.assertIn("appLock.isUnlocked", host)
        self.assertIn("bool get canSyncClinicalData", transport)
        self.assertIn("AuthEpoch", transport)
        self.assertNotIn("appLock.isUnlocked = true", host)

    def test_android_and_ios_backup_guards_from_main_preserved(self):
        manifest = ET.fromstring(read("frontend/android/app/src/main/AndroidManifest.xml"))
        android_uri = "{http://schemas.android.com/apk/res/android}"
        self.assertEqual(manifest.find("application").get(android_uri + "allowBackup"), "false")
        scene = read("frontend/ios/Runner/SceneDelegate.swift")
        self.assertIn("ClinicalVaultBackupExclusion.applyToDocumentsDirectory()", scene)
        self.assertIn("sceneDidEnterBackground", scene)
        app = read("frontend/ios/Runner/AppDelegate.swift")
        self.assertIn("isExcludedFromBackup = true", app)

    def test_d11_browser_review_bootstrap_stays_scoped(self):
        source = read("frontend/web/flutter_bootstrap.js")
        self.assertIn("async function startHostedReview()", source)
        self.assertIn("await cleanupHostedReviewCaches();", source)

if __name__ == "__main__":
    unittest.main()
