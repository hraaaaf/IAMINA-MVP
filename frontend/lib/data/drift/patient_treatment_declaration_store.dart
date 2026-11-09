import 'dart:convert';

import 'package:drift/drift.dart';

import 'database.dart';

const patientTreatmentDeclarationCodesV1 = {
  'insulin', 'oral_meds', 'lifestyle', 'other',
};
const patientTreatmentDeclarationStatesV1 = {
  'not_answered', 'unsure', 'declared', 'none_declared',
};

/// Patient-reported choices; not medication orders, diagnosis or clinical rules.
final class PatientTreatmentDeclarationRecord {
  final int ownerId;
  final String state;
  final List<String> codes;
  final int version;
  final String provenance;
  final DateTime updatedAtUtc;
  final String syncStatus;
  final DateTime? baseServerUpdatedAtUtc;
  final int localGeneration;

  PatientTreatmentDeclarationRecord({
    required this.ownerId,
    required this.state,
    required List<String> codes,
    required this.version,
    required this.provenance,
    required this.updatedAtUtc,
    required this.syncStatus,
    required this.baseServerUpdatedAtUtc,
    required this.localGeneration,
  }) : codes = List.unmodifiable(codes);
}

void validatePatientTreatmentDeclarationV1({
  required String state,
  required List<String> codes,
}) {
  if (!patientTreatmentDeclarationStatesV1.contains(state)) {
    throw ArgumentError.value(state, 'state', 'Unsupported declaration state');
  }
  if (codes.toSet().length != codes.length ||
      codes.any((code) => !patientTreatmentDeclarationCodesV1.contains(code))) {
    throw ArgumentError.value(codes, 'codes', 'Invalid or duplicated code');
  }
  if ((state == 'declared') != codes.isNotEmpty) {
    throw ArgumentError('State and treatment codes disagree');
  }
}

/// This store accepts only an already selected, physically isolated vault.
/// Native owner IDs originate from AuthService + Django, never a UI form.
/// Legacy scalar treatment data is deliberately NOT migrated automatically.
final class PatientTreatmentDeclarationStore {
  final AppDatabase db;

  PatientTreatmentDeclarationStore(this.db) {
    if (db.patientVaultScope == null) {
      throw StateError('A verified patient vault is required');
    }
  }

  int get _ownerId => db.activeProfileRowId;

  Future<PatientTreatmentDeclarationRecord?> read() async {
    final rows = await db.customSelect(
      '''SELECT user_id, declaration_state, codes_json,
         declaration_version, provenance, updated_at_utc,
         sync_status, base_server_updated_at, local_generation
         FROM patient_treatment_declarations_v1 WHERE user_id = ?''',
      variables: [Variable<int>(_ownerId)],
    ).get();
    if (rows.isEmpty) return null;
    if (rows.length != 1) {
      throw StateError('Ambiguous patient treatment declarations');
    }
    final data = rows.single.data;
    final rawCodes = jsonDecode(data['codes_json'] as String);
    if (rawCodes is! List || rawCodes.any((item) => item is! String)) {
      throw StateError('Invalid stored patient declaration');
    }
    final codes = rawCodes.cast<String>().toList(growable: false);
    final state = data['declaration_state'] as String;
    validatePatientTreatmentDeclarationV1(state: state, codes: codes);
    if (data['declaration_version'] != 1 ||
        data['provenance'] != 'patient_declared') {
      throw StateError('Unrecognized declaration provenance or version');
    }
    return PatientTreatmentDeclarationRecord(
      ownerId: data['user_id'] as int,
      state: state,
      codes: codes,
      version: 1,
      provenance: data['provenance'] as String,
      updatedAtUtc: DateTime.parse(data['updated_at_utc'] as String).toUtc(),
      syncStatus: data['sync_status'] as String,
      baseServerUpdatedAtUtc: (data['base_server_updated_at'] as String?) == null
          ? null
          : DateTime.parse(data['base_server_updated_at'] as String).toUtc(),
      localGeneration: data['local_generation'] as int,
    );
  }

  /// Restore an explicit server declaration only if the patient's isolated
  /// native Django vault has no declaration. A late GET never overwrites
  /// a local offline edit, and no legacy scalar is inferred.
  Future<bool> restoreRemoteIfAbsent({
    required String state,
    required List<String> codes,
    required DateTime updatedAtUtc,
  }) async {
    if (db.patientVaultScope?.nativeDjangoUserId == null) {
      throw StateError('Remote declaration requires native Django vault');
    }
    validatePatientTreatmentDeclarationV1(state: state, codes: codes);
    final owner = _ownerId;
    return db.transaction(() async {
      if (await db.getProfileForLocalUserId(owner) == null) {
        throw StateError('No patient-owned profile for remote declaration');
      }
      final existing = await db.customSelect(
        'SELECT 1 FROM patient_treatment_declarations_v1 WHERE user_id = ?',
        variables: [Variable<int>(owner)],
      ).get();
      if (existing.isNotEmpty) return false;
      await db.customStatement('''
        INSERT INTO patient_treatment_declarations_v1
          (user_id, declaration_state, codes_json, declaration_version,
           provenance, updated_at_utc, sync_status,
           base_server_updated_at, local_generation)
        VALUES (?, ?, ?, 1, 'patient_declared', ?, 'confirmed', ?, 1)
        ON CONFLICT(user_id) DO NOTHING
      ''', [
        owner, state, jsonEncode(codes), updatedAtUtc.toUtc().toIso8601String(),
        updatedAtUtc.toUtc().toIso8601String(),
      ]);
      return true;
    });
  }

  /// Acknowledge only the generation sent to the server. A local edit racing
  /// a response remains pending, never falsely confirmed or overwritten.
  Future<bool> acknowledgeIfUnchanged({
    required int expectedGeneration,
    required DateTime serverUpdatedAtUtc,
  }) async {
    final updated = await db.customUpdate('''
      UPDATE patient_treatment_declarations_v1 SET
        sync_status = 'confirmed',
        base_server_updated_at = ?
      WHERE user_id = ? AND local_generation = ?
        AND sync_status = 'pending'
    ''', variables: [
      Variable<String>(serverUpdatedAtUtc.toUtc().toIso8601String()),
      Variable<int>(_ownerId),
      Variable<int>(expectedGeneration),
    ]);
    return updated == 1;
  }

  /// The server accepted an earlier local generation while a new patient
  /// edit was made in flight. Advance only its CAS baseline: the new choice
  /// stays pending, untouched, and can be retried against the fresh revision.
  /// A different baseline or an existing conflict must never be rebased.
  Future<bool> rebasePendingAfterStaleAck({
    required int acknowledgedGeneration,
    required DateTime? sentBaseUpdatedAtUtc,
    required DateTime serverUpdatedAtUtc,
  }) async {
    final changed = await db.customUpdate('''
      UPDATE patient_treatment_declarations_v1
      SET base_server_updated_at = ?
      WHERE user_id = ?
        AND local_generation > ?
        AND sync_status = 'pending'
        AND base_server_updated_at IS ?
    ''', variables: [
      Variable<String>(serverUpdatedAtUtc.toUtc().toIso8601String()),
      Variable<int>(_ownerId),
      Variable<int>(acknowledgedGeneration),
      Variable<String>(sentBaseUpdatedAtUtc?.toUtc().toIso8601String()),
    ]);
    return changed == 1;
  }

  /// A 409 never discards the patient's local declaration. It stays blocked
  /// for explicit reconciliation rather than being silently retried.
  Future<bool> markConflictIfUnchanged(int expectedGeneration) async {
    final updated = await db.customUpdate('''
      UPDATE patient_treatment_declarations_v1
      SET sync_status = 'conflict'
      WHERE user_id = ? AND local_generation = ?
        AND sync_status = 'pending'
    ''', variables: [
      Variable<int>(_ownerId),
      Variable<int>(expectedGeneration),
    ]);
    return updated == 1;
  }

  /// Only a patient-initiated, reviewed choice may resolve a 409.
  /// The latest owner-scoped remote CAS revision is supplied by a verified GET.
  /// The local statement itself is never rewritten here.
  Future<bool> retryConflictAfterExplicitReview({
    required int expectedGeneration,
    required DateTime currentServerRevisionUtc,
  }) async {
    final updated = await db.customUpdate('''
      UPDATE patient_treatment_declarations_v1
      SET sync_status = 'pending',
          base_server_updated_at = ?,
          local_generation = local_generation + 1
      WHERE user_id = ? AND local_generation = ?
        AND sync_status = 'conflict'
    ''', variables: [
      Variable<String>(currentServerRevisionUtc.toUtc().toIso8601String()),
      Variable<int>(_ownerId),
      Variable<int>(expectedGeneration),
    ]);
    return updated == 1;
  }

  Future<void> write({
    required String state,
    required List<String> codes,
  }) async {
    validatePatientTreatmentDeclarationV1(state: state, codes: codes);
    final owner = _ownerId;
    await db.transaction(() async {
      final profile = await db.getProfileForLocalUserId(owner);
      if (profile == null) {
        throw StateError('Cannot attach declarations without owned profile');
      }
      await db.customStatement('''
        INSERT INTO patient_treatment_declarations_v1
          (user_id, declaration_state, codes_json, declaration_version,
           provenance, updated_at_utc)
        VALUES (?, ?, ?, 1, 'patient_declared', ?)
        ON CONFLICT(user_id) DO UPDATE SET
          declaration_state = excluded.declaration_state,
          codes_json = excluded.codes_json,
          declaration_version = excluded.declaration_version,
          provenance = excluded.provenance,
          updated_at_utc = excluded.updated_at_utc,
          sync_status = CASE
            WHEN patient_treatment_declarations_v1.sync_status = 'conflict'
            THEN 'conflict' ELSE 'pending' END,
          local_generation =
            patient_treatment_declarations_v1.local_generation + 1
      ''', [
        owner, state, jsonEncode(codes), DateTime.now().toUtc().toIso8601String(),
      ]);
    });
  }
}
