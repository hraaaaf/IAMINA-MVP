"""W02/D10 Web guest source contract — NOT a browser/clinical certification."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
DB = (ROOT / 'frontend/lib/data/drift/database.dart').read_text(encoding='utf-8')
HOST = (ROOT / 'frontend/lib/services/patient_vault_app_host.dart').read_text(encoding='utf-8')
MAIN = (ROOT / 'frontend/lib/main.dart').read_text(encoding='utf-8')
WEB = (ROOT / 'frontend/lib/data/drift/guest_audit_executor_web.dart').read_text(encoding='utf-8')
NATIVE = (ROOT / 'frontend/lib/data/drift/guest_audit_executor_native.dart').read_text(encoding='utf-8')


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
        self.assertIn('guest_executor.openVolatileGuestWeb(sqlite3Wasm: sqlite3Wasm)', guest)
        self.assertIn('InMemoryFileSystem()', WEB)
        self.assertIn('sqlite.openInMemory()', WEB)
        self.assertIn('closeUnderlyingOnClose: true', WEB)
        self.assertNotIn('DriftWebOptions(', WEB)
        self.assertNotIn('IndexedDbFileSystem', WEB)

    def test_wasm_imports_never_reach_native_vm(self):
        self.assertIn('if (dart.library.js_interop)', DB)
        self.assertIn("'guest_audit_executor_native.dart'", DB)
        self.assertIn("'guest_audit_executor_web.dart'", DB)
        self.assertNotIn("import 'package:drift/wasm.dart'", DB)
        self.assertNotIn("import 'package:sqlite3/wasm.dart'", DB)
        self.assertNotIn("import 'package:drift/wasm.dart'", NATIVE)
        self.assertNotIn("import 'package:sqlite3/wasm.dart'", NATIVE)
        self.assertIn("import 'package:drift/wasm.dart'", WEB)
        self.assertIn("import 'package:sqlite3/wasm.dart'", WEB)

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
