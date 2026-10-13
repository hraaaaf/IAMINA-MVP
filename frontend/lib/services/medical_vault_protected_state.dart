import '../data/drift/database.dart';

/// Only a presence check for app-lock rollback detection. Never extracts or
/// migrates clinical rows from the historical database or another owner.
Future<bool> hasProtectedMedicalVaultRows(AppDatabase db) async {
  if (await (db.select(db.patientProfiles)..limit(1)).getSingleOrNull() != null) {
    return true;
  }
  if (await (db.select(db.logEntries)..limit(1)).getSingleOrNull() != null) {
    return true;
  }
  if (await (db.select(db.chatMessages)..limit(1)).getSingleOrNull() != null) {
    return true;
  }
  if (await (db.select(db.medicationEvents)..limit(1)).getSingleOrNull() != null) {
    return true;
  }
  if (await (db.select(db.reminders)..limit(1)).getSingleOrNull() != null) {
    return true;
  }
  // D7 multi-treatment declarations use an additive hand-managed table.
  final declarations = await db.customSelect(
    'SELECT 1 FROM patient_treatment_declarations_v1 LIMIT 1',
  ).get();
  return declarations.isNotEmpty;
}
