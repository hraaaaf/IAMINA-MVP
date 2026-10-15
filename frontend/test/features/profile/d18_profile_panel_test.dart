import 'package:amina/data/drift/database.dart';
import 'package:amina/data/drift/patient_progressive_demographics_store.dart';
import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:amina/data/drift/patient_weight_history_store.dart';
import 'package:amina/features/profile/d18_profile_panel.dart';
import 'package:drift/drift.dart' as drift;
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

Future<AppDatabase> _patientDb(int owner, {bool hasProfile = true}) async {
  final db = AppDatabase.testPatientVault(
    NativeDatabase.memory(), PatientVaultScope.nativeDjango(owner));
  if (hasProfile) {
    await db.into(db.patientProfiles).insert(
      PatientProfilesCompanion.insert(
        userId: drift.Value(owner),
        preferredLanguage: const drift.Value('fr'),
        updatedAt: DateTime.now().toUtc(),
      ),
    );
  }
  return db;
}

Future<void> _mount(WidgetTester tester, AppDatabase db) async {
  await tester.pumpWidget(MaterialApp(
    home: Scaffold(
      body: SingleChildScrollView(child: D18ProfilePanel(db: db)),
    ),
  ));
  await tester.pumpAndSettle();
  await tester.tap(find.byKey(const Key('d18-expand-profile')));
  await tester.pumpAndSettle();
}

Future<void> _tapVisible(WidgetTester tester, String key) async {
  final target = find.byKey(Key(key));
  await tester.ensureVisible(target);
  await tester.pumpAndSettle();
  await tester.tap(target);
  await tester.pumpAndSettle();
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('D18 initial empty, explicit edit and dated append are local',
      (tester) async {
    final db = await _patientDb(734);
    addTearDown(db.close);
    await _mount(tester, db);
    expect(find.text('No recorded readings.'), findsOneWidget);
    expect(await PatientProgressiveDemographicsStore(db).read(), isNull);
    expect(await PatientWeightHistoryStore(db).recent(), isEmpty);

    await tester.enterText(find.byKey(const Key('d18-birth-year')), '1994');
    await _tapVisible(tester, 'd18-save-demographics');
    expect((await PatientProgressiveDemographicsStore(db).read())?.birthYear,
        1994);

    await tester.enterText(find.byKey(const Key('d18-weight-value')), '72,50');
    await _tapVisible(tester, 'd18-save-weight');
    final readings = await PatientWeightHistoryStore(db).recent();
    expect(readings, hasLength(1));
    expect(readings.single.valueHundredths, 7250);
    expect(readings.single.unit, 'kg');
    expect(readings.single.provenance, 'patient_declared');
    expect(find.text('72.50 kg'), findsOneWidget);

    await tester.enterText(find.byKey(const Key('d18-weight-value')), '70');
    await _tapVisible(tester, 'd18-save-weight');
    final all = await PatientWeightHistoryStore(db).recent();
    expect(all, hasLength(2));
    expect(all.map((row) => row.valueHundredths), containsAll([7000, 7250]));
  });

  testWidgets('D18 invalid entry does not manufacture a profile or weight',
      (tester) async {
    final db = await _patientDb(812);
    addTearDown(db.close);
    await _mount(tester, db);
    await tester.enterText(find.byKey(const Key('d18-birth-year')), '1899');
    await _tapVisible(tester, 'd18-save-demographics');
    expect(await PatientProgressiveDemographicsStore(db).read(), isNull);
    await tester.enterText(find.byKey(const Key('d18-weight-value')), 'abc');
    await _tapVisible(tester, 'd18-save-weight');
    expect(await PatientWeightHistoryStore(db).recent(), isEmpty);
  });

  testWidgets('D18 no persisted patient profile refuses writes',
      (tester) async {
    final db = await _patientDb(913, hasProfile: false);
    addTearDown(db.close);
    await _mount(tester, db);
    await tester.enterText(find.byKey(const Key('d18-weight-value')), '70');
    await _tapVisible(tester, 'd18-save-weight');
    expect(await PatientWeightHistoryStore(db).recent(), isEmpty);
    expect(find.byKey(const Key('d18-local-status')), findsOneWidget);
  });
}
