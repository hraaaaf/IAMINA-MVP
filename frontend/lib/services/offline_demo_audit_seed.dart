import '../data/drift/database.dart';
import '../data/drift/patient_vault_scope.dart';

/// Seeds deterministic local demo data only for the explicit, loopback-gated
/// offline audit path. Production runtime does not call this unless both gates
/// are already satisfied by the caller.
Future<void> seedOfflineDemoAuditData(
  AppDatabase db, {
  required bool auditAllowed,
  required bool offlineDemo,
}) async {
  if (!auditAllowed || !offlineDemo) return;
  // D11: user-owned, device-local and legacy vaults never receive demo data.
  if (db.patientVaultScope?.databaseName !=
      PatientVaultScope.auditOnly().databaseName) {
    return;
  }
  await db.seedDemoData();
}
