import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

import '../lib/core/theme/amina_visual_language.dart';
import '../lib/core/theme/app_theme.dart';
import '../lib/data/drift/database.dart';
import '../lib/features/companion/companion_screen.dart';
import '../lib/features/dashboard/dashboard_companion_entry_screen.dart';
import '../lib/features/dashboard/dashboard_screen.dart';
import '../lib/features/documents/document_import_screen.dart';
import '../lib/features/import/import_screen.dart';
import '../lib/features/journal/add_log_screen.dart';
import '../lib/features/journal/ai_summary_screen.dart';
import '../lib/features/journal/journal_screen.dart';
import '../lib/features/medications/medication_screen.dart';
import '../lib/features/profile/profile_screen.dart';
import '../lib/features/reminders/reminders_screen.dart';
import '../lib/l10n/app_localizations.dart';
import '../lib/services/api_client.dart';
import '../lib/services/auth_service.dart';
import '../lib/services/consent_service.dart';
import '../lib/services/modules_provider.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  final cases = <_GoldenCase>[
    const _GoldenCase('dashboard-390x844', Size(390, 844), 'dashboard'),
    const _GoldenCase('journal-390x844', Size(390, 844), 'journal'),
    const _GoldenCase('summary-390x844', Size(390, 844), 'summary'),
    const _GoldenCase('profile-390x844', Size(390, 844), 'profile'),
    const _GoldenCase('importer-390x844', Size(390, 844), 'importer'),
    const _GoldenCase('document-import-390x844', Size(390, 844), 'document-import'),
    const _GoldenCase('companion-390x844', Size(390, 844), 'companion'),
    const _GoldenCase('add-log-390x844', Size(390, 844), 'add-log'),
    const _GoldenCase('medications-390x844', Size(390, 844), 'medications'),
    const _GoldenCase('reminders-390x844', Size(390, 844), 'reminders'),
    const _GoldenCase('dashboard-1440x1000', Size(1440, 1000), 'dashboard'),
    const _GoldenCase('journal-1440x1000', Size(1440, 1000), 'journal'),
    const _GoldenCase('summary-1440x1000', Size(1440, 1000), 'summary'),
    const _GoldenCase('profile-1440x1000', Size(1440, 1000), 'profile'),
  ];

  for (final goldenCase in cases) {
    testWidgets('native visual audit ${goldenCase.name}', (tester) async {
      await tester.binding.setSurfaceSize(goldenCase.size);
      addTearDown(() => tester.binding.setSurfaceSize(null));

      final db = AppDatabase(NativeDatabase.memory());
      addTearDown(db.close);
      await db.seedDemoData();
      final profile =
          await (db.select(db.patientProfiles)..limit(1)).getSingleOrNull();

      final auth = AuthService();
      final api = ApiClient(authService: auth);
      final consent = ConsentService()
        ..seedInitialProfile(profile)
        ..attachStream(db.watchProfile());
      final modules = ModulesProvider(api);
      addTearDown(consent.dispose);
      addTearDown(modules.dispose);
      addTearDown(auth.dispose);

      await tester.pumpWidget(
        MaterialApp(
          debugShowCheckedModeBanner: false,
          theme: AminaVisualLanguage.harmonize(AminaTheme.light),
          darkTheme: AminaVisualLanguage.harmonize(AminaTheme.dark),
          themeMode: ThemeMode.light,
          locale: const Locale('fr'),
          localizationsDelegates: const [
            AppLocalizations.delegate,
            GlobalMaterialLocalizations.delegate,
            GlobalWidgetsLocalizations.delegate,
            GlobalCupertinoLocalizations.delegate,
          ],
          supportedLocales: AppLocalizations.supportedLocales,
          home: MultiProvider(
            providers: [
              Provider<AppDatabase>.value(value: db),
              ChangeNotifierProvider<AuthService>.value(value: auth),
              Provider<ApiClient>.value(value: api),
              ChangeNotifierProvider<ConsentService>.value(value: consent),
              ChangeNotifierProvider<ModulesProvider>.value(value: modules),
              ChangeNotifierProvider<TweaksNotifier>(
                create: (_) => TweaksNotifier(),
              ),
              StreamProvider<PatientProfileData?>(
                create: (_) => db.watchProfile(),
                initialData: profile,
              ),
            ],
            child: _surfaceFor(goldenCase.screen, goldenCase.size.width),
          ),
        ),
      );

      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump(const Duration(seconds: 1));

      expect(tester.takeException(), isNull);
      await expectLater(
        find.byType(MaterialApp),
        matchesGoldenFile('goldens/${goldenCase.name}.png'),
      );
    });
  }
}

Widget _surfaceFor(String screen, double width) {
  return switch (screen) {
    'journal' => const JournalScreen(),
    'summary' => const AISummaryScreen(),
    'profile' => const ProfileScreen(),
    'importer' => const ImportScreen(),
    'document-import' => const DocumentImportScreen(),
    'companion' => const CompanionScreen(),
    'add-log' => const AddLogScreen(),
    'medications' => const MedicationScreen(),
    'reminders' => const RemindersScreen(),
    _ => width < 700
        ? const DashboardCompanionEntryScreen()
        : const DashboardScreen(),
  };
}

class _GoldenCase {
  final String name;
  final Size size;
  final String screen;

  const _GoldenCase(this.name, this.size, this.screen);
}
