import 'package:amina/data/drift/database.dart';
import 'package:drift/drift.dart' as drift;
import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('D7 scoped local profile readers do not return another owner', () async {
    final db = AppDatabase(NativeDatabase.memory());
    addTearDown(db.close);

    await db.into(db.patientProfiles).insert(
      PatientProfilesCompanion.insert(
        userId: const drift.Value(734),
        preferredLanguage: const drift.Value('fr'),
        updatedAt: DateTime.utc(2026, 10, 13),
        diabetesType: const drift.Value('type1'),
        treatment: const drift.Value('insulin'),
      ),
    );
    await db.into(db.patientProfiles).insert(
      PatientProfilesCompanion.insert(
        userId: const drift.Value(812),
        preferredLanguage: const drift.Value('ar'),
        updatedAt: DateTime.utc(2026, 10, 13),
        diabetesType: const drift.Value('type2'),
        treatment: const drift.Value('tablets'),
      ),
    );

    final first = await db.getProfileForLocalUserId(734);
    final second = await db.getProfileForLocalUserId(812);
    expect(first?.userId, 734);
    expect(first?.diabetesType, 'type1');
    expect(second?.userId, 812);
    expect(second?.treatment, 'tablets');
    expect(await db.getProfileForLocalUserId(33), isNull);

    final watched = await db.watchProfileForLocalUserId(812).first;
    expect(watched?.userId, 812);
    expect(watched?.diabetesType, 'type2');

    await (db.update(db.patientProfiles)
          ..where((p) => p.userId.equals(812)))
        .write(const PatientProfilesCompanion(
          treatment: drift.Value('lifestyle'),
        ));
    expect((await db.getProfileForLocalUserId(734))?.treatment, 'insulin');
    expect((await db.getProfileForLocalUserId(812))?.treatment, 'lifestyle');
  });

  test('D7 scoped local profile APIs refuse invalid IDs', () async {
    final db = AppDatabase(NativeDatabase.memory());
    addTearDown(db.close);
    expect(() => db.watchProfileForLocalUserId(0), throwsArgumentError);
    expect(() => db.watchProfileForLocalUserId(-1), throwsArgumentError);
    expect(() => db.getProfileForLocalUserId(0), throwsArgumentError);
    expect(() => db.getProfileForLocalUserId(-4), throwsArgumentError);
  });
}
