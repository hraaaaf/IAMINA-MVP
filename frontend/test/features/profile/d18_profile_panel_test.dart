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

Future<void> _confirmMeasuredAt(WidgetTester tester) async {
  await _tapVisible(tester, 'd18-measured-at');
  await tester.tap(find.text('OK').last);
  await tester.pumpAndSettle();
  await tester.tap(find.text('OK').last);
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
    await tester.pump(); // onChanged setState must rebuild the button.
    expect(tester.widget<TextButton>(find.byKey(const Key('d18-refresh')))
        .onPressed, isNull);
    await _tapVisible(tester, 'd18-save-demographics');
    expect((await PatientProgressiveDemographicsStore(db).read())?.birthYear,
        1994);

    await tester.enterText(find.byKey(const Key('d18-weight-value')), '72,50');
    // Patient must explicitly confirm date and time; never manufacture it.
    expect(tester.widget<FilledButton>(find.byKey(const Key('d18-save-weight')))
        .onPressed, isNull);
    await _confirmMeasuredAt(tester);
    await _tapVisible(tester, 'd18-save-weight');
    final readings = await PatientWeightHistoryStore(db).recent();
    expect(readings, hasLength(1));
    expect(readings.single.valueHundredths, 7250);
    expect(readings.single.unit, 'kg');
    expect(readings.single.provenance, 'patient_declared');
    expect(find.text('72.50 kg'), findsOneWidget);
    expect(find.textContaining('Patient-entered'), findsOneWidget);

    await tester.enterText(find.byKey(const Key('d18-weight-value')), '70');
    await _confirmMeasuredAt(tester);
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
    await _confirmMeasuredAt(tester);
    await _tapVisible(tester, 'd18-save-weight');
    expect(await PatientWeightHistoryStore(db).recent(), isEmpty);
  });

  testWidgets('D18 year edit preserves newer gender declaration',
      (tester) async {
    final db = await _patientDb(734);
    addTearDown(db.close);
    final store = PatientProgressiveDemographicsStore(db);
    await store.update(
      updateBirthYear: true, birthYear: 1988,
      updateGenderIdentity: true, genderIdentity: 'woman',
    );
    await _mount(tester, db);
    // Another local writer changes one field after the widget read.
    // Saving the edited birth year must not replace its newer gender.
    await store.update(
      updateGenderIdentity: true, genderIdentity: 'non_binary',
    );
    await tester.enterText(find.byKey(const Key('d18-birth-year')), '1994');
    await _tapVisible(tester, 'd18-save-demographics');
    final updated = await store.read();
    expect(updated?.birthYear, 1994);
    expect(updated?.genderIdentity, 'non_binary');
  });

  testWidgets('D18 optional fields can be cleared without touching clinical targets',
      (tester) async {
    final db = await _patientDb(734);
    addTearDown(db.close);
    final store = PatientProgressiveDemographicsStore(db);
    await store.update(
      updateBirthYear: true, birthYear: 1994,
      updateGenderIdentity: true, genderIdentity: 'woman',
    );
    final before = await db.getProfileForLocalUserId(db.activeProfileRowId);
    await _mount(tester, db);
    expect(tester.widget<TextField>(find.byKey(const Key('d18-birth-year')))
        .controller?.text, '1994');
    await tester.enterText(find.byKey(const Key('d18-birth-year')), '');
    await tester.pump();
    // Choose the explicit "not provided" option: no gender is inferred.
    final identity = tester.widget<DropdownButton<String?>>(
      find.byKey(const Key('d18-gender-identity')));
    identity.onChanged?.call(null);
    await tester.pump();
    await _tapVisible(tester, 'd18-save-demographics');

    final cleared = await store.read();
    expect(cleared?.birthYear, isNull);
    expect(cleared?.genderIdentity, isNull);
    final after = await db.getProfileForLocalUserId(db.activeProfileRowId);
    // D18 declaration changes must not alter clinical configuration.
    expect(after?.diabetesType, before?.diabetesType);
    expect(after?.treatment, before?.treatment);
    expect(after?.targetRangeLow, before?.targetRangeLow);
    expect(after?.targetRangeHigh, before?.targetRangeHigh);
    expect(after?.unitPreference, before?.unitPreference);
  });

  testWidgets('D18 same widget switches A to B to A without stale identity',
      (tester) async {
    final a = await _patientDb(734);
    final b = await _patientDb(812);
    addTearDown(a.close);
    addTearDown(b.close);
    await PatientProgressiveDemographicsStore(a).update(
      updateBirthYear: true, birthYear: 1994,
    );
    await PatientProgressiveDemographicsStore(b).update(
      updateBirthYear: true, birthYear: 2001,
    );

    Future<void> showVault(AppDatabase db) async {
      await tester.pumpWidget(MaterialApp(
        home: Scaffold(body: SingleChildScrollView(
          child: D18ProfilePanel(db: db),
        )),
      ));
      await tester.pumpAndSettle();
    }

    await showVault(a);
    await tester.tap(find.byKey(const Key('d18-expand-profile')));
    await tester.pumpAndSettle();
    expect(tester.widget<TextField>(find.byKey(const Key('d18-birth-year')))
        .controller?.text, '1994');
    await showVault(b);
    expect(tester.widget<TextField>(find.byKey(const Key('d18-birth-year')))
        .controller?.text, '2001');
    await showVault(a);
    expect(tester.widget<TextField>(find.byKey(const Key('d18-birth-year')))
        .controller?.text, '1994');
  });

  for (final size in <Size>[
    const Size(360, 560),
    const Size(390, 844),
    const Size(768, 1024),
    const Size(1280, 900),
  ]) {
    testWidgets('D18 optional form remains usable at $size', (tester) async {
      tester.view.devicePixelRatio = 1;
      tester.view.physicalSize = size;
      addTearDown(() {
        tester.view.resetDevicePixelRatio();
        tester.view.resetPhysicalSize();
      });
      final db = await _patientDb(734);
      addTearDown(db.close);
      await _mount(tester, db);

      expect(find.byKey(const Key('d18-birth-year')), findsOneWidget);
      expect(find.byKey(const Key('d18-gender-identity')), findsOneWidget);
      await tester.ensureVisible(find.byKey(const Key('d18-save-weight')));
      await tester.pumpAndSettle();
      expect(find.byKey(const Key('d18-save-weight')), findsOneWidget);
      expect(tester.takeException(), isNull);
    });
  }

  testWidgets('D18 no persisted patient profile refuses writes',
      (tester) async {
    final db = await _patientDb(913, hasProfile: false);
    addTearDown(db.close);
    await _mount(tester, db);
    await tester.enterText(find.byKey(const Key('d18-weight-value')), '70');
    await _confirmMeasuredAt(tester);
    await _tapVisible(tester, 'd18-save-weight');
    expect(await PatientWeightHistoryStore(db).recent(), isEmpty);
    expect(find.byKey(const Key('d18-local-status')), findsOneWidget);
  });
}
