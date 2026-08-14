import 'package:drift/wasm.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:provider/provider.dart';

import 'core/theme/amina_visual_language.dart';
import 'core/theme/app_theme.dart';
import 'data/drift/database.dart';
import 'features/companion/companion_screen.dart';
import 'features/dashboard/dashboard_companion_entry_screen.dart';
import 'features/dashboard/dashboard_screen.dart';
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

/// CI-only visual audit entrypoint.
///
/// It deliberately bypasses Firebase and backend boot so screenshots prove the
/// real Flutter surfaces rather than an external-service startup path. Local
/// Drift data is seeded deterministically after runApp, and the same production
/// widgets/theme are mounted below the providers they normally consume.
void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const _UiAuditApp());
}

class _UiAuditApp extends StatefulWidget {
  const _UiAuditApp();

  @override
  State<_UiAuditApp> createState() => _UiAuditAppState();
}

class _UiAuditAppState extends State<_UiAuditApp> {
  late final Future<_AuditDependencies> _dependencies = _bootstrap();

  Future<_AuditDependencies> _bootstrap() async {
    final opened = await WasmDatabase.open(
      databaseName: 'iamina_ui_audit',
      sqlite3Uri: Uri.parse('sqlite3.wasm'),
      driftWorkerUri: Uri.parse('drift_worker.js'),
    );
    final db = AppDatabase(opened.resolvedExecutor);
    if (await db.countLogs() == 0) {
      await db.seedDemoData();
    }
    final profile =
        await (db.select(db.patientProfiles)..limit(1)).getSingleOrNull();

    final auth = AuthService();
    final api = ApiClient(authService: auth);
    final consent = ConsentService()
      ..seedInitialProfile(profile)
      ..attachStream(db.watchProfile());
    final modules = ModulesProvider(api);

    return _AuditDependencies(
      db: db,
      profile: profile,
      auth: auth,
      api: api,
      consent: consent,
      modules: modules,
    );
  }

  @override
  Widget build(BuildContext context) {
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
      builder: (context, child) {
        ErrorWidget.builder = (details) => Material(
          color: const Color(0xFFFFF3F0),
          child: Center(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Text(
                'UI AUDIT ERROR\n${details.exception}',
                textAlign: TextAlign.center,
                style: const TextStyle(
                  color: Color(0xFF8A1C0C),
                  fontSize: 14,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ),
          ),
        );
        return child!;
      },
      home: FutureBuilder<_AuditDependencies>(
        future: _dependencies,
        builder: (context, snapshot) {
          if (snapshot.hasError) {
            return _AuditState(
              icon: Icons.error_outline_rounded,
              title: 'UI audit bootstrap failed',
              body: snapshot.error.toString(),
            );
          }
          final deps = snapshot.data;
          if (deps == null) {
            return const _AuditState(
              loading: true,
              icon: Icons.auto_awesome_rounded,
              title: 'IAmina',
              body: 'Préparation de la surface de certification…',
            );
          }

          return MultiProvider(
            providers: [
              Provider<AppDatabase>.value(value: deps.db),
              ChangeNotifierProvider<AuthService>.value(value: deps.auth),
              Provider<ApiClient>.value(value: deps.api),
              ChangeNotifierProvider<ConsentService>.value(value: deps.consent),
              ChangeNotifierProvider<ModulesProvider>.value(value: deps.modules),
              ChangeNotifierProvider<TweaksNotifier>(
                create: (_) => TweaksNotifier(),
              ),
              StreamProvider<PatientProfileData?>(
                create: (_) => deps.db.watchProfile(),
                initialData: deps.profile,
              ),
            ],
            child: const _AuditSurface(),
          );
        },
      ),
    );
  }
}

class _AuditSurface extends StatelessWidget {
  const _AuditSurface();

  @override
  Widget build(BuildContext context) {
    final screen = Uri.base.queryParameters['screen'] ?? 'dashboard';
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
      _ => LayoutBuilder(
          builder: (context, constraints) => constraints.maxWidth < 700
              ? const DashboardCompanionEntryScreen()
              : const DashboardScreen(),
        ),
    };
  }
}

class _AuditDependencies {
  final AppDatabase db;
  final PatientProfileData? profile;
  final AuthService auth;
  final ApiClient api;
  final ConsentService consent;
  final ModulesProvider modules;

  const _AuditDependencies({
    required this.db,
    required this.profile,
    required this.auth,
    required this.api,
    required this.consent,
    required this.modules,
  });
}

class _AuditState extends StatelessWidget {
  final bool loading;
  final IconData icon;
  final String title;
  final String body;

  const _AuditState({
    this.loading = false,
    required this.icon,
    required this.title,
    required this.body,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Container(
          width: 320,
          padding: const EdgeInsets.all(24),
          decoration: AminaVisualLanguage.cardDecoration(context),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              if (loading)
                const SizedBox(
                  width: 28,
                  height: 28,
                  child: CircularProgressIndicator(strokeWidth: 2.4),
                )
              else
                Icon(icon, size: 30, color: AminaVisualLanguage.actionGreen),
              const SizedBox(height: 14),
              Text(
                title,
                textAlign: TextAlign.center,
                style: const TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w800,
                  color: AminaVisualLanguage.forest,
                ),
              ),
              const SizedBox(height: 7),
              Text(
                body,
                textAlign: TextAlign.center,
                style: const TextStyle(
                  fontSize: 12.5,
                  height: 1.4,
                  color: AminaVisualLanguage.secondaryText,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
