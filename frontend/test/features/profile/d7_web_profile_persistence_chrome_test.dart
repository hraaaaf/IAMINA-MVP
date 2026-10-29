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
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

// D7 single-patient first-user journey, on an actual remote Chrome renderer.
// Synthetic, isolated Web IndexedDB only; NO hosted SSO, real patient or
// clinician review is implied by a PASS here.
void main() {
  testWidgets('D7 Web: a returning patient changes type without altering '
      'treatment, physically reopens the vault, then edits explicitly',
      (tester) async {
    // One fixed test-only browser vault. GitHub runners are disposable.
    final scope = PatientVaultScope.deviceLocal(
      'eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee',
    );
    var db = AppDatabase.forPatientVault(scope);
    addTearDown(() async => db.close());
    await db.customSelect('SELECT 1').getSingle();
    expect(await db.getProfileForLocalUserId(db.activeProfileRowId), isNull);

    await db.into(db.patientProfiles).insert(
      PatientProfilesCompanion.insert(
        userId: drift.Value(db.activeProfileRowId),
        preferredLanguage: const drift.Value('fr'),
        updatedAt: DateTime.utc(2026, 10, 29),
        diabetesType: const drift.Value('type2'),
        treatment: const drift.Value('tablets'),
        unitPreference: const drift.Value('mg/dL'),
        targetRangeLow: const drift.Value(84),
        targetRangeHigh: const drift.Value(168),
      ),
    );
    final stored = PatientTreatmentDeclarationStore(db);
    await stored.write(state: 'declared', codes: ['oral_meds', 'insulin']);
    final before = (await stored.read())!;

    final auth = AuthService();
    addTearDown(auth.dispose);
    final consent = ConsentService()
      ..seedInitialProfile((await db.getProfileForLocalUserId(db.activeProfileRowId))!);
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

    // Change only the self-declared type. No implicit edit of treatment.
    final type1 = find.text('Diabète Type 1');
    await tester.ensureVisible(type1);
    await tester.tap(type1);
    await tester.pumpAndSettle();
    final save = find.text('Enregistrer');
    await tester.ensureVisible(save);
    await tester.tap(save);
    await tester.pumpAndSettle();

    final savedProfile =
        (await db.getProfileForLocalUserId(db.activeProfileRowId))!;
    expect(savedProfile.diabetesType, 'type1');
    expect(savedProfile.treatment, 'tablets');
    expect(savedProfile.targetRangeLow, 84);
    expect(savedProfile.targetRangeHigh, 168);
    final unchanged = (await PatientTreatmentDeclarationStore(db).read())!;
    expect(unchanged.state, before.state);
    expect(unchanged.codes, before.codes);
    expect(unchanged.localGeneration, before.localGeneration);

    // Tear down actual UI, close physical browser-backed SQLite, reopen
    // its same synthetic vault, then render ProfileScreen again.
    await tester.pumpWidget(const SizedBox.shrink());
    await tester.pumpAndSettle();
    await db.close();
    db = AppDatabase.forPatientVault(scope);
    await db.customSelect('SELECT 1').getSingle();
    final afterReload =
        (await db.getProfileForLocalUserId(db.activeProfileRowId))!;
    expect(afterReload.diabetesType, 'type1');
    expect(afterReload.treatment, 'tablets');
    final treatmentsAfterReload =
        (await PatientTreatmentDeclarationStore(db).read())!;
    expect(treatmentsAfterReload.codes, ['oral_meds', 'insulin']);
    expect(treatmentsAfterReload.localGeneration, before.localGeneration);

    await tester.pumpWidget(harness());
    await tester.pumpAndSettle();
    await expandMedical();
    expect(find.byKey(const Key('d7-treatment-insulin')), findsOneWidget);
    expect(find.byKey(const Key('d7-treatment-oral_meds')), findsOneWidget);

    // The patient alone explicitly reports no current treatment.
    final none = find.byKey(const Key('d7-none'));
    await tester.ensureVisible(none);
    await tester.tap(none);
    await tester.pumpAndSettle();
    await tester.ensureVisible(save);
    await tester.tap(save);
    await tester.pumpAndSettle();
    final explicitlyChanged =
        (await PatientTreatmentDeclarationStore(db).read())!;
    expect(explicitlyChanged.state, 'none_declared');
    expect(explicitlyChanged.codes, isEmpty);
    expect(explicitlyChanged.localGeneration,
        greaterThan(before.localGeneration));
    expect(explicitlyChanged.syncStatus, 'pending'); // Not a remote ACK.
    expect(tester.takeException(), isNull);
  });
}
