import '../data/drift/database.dart';

/// Seeds deterministic local demo data only for the explicit, loopback-gated
/// offline audit path. Production runtime does not call this unless both gates
/// are already satisfied by the caller.
Future<void> seedOfflineDemoAuditData(
  AppDatabase db, {
  required bool auditAllowed,
  required bool offlineDemo,
}) async {
  if (!auditAllowed || !offlineDemo) return;
  await db.seedDemoData();
}
