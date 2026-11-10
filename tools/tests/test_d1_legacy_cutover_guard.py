"""Synthetic contract tests for the D1 legacy no-cutover static guard."""
from pathlib import Path
import tempfile
import unittest

from tools.d1_legacy_cutover_guard import check, reachable_sources


class D1LegacyNoCutoverContract(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.lib = self.root / "frontend" / "lib"
        self._put("data/drift/database.dart", """
class AppDatabase {
  AppDatabase.defaults() : super(driftDatabase(name: 'amina'));
  AppDatabase.forPatientVault(PatientVaultScope scope)
      : super(driftDatabase(name: scope.databaseName));
}
""")
        self._put("data/drift/patient_vault_scope.dart",
                  "'amina_vault_v1_native_' 'amina_vault_v1_device_' 'amina_vault_v1_audit'")
        self._put("main.dart", "import 'services/patient_vault_app_host.dart';")
        self._put("services/patient_vault_app_host.dart",
                  "import '../data/drift/database.dart';")
        self._put("services/patient_vault_session_controller.dart",
                  "import '../data/drift/database.dart';")

    def _put(self, path, body):
        p = self.lib / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")

    def test_stable_scopes_are_accepted(self):
        self.assertEqual(check(self.root), [])

    def test_transitive_experimental_cutover_is_rejected(self):
        self._put("services/patient_vault_app_host.dart",
                  "import '../data/drift/bridge.dart';")
        self._put("data/drift/bridge.dart", "export 'd18_old_cutover.dart';")
        self._put("data/drift/d18_old_cutover.dart", "void dangerous() {}")
        self.assertTrue(any("d18_old_cutover" in e for e in check(self.root)))

    def test_destructive_entrypoint_is_rejected(self):
        p = self.lib / "data/drift/database.dart"
        p.write_text(p.read_text() + "\nvoid bad() { deleteDatabase('amina'); }\n")
        self.assertTrue(any("destructive" in e for e in check(self.root)))

    def test_legacy_name_replacement_is_rejected(self):
        p = self.lib / "data/drift/database.dart"
        p.write_text(p.read_text().replace("name: 'amina'", "name: 'amina_v2'"))
        self.assertTrue(any("boundary changed" in e for e in check(self.root)))

    def test_missing_source_fails_closed(self):
        (self.lib / "services/patient_vault_app_host.dart").unlink()
        self.assertTrue(any("missing source" in e for e in check(self.root)))

    def test_unrelated_sdk_package_import_ignored(self):
        self._put("main.dart", "import 'package:flutter/material.dart';\n"
                  "import 'services/patient_vault_app_host.dart';")
        self.assertEqual(check(self.root), [])


if __name__ == "__main__":
    unittest.main()
