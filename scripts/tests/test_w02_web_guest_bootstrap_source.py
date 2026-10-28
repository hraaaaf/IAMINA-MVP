"""W02/D10 Web guest source contract — NOT a browser/clinical certification."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
DB = (ROOT / 'frontend/lib/data/drift/database.dart').read_text(encoding='utf-8')
HOST = (ROOT / 'frontend/lib/services/patient_vault_app_host.dart').read_text(encoding='utf-8')
MAIN = (ROOT / 'frontend/lib/main.dart').read_text(encoding='utf-8')


class WebGuestBootstrapSourceContract(unittest.TestCase):
    def test_patient_vault_fails_closed_for_plaintext_web(self):
        self.assertRegex(DB, r'if \(kIsWeb\)\s*\{\s*throw StateError\('
                             r"'encrypted_web_patient_vault_unavailable'\)")
        self.assertIn('super(_w02ProtectedPatientVaultExecutor(scope))', DB)

    def test_guest_web_uses_only_volatile_wasm(self):
        guest = DB.split('QueryExecutor _w02GuestAuditExecutor(', 1)[1].split(
            '// ============================================================================', 1
        )[0]
        self.assertIn('if (!kIsWeb)', guest)
        self.assertIn('InMemoryFileSystem()', guest)
        self.assertIn('sqlite.openInMemory()', guest)
        self.assertIn('closeUnderlyingOnClose: true', guest)
        self.assertNotIn('DriftWebOptions(', guest)
        self.assertNotIn('IndexedDbFileSystem', guest)

    def test_host_uses_only_guest_constructor(self):
        self.assertIn('_guestDatabase = AppDatabase.guestAuditOnly()', HOST)
        self.assertNotIn('_guestDatabase = AppDatabase.forPatientVault(', HOST)

    def test_web_boot_does_not_open_legacy_plaintext(self):
        legacy = MAIN.split('// The historical mixed-owner DB', 1)[1].split(
            '// A missing app-lock credential', 1
        )[0]
        self.assertRegex(legacy, r'if \(!kIsWeb\)\s*\{\s*final legacy = AppDatabase.defaults\(\)')
        self.assertIn('bool legacyProtected = true', legacy)


if __name__ == '__main__':
    unittest.main()
