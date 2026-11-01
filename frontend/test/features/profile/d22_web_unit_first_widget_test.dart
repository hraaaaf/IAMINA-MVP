import 'package:amina/data/drift/database.dart';
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

/// D22-A: isolated widget evidence for the real Profile medical section.
///
/// Test data is synthetic. This does not approve target values, normalize
/// measurements, review legacy provenance, or replace real Chrome FUE.
void main() {
  const viewports = <Size>[
    Size(390, 844),
    Size(768, 1024),
    Size(1280, 900),
  ];

  for (final viewport in viewports) {
    for (final language in <String>['fr', 'ar']) {
      testWidgets(
        'D22-A Profile renders unit before target ${viewport.width.toInt()}x'
        '${viewport.height.toInt()} $language',
        (tester) async {
          tester.view.physicalSize = viewport;
          tester.view.devicePixelRatio = 1;
          addTearDown(tester.view.resetPhysicalSize);
          addTearDown(tester.view.resetDevicePixelRatio);

          final db = AppDatabase.testPatientVault(
            NativeDatabase.memory(),
            PatientVaultScope.nativeDjango(734),
          );
          addTearDown(db.close);
          await db.into(db.patientProfiles).insert(
            PatientProfilesCompanion.insert(
              userId: const drift.Value(734),
              preferredLanguage: drift.Value(language),
              updatedAt: DateTime.utc(2026, 11, 1),
              unitPreference: const drift.Value('mg/dL'),
              // Synthetic legacy fixtures, not recommended targets.
              targetRangeLow: const drift.Value(84),
              targetRangeHigh: const drift.Value(168),
            ),
          );

          final auth = AuthService();
          final consent = ConsentService()
            ..seedInitialProfile((await db.getProfileForLocalUserId(734))!);
          final lock = AppLockService();
          final api = ApiClient(authService: auth);
          addTearDown(auth.dispose);
          addTearDown(consent.dispose);
          addTearDown(lock.dispose);

          await tester.pumpWidget(MaterialApp(
            locale: Locale(language),
            supportedLocales: AppLocalizations.supportedLocales,
            localizationsDelegates: AppLocalizations.localizationsDelegates,
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
          ));
          await tester.pumpAndSettle();

          final medical = find.byKey(const Key('profile-medical-section'));
          expect(medical, findsOneWidget);
          await tester.ensureVisible(medical);
          await tester.pumpAndSettle();
          await tester.tap(find.descendant(
            of: medical,
            matching: find.byType(ExpansionTile),
          ));
          await tester.pumpAndSettle();

          final l10n = AppLocalizations.of(tester.element(medical))!;
          final unitHeading = find.text(l10n.measureUnit);
          final targetHeading = find.text(l10n.glucoseTarget);
          expect(unitHeading, findsOneWidget);
          expect(targetHeading, findsOneWidget);
          // This is the actual rendered widget order, not source text order.
          expect(
            tester.getTopLeft(unitHeading).dy,
            lessThan(tester.getTopLeft(targetHeading).dy),
          );
          expect(
            Directionality.of(tester.element(unitHeading)),
            language == 'ar' ? TextDirection.rtl : TextDirection.ltr,
          );
          expect(find.text('mg/dL'), findsWidgets);
          expect(find.text('mmol/L'), findsWidgets);
          expect(tester.takeException(), isNull);
        },
      );
    }
  }
}
