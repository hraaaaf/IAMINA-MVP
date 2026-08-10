import 'package:amina/data/drift/database.dart';
import 'package:amina/features/profile/profile_screen.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:amina/services/consent_service.dart';
import 'package:drift/drift.dart' as drift;
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

void main() {
  testWidgets('Ramadan profile actions do not overflow at 360x560 in French', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(360, 560);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    final db = AppDatabase(NativeDatabase.memory());
    addTearDown(db.close);
    await db.into(db.patientProfiles).insert(
      PatientProfilesCompanion.insert(
        userId: const drift.Value(1),
        updatedAt: DateTime(2026, 8, 10),
        diabetesType: const drift.Value('type2'),
        treatment: const drift.Value('lifestyle'),
        ramadanStartDate: drift.Value(DateTime(2026, 2, 18)),
        ramadanEndDate: drift.Value(DateTime(2026, 3, 20)),
      ),
    );
    final profile = await db.select(db.patientProfiles).getSingle();
    final consent = ConsentService()..seedInitialProfile(profile);
    addTearDown(consent.dispose);

    await tester.pumpWidget(
      MaterialApp(
        locale: const Locale('fr'),
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        supportedLocales: AppLocalizations.supportedLocales,
        home: MultiProvider(
          providers: [
            Provider<AppDatabase>.value(value: db),
            ChangeNotifierProvider<ConsentService>.value(value: consent),
          ],
          child: const ProfileScreen(),
        ),
      ),
    );
    await tester.pumpAndSettle();

    final section = find.byKey(const ValueKey('profile-ramadan-section'));
    await tester.ensureVisible(section);
    await tester.pumpAndSettle();
    await tester.tap(
      find.descendant(of: section, matching: find.byType(ExpansionTile)),
    );
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.byKey(const Key('ramadan-save-period')));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('ramadan-clear-period')), findsOneWidget);
    expect(find.byKey(const Key('ramadan-save-period')), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
