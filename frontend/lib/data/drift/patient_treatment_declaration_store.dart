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

  PatientTreatmentDeclarationRecord({
    required this.ownerId,
    required this.state,
    required List<String> codes,
    required this.version,
    required this.provenance,
    required this.updatedAtUtc,
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
         declaration_version, provenance, updated_at_utc
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
           provenance, updated_at_utc)
        VALUES (?, ?, ?, 1, 'patient_declared', ?)
        ON CONFLICT(user_id) DO NOTHING
      ''', [
        owner, state, jsonEncode(codes), updatedAtUtc.toUtc().toIso8601String(),
      ]);
      return true;
    });
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
          updated_at_utc = excluded.updated_at_utc
      ''', [
        owner, state, jsonEncode(codes), DateTime.now().toUtc().toIso8601String(),
      ]);
    });
  }
}
