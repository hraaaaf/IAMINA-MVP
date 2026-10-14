import 'package:amina/data/drift/database.dart';
import 'package:amina/data/drift/patient_treatment_declaration_store.dart';
import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:amina/features/profile/profile_screen.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:amina/services/auth_service.dart';
import 'package:amina/services/consent_service.dart';
import 'package:drift/drift.dart' as drift;
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

void main() {
  const viewports = <Size>[
    Size(390, 844),
    Size(768, 1024),
    Size(1280, 900),
  ];
  const locales = ['fr', 'en', 'ar'];
  const copy = {
    'fr': 'Comparer et résoudre le conflit',
    'en': 'Review and resolve conflict',
    'ar': 'مراجعة التعارض وحلّه',
  };

  for (final size in viewports) {
    for (final lang in locales) {
      testWidgets(
        'D7 conflict CTA renders without overflow at '
        '${size.width.toInt()}x${size.height.toInt()} in $lang',
        (tester) async {
          tester.view.physicalSize = size;
          tester.view.devicePixelRatio = 1;
          addTearDown(tester.view.resetPhysicalSize);
          addTearDown(tester.view.resetDevicePixelRatio);

          final db = AppDatabase.testPatientVault(
            NativeDatabase.memory(), PatientVaultScope.nativeDjango(734),
          );
          addTearDown(db.close);
          await db.into(db.patientProfiles).insert(
            PatientProfilesCompanion.insert(
              userId: const drift.Value(734),
              preferredLanguage: drift.Value(lang),
              updatedAt: DateTime.utc(2026, 10, 14),
              diabetesType: const drift.Value('type2'),
              treatment: const drift.Value('tablets'),
            ),
          );
          final store = PatientTreatmentDeclarationStore(db);
          await store.write(state: 'declared', codes: ['insulin', 'oral_meds']);
          final record = (await store.read())!;
          expect(await store.markConflictIfUnchanged(record.localGeneration),
              isTrue);
          final profile = await db.getProfileForLocalUserId(734);
          final consent = ConsentService()..seedInitialProfile(profile!);
          addTearDown(consent.dispose);
          final auth = AuthService();
          addTearDown(auth.dispose);

          await tester.pumpWidget(MaterialApp(
            locale: Locale(lang),
            localizationsDelegates: AppLocalizations.localizationsDelegates,
            supportedLocales: AppLocalizations.supportedLocales,
            home: MultiProvider(
              providers: [
                Provider<AppDatabase>.value(value: db),
                ChangeNotifierProvider<ConsentService>.value(value: consent),
                ChangeNotifierProvider<AuthService>.value(value: auth),
              ],
              child: const ProfileScreen(),
            ),
          ));
          await tester.pumpAndSettle();
          // The medical section intentionally starts collapsed; a user must
          // expand it before a conflict CTA becomes visible and actionable.
          final medical = find.byKey(const Key('profile-medical-section'));
          await tester.ensureVisible(medical);
          await tester.pumpAndSettle();
          await tester.tap(find.descendant(
            of: medical, matching: find.byType(ExpansionTile),
          ));
          await tester.pumpAndSettle();

          final action = find.byKey(const Key('d7-resolve-treatment-conflict'));
          expect(action, findsOneWidget);
          expect(find.text(copy[lang]!), findsOneWidget);
          await tester.ensureVisible(action);
          await tester.pumpAndSettle();
          expect(tester.takeException(), isNull);
          // Viewing a conflict cannot change or ACK its local data.
          final after = (await store.read())!;
          expect(after.syncStatus, 'conflict');
          expect(after.codes, record.codes);
          expect(after.localGeneration, record.localGeneration);
        },
      );
    }
  }

  testWidgets('D7 non-conflicted declaration has no conflict CTA', (tester) async {
    final db = AppDatabase.testPatientVault(
      NativeDatabase.memory(), PatientVaultScope.nativeDjango(734),
    );
    addTearDown(db.close);
    await db.into(db.patientProfiles).insert(
      PatientProfilesCompanion.insert(
        userId: const drift.Value(734),
        updatedAt: DateTime.utc(2026, 10, 14),
      ),
    );
    final store = PatientTreatmentDeclarationStore(db);
    await store.write(state: 'declared', codes: ['lifestyle']);
    final profile = await db.getProfileForLocalUserId(734);
    final consent = ConsentService()..seedInitialProfile(profile!);
    addTearDown(consent.dispose);
    final auth = AuthService();
    addTearDown(auth.dispose);

    await tester.pumpWidget(MaterialApp(
      locale: const Locale('fr'),
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: AppLocalizations.supportedLocales,
      home: MultiProvider(
        providers: [
          Provider<AppDatabase>.value(value: db),
          ChangeNotifierProvider<ConsentService>.value(value: consent),
          ChangeNotifierProvider<AuthService>.value(value: auth),
        ],
        child: const ProfileScreen(),
      ),
    ));
    await tester.pumpAndSettle();
    final medical = find.byKey(const Key('profile-medical-section'));
    await tester.ensureVisible(medical);
    await tester.pumpAndSettle();
    await tester.tap(find.descendant(
      of: medical, matching: find.byType(ExpansionTile),
    ));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('d7-resolve-treatment-conflict')), findsNothing);
    expect((await store.read())?.syncStatus, 'pending');
    expect(tester.takeException(), isNull);
  });
}
