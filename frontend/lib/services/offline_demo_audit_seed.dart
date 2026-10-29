import '../data/drift/database.dart';
import '../data/drift/patient_vault_scope.dart';

/// D11: the audit compile flag and loopback origin are NOT enough to seed a
/// patient vault. Seed only the dedicated synthetic audit database namespace.
/// A real/native/device-local vault must remain untouched even if a tester
/// enters the audit URL while an authenticated patient session exists.
bool canSeedOfflineDemoAuditVault({
  required bool auditAllowed,
  required bool offlineDemo,
  required PatientVaultScope? scope,
}) =>
    auditAllowed &&
    offlineDemo &&
    scope?.databaseName == PatientVaultScope.auditOnly().databaseName;

/// Synthetic fixture never runs on a real patient's physical Drift vault.
/// Direct callers cannot turn audit mode into clinical data contamination.
Future<void> seedOfflineDemoAuditData(
  AppDatabase db, {
  required bool auditAllowed,
  required bool offlineDemo,
}) async {
  if (!canSeedOfflineDemoAuditVault(
    auditAllowed: auditAllowed,
    offlineDemo: offlineDemo,
    scope: db.patientVaultScope,
  )) return;
  await db.seedDemoData();
}
