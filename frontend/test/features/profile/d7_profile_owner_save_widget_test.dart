import 'package:amina/data/drift/database.dart';
import 'package:amina/data/drift/patient_treatment_declaration_store.dart';
import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:amina/features/profile/profile_screen.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:amina/services/api_client.dart';
import 'package:amina/services/app_lock_service.dart';
import 'package:amina/services/auth_service.dart';
import 'package:amina/services/consent_service.dart';
import 'package:drift/drift.dart' as drift;
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

// D7: Synthetic fixture only. No clinical target authority, production data,
// remote authorization, or real-browser persistence is asserted by this test.
void main() {
  testWidgets('D7 Profile save changes only the active owner, never '
      'silently rewrites reported treatment, and survives reopening',
      (tester) async {
    final db = AppDatabase.testPatientVault(
      NativeDatabase.memory(), PatientVaultScope.nativeDjango(734),
    );
    addTearDown(db.close);
    await db.into(db.patientProfiles).insert(
      PatientProfilesCompanion.insert(
        userId: const drift.Value(734),
        preferredLanguage: const drift.Value('fr'),
        updatedAt: DateTime.utc(2026, 10, 29),
        diabetesType: const drift.Value('type2'),
        treatment: const drift.Value('tablets'),
        unitPreference: const drift.Value('mg/dL'),
        targetRangeLow: const drift.Value(84.125),
        targetRangeHigh: const drift.Value(168.75),
      ),
    );
    // Adversarial legacy row: a scoped write must not modify another ID,
    // even when the fixture contains an extraneous profile.
    await db.into(db.patientProfiles).insert(
      PatientProfilesCompanion.insert(
        userId: const drift.Value(812),
        preferredLanguage: const drift.Value('ar'),
        updatedAt: DateTime.utc(2026, 10, 29),
        diabetesType: const drift.Value('type1'),
        treatment: const drift.Value('insulin'),
        unitPreference: const drift.Value('mg/dL'),
        targetRangeLow: const drift.Value(85),
        targetRangeHigh: const drift.Value(165),
      ),
    );

    final store = PatientTreatmentDeclarationStore(db);
    await store.write(state: 'declared', codes: ['insulin', 'oral_meds']);
    final before = (await store.read())!;
    final otherBefore = await db.getProfileForLocalUserId(812);

    final auth = AuthService();
    addTearDown(auth.dispose);
    final consent = ConsentService()
      ..seedInitialProfile((await db.getProfileForLocalUserId(734))!);
    addTearDown(consent.dispose);
    final lock = AppLockService();
    addTearDown(lock.dispose);
    final api = ApiClient(authService: auth);
    Widget harness() => MaterialApp(
      locale: const Locale('fr'),
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: AppLocalizations.supportedLocales,
      home: MultiProvider(
        providers: [
          Provider<AppDatabase>.value(value: db),
          Provider<ApiClient>.value(value: api),
          ChangeNotifierProvider<AuthService>.value(value: auth),
          ChangeNotifierProvider<ConsentService>.value(value: consent),
          ChangeNotifierProvider<AppLockService>.value(value: lock),
        ],
        child: const ProfileScreen(),
      ),
    );

    Future<void> expandMedical() async {
      final medical = find.byKey(const Key('profile-medical-section'));
      await tester.ensureVisible(medical);
      await tester.pumpAndSettle();
      await tester.tap(find.descendant(
        of: medical,
        matching: find.byType(ExpansionTile),
      ));
      await tester.pumpAndSettle();
    }

    await tester.pumpWidget(harness());
    await tester.pumpAndSettle();
    await expandMedical();
    expect(find.byKey(const Key('d7-treatment-insulin')), findsOneWidget);
    expect(find.byKey(const Key('d7-treatment-oral_meds')), findsOneWidget);
    final type1 = find.text('Diabète Type 1');
    await tester.ensureVisible(type1);
    await tester.tap(type1);
    await tester.pumpAndSettle();

    final save = find.text('Enregistrer');
    await tester.ensureVisible(save);
    await tester.tap(save);
    await tester.pumpAndSettle();

    final saved = (await db.getProfileForLocalUserId(734))!;
    expect(saved.diabetesType, 'type1');
    expect(saved.treatment, 'tablets'); // Legacy declaration untouched.
    expect(saved.unitPreference, 'mg/dL');
    expect(saved.targetRangeLow, 84.125);
    expect(saved.targetRangeHigh, 168.75);
    final original = (await store.read())!;
    expect(original.codes, before.codes);
    expect(original.state, 'declared');
    expect(original.localGeneration, before.localGeneration);
    final otherAfter = (await db.getProfileForLocalUserId(812))!;
    expect(otherAfter.diabetesType, otherBefore!.diabetesType);
    expect(otherAfter.treatment, otherBefore.treatment);
    expect(otherAfter.targetRangeLow, otherBefore.targetRangeLow);
    expect(otherAfter.targetRangeHigh, otherBefore.targetRangeHigh);
    expect((await db.select(db.patientProfiles).get()).length, 2);

    // Simulate closing and opening the Profile screen with the same scoped DB.
    await tester.pumpWidget(const SizedBox.shrink());
    await tester.pumpAndSettle();
    await tester.pumpWidget(harness());
    await tester.pumpAndSettle();
    await expandMedical();
    expect(find.byKey(const Key('d7-treatment-insulin')), findsOneWidget);
    expect(find.byKey(const Key('d7-treatment-oral_meds')), findsOneWidget);

    // The patient may explicitly change their reported status; no automated
    // diagnosis-to-treatment inference is permitted.
    final none = find.byKey(const Key('d7-none'));
    await tester.ensureVisible(none);
    await tester.tap(none);
    await tester.pumpAndSettle();
    await tester.ensureVisible(save);
    await tester.tap(save);
    await tester.pumpAndSettle();
    final declared = (await store.read())!;
    expect(declared.state, 'none_declared');
    expect(declared.codes, isEmpty);
    expect(declared.localGeneration, greaterThan(before.localGeneration));
    expect(declared.syncStatus, 'pending'); // No remote confirmation.
    expect((await db.getProfileForLocalUserId(812))!.diabetesType, 'type1');
    expect(tester.takeException(), isNull);
  });
}
