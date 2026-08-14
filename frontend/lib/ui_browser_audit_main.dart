import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:provider/provider.dart';

import 'core/theme/amina_visual_language.dart';
import 'core/theme/app_theme.dart';
import 'data/drift/database.dart';
import 'features/companion/companion_premium_screen.dart';
import 'features/dashboard/dashboard_companion_entry_screen.dart';
import 'features/documents/document_import_screen.dart';
import 'features/import/import_screen.dart';
import 'features/journal/add_log_screen.dart';
import 'features/journal/ai_summary_screen.dart';
import 'features/journal/journal_screen.dart';
import 'features/medications/medication_screen.dart';
import 'features/profile/profile_screen.dart';
import 'features/reminders/reminders_screen.dart';
import 'l10n/app_localizations.dart';
import 'services/api_client.dart';
import 'services/auth_service.dart';
import 'services/consent_service.dart';
import 'services/modules_provider.dart';
import 'services/sync_service.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();

  final db = AppDatabase.defaults();
  final auth = AuthService();
  final api = ApiClient(authService: auth);
  final consent = ConsentService()
    ..seedInitialProfile(null)
    ..attachStream(db.watchProfile());
  final modules = ModulesProvider(api);
  final sync = SyncService(db, api);

  runApp(
    MultiProvider(
      providers: [
        Provider<AppDatabase>.value(value: db),
        ChangeNotifierProvider<AuthService>.value(value: auth),
        Provider<ApiClient>.value(value: api),
        Provider<SyncService>.value(value: sync),
        ChangeNotifierProvider<ConsentService>.value(value: consent),
        ChangeNotifierProvider<ModulesProvider>.value(value: modules),
        ChangeNotifierProvider<TweaksNotifier>(create: (_) => TweaksNotifier()),
        StreamProvider<PatientProfileData?>(
          create: (_) => db.watchProfile(),
          initialData: null,
        ),
      ],
      child: const _BrowserAuditApp(),
    ),
  );

  WidgetsBinding.instance.addPostFrameCallback((_) async {
    try {
      await db.seedDemoData();
    } catch (error) {
      debugPrint('Browser audit demo seed unavailable: $error');
    }
  });
}

class _BrowserAuditApp extends StatelessWidget {
  const _BrowserAuditApp();

  @override
  Widget build(BuildContext context) {
    final surface = Uri.base.queryParameters['surface'] ?? 'dashboard';
    final child = switch (surface) {
      'dashboard' => const DashboardCompanionEntryScreen(),
      'companion' => const CompanionPremiumScreen(),
      'summary' => const AISummaryScreen(),
      'profile' => const ProfileScreen(),
      'journal' => const JournalScreen(),
      'importer' => const ImportScreen(),
      'document-import' => const DocumentImportScreen(),
      'add-log' => const AddLogScreen(),
      'medications' => const MedicationScreen(),
      'reminders' => const RemindersScreen(),
      _ => const DashboardCompanionEntryScreen(),
    };

    return MaterialApp(
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
      home: child,
    );
  }
}
