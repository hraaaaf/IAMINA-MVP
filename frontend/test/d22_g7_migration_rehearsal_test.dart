import 'package:amina/data/drift/database.dart';
import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:drift/drift.dart' as drift;
import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';

/// D22 G7 DESIGN REHEARSAL ONLY. Creates a sidecar table in a synthetic,
/// in-memory vault. Never changes AppDatabase.schemaVersion or real patients.
/// Existing legacy numbers remain stored exactly as observed with UNKNOWN
/// source unit and no verified personal-target authority.
void main() {
  Future<AppDatabase> dbFor(int scopedOwner) async {
    final db = AppDatabase.testPatientVault(
      NativeDatabase.memory(), PatientVaultScope.nativeDjango(scopedOwner),
    );
    await db.into(db.patientProfiles).insert(
      PatientProfilesCompanion.insert(
        userId: drift.Value(scopedOwner),
        preferredLanguage: const drift.Value('fr'),
        updatedAt: DateTime.utc(2026, 11, 1),
        unitPreference: const drift.Value('mmol/L'),
        targetRangeLow: const drift.Value(70.125),
        targetRangeHigh: const drift.Value(180.875),
      ),
    );
    return db;
  }

  Future<void> createCandidateSidecar(AppDatabase db) async {
    await db.customStatement('''
      CREATE TABLE d22_target_source_rehearsal (
        owner_id INTEGER NOT NULL PRIMARY KEY,
        legacy_low REAL NOT NULL,
        legacy_high REAL NOT NULL,
        low_source_unit TEXT,
        high_source_unit TEXT,
        authority_state TEXT NOT NULL DEFAULT 'unknown'
          CHECK (authority_state IN ('unknown', 'review_pending', 'approved')),
        provenance TEXT,
        CHECK (
          authority_state != 'approved'
          OR (
            low_source_unit IN ('mg/dL', 'mmol/L')
            AND high_source_unit IN ('mg/dL', 'mmol/L')
            AND provenance IS NOT NULL AND length(trim(provenance)) > 0
          )
        )
      )
    ''');
    await db.customStatement('''
      INSERT INTO d22_target_source_rehearsal
        (owner_id, legacy_low, legacy_high)
      SELECT user_id, target_range_low, target_range_high
      FROM patient_profiles
    ''');
  }

  test('G7 legacy values survive a scoped rehearsal without inventing units',
      () async {
    final db = await dbFor(734);
    addTearDown(db.close);
    final before = (await db.getProfileForLocalUserId(734))!;
    await db.transaction(() async => createCandidateSidecar(db));
    final sidecar = await db.customSelect(
      'SELECT * FROM d22_target_source_rehearsal WHERE owner_id = ?',
      variables: [const drift.Variable<int>(734)],
    ).getSingle();
    expect(sidecar.read<double>('legacy_low'), 70.125);
    expect(sidecar.read<double>('legacy_high'), 180.875);
    expect(sidecar.readNullable<String>('low_source_unit'), isNull);
    expect(sidecar.readNullable<String>('high_source_unit'), isNull);
    expect(sidecar.read<String>('authority_state'), 'unknown');
    expect(sidecar.readNullable<String>('provenance'), isNull);
    final after = (await db.getProfileForLocalUserId(734))!;
    expect(after.targetRangeLow, before.targetRangeLow);
    expect(after.targetRangeHigh, before.targetRangeHigh);
    expect(after.unitPreference, before.unitPreference);
  });

  test('G7 candidate schema cannot approve legacy without explicit unit data',
      () async {
    final db = await dbFor(734);
    addTearDown(db.close);
    await createCandidateSidecar(db);
    await expectLater(
      db.customStatement('''
        UPDATE d22_target_source_rehearsal
        SET authority_state = 'approved', provenance = 'untrusted-text'
        WHERE owner_id = 734
      '''),
      throwsA(isA<Exception>()),
    );
    final rows = await db.customSelect(
      'SELECT authority_state FROM d22_target_source_rehearsal',
    ).get();
    expect(rows.single.read<String>('authority_state'), 'unknown');
  });

  test('G7 transaction failure rolls back sidecar and keeps source profile',
      () async {
    final db = await dbFor(734);
    addTearDown(db.close);
    await expectLater(db.transaction(() async {
      await createCandidateSidecar(db);
      throw StateError('synthetic migration failure');
    }), throwsStateError);
    final names = await db.customSelect(
      "SELECT name FROM sqlite_master WHERE type = 'table' "
      "AND name = 'd22_target_source_rehearsal'",
    ).get();
    expect(names, isEmpty);
    final original = (await db.getProfileForLocalUserId(734))!;
    expect(original.targetRangeLow, 70.125);
    expect(original.targetRangeHigh, 180.875);
  });

  test('G7 two separately opened vaults do not share rehearsal provenance',
      () async {
    final a = await dbFor(734);
    final b = await dbFor(812);
    addTearDown(a.close);
    addTearDown(b.close);
    await createCandidateSidecar(a);
    await createCandidateSidecar(b);
    final countA = await a.customSelect(
      'SELECT COUNT(*) AS count FROM d22_target_source_rehearsal',
    ).getSingle();
    final countB = await b.customSelect(
      'SELECT COUNT(*) AS count FROM d22_target_source_rehearsal',
    ).getSingle();
    expect(countA.read<int>('count'), 1);
    expect(countB.read<int>('count'), 1);
    final bLeak = await b.customSelect(
      'SELECT * FROM d22_target_source_rehearsal WHERE owner_id = 734',
    ).get();
    expect(bLeak, isEmpty);
  });
}
