import 'package:amina/data/drift/database.dart';
import 'package:amina/features/profile/profile_owner_guard.dart';
import 'package:drift/drift.dart' as drift;
import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('existing real owner and new explicit owner are preserved', () {
    expect(resolveProfileRecordOwner(localUserIds: [734], authenticatedUserId: 734), 734);
    expect(resolveProfileRecordOwner(localUserIds: [734], authenticatedUserId: null), 734);
    expect(resolveProfileRecordOwner(localUserIds: [], authenticatedUserId: 812), 812);
    expect(resolveProfileRecordOwner(localUserIds: [], authenticatedUserId: null), 1);
  });

  test('ambiguity or foreign signed-in account fails closed', () {
    for (final ids in [[734, 1], [734, 812], [-1]]) {
      expect(() => resolveProfileRecordOwner(localUserIds: ids, authenticatedUserId: null), throwsStateError);
    }
    expect(() => resolveProfileRecordOwner(localUserIds: [734], authenticatedUserId: 812), throwsStateError);
    expect(() => resolveProfileRecordOwner(localUserIds: [], authenticatedUserId: 0), throwsStateError);
  });

  test('real Drift update retains patient ID and changes only intended values', () async {
    final db = AppDatabase(NativeDatabase.memory());
    addTearDown(db.close);
    await db.into(db.patientProfiles).insert(PatientProfilesCompanion.insert(
      userId: const drift.Value(734),
      preferredLanguage: const drift.Value('fr'),
      updatedAt: DateTime.utc(2026, 10, 12),
      diabetesType: const drift.Value('type1'),
      treatment: const drift.Value('insulin'),
      unitPreference: const drift.Value('mg/dL'),
    ));
    final original = await db.select(db.patientProfiles).get();
    final id = resolveProfileRecordOwner(
      localUserIds: original.map((p) => p.userId),
      authenticatedUserId: 734,
    );
    await db.into(db.patientProfiles).insertOnConflictUpdate(PatientProfilesCompanion.insert(
      userId: drift.Value(id),
      preferredLanguage: const drift.Value('fr'),
      updatedAt: DateTime.utc(2026, 10, 12, 1),
      diabetesType: const drift.Value('type2'),
      treatment: const drift.Value('tablets'),
      unitPreference: const drift.Value('mg/dL'),
    ));
    final rows = await db.select(db.patientProfiles).get();
    expect(rows, hasLength(1));
    expect(rows.single.userId, 734);
    expect(rows.single.diabetesType, 'type2');
    expect(rows.single.treatment, 'tablets');
    expect(rows.single.unitPreference, 'mg/dL');
  });
}
