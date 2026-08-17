import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import 'core/theme/amina_visual_language.dart';
import 'core/theme/app_theme.dart';
import 'data/drift/database.dart';
import 'data/models/companion_models.dart';
import 'data/models/proactive_preview_models.dart';
import 'features/companion/companion_premium_screen.dart';
import 'features/dashboard/dashboard_companion_entry_screen.dart';
import 'features/dashboard/widgets/dashboard_adaptive_kpi_section.dart';
import 'features/dashboard/widgets/dashboard_insight_section.dart';
import 'features/dashboard/widgets/dashboard_next_action_section.dart';
import 'features/dashboard/widgets/dashboard_trend_section.dart';
import 'features/documents/document_import_premium_screen.dart';
import 'features/import/import_screen.dart';
import 'features/journal/add_log_screen.dart';
import 'features/journal/ai_summary_screen.dart';
import 'features/journal/journal_screen.dart';
import 'features/medications/medication_screen.dart';
import 'features/navigation/main_shell.dart';
import 'features/profile/profile_screen.dart';
import 'features/reminders/reminders_screen.dart';
import 'l10n/app_localizations.dart';
import 'services/api_client.dart';
import 'services/auth_service.dart';
import 'services/companion_service.dart';
import 'services/consent_service.dart';
import 'services/modules_provider.dart';
import 'services/sync_service.dart';

class _BrowserAuditCompanionService extends CompanionService {
  @override
  Future<CompanionOverview?> fetchOverview() async => CompanionOverview(
    patternStatus: 'ready',
    reviewStatus: 'ready',
    reviewAnchorCapturedAt: DateTime.utc(2026, 8, 15, 10),
    patterns: const <CompanionPattern>[],
    changesSinceReview: const <CompanionChange>[
      CompanionChange(
        observationKey: 'meal:lunch',
        changeKind: 'persisting',
        evidenceStrength: 'moderate',
        missingData: <String>[],
      ),
    ],
    afterVisit: const CompanionAfterVisit(
      status: 'no_recorded_visit',
      anchorId: null,
      occurredAt: null,
      source: null,
      factCount: 0,
      latestFactAt: null,
    ),
    safetyNotice: 'governed_browser_fixture',
    sourceVersion: 'ui-browser-audit.v1',
  );

  @override
  Future<ProactivePreview?> fetchProactivePreview() async => const ProactivePreview(
    status: 'available',
    attentionBudget: 'one_non_urgent_item_per_24h',
    cooldownUntil: null,
    pendingCount: 1,
    safetyNotice: 'governed_browser_preview_fixture',
    item: ProactivePreviewItem(
      observationKey: 'context:stress',
      kind: 'context',
      state: 'persisting',
      surfaceNow: false,
      whatChanged: 'repeated_eligible_evidence',
      whyItIsSurfacingNow: 'persistence_or_evidence_density_changed',
      evidenceWindowDays: 90,
      personalBaselineComparisonMgDl: 24,
      observations: 6,
      distinctDays: 4,
      evidenceDensity: 'moderate',
      limitationsOrMissingData: <String>[
        'observational_association_only',
        'no_causality_diagnosis_or_treatment_inference',
      ],
      allowedNextStep: 'PREPARE_CLINICIAN_DISCUSSION',
      escalationClass: 'none',
      evidenceId: 'rule.personal-response.repetition.v1',
      sourceVersion: 'proactive.personal-response.lifecycle.v1',
      priority: ProactivePreviewPriority(
        safetyTimeSensitivity: 'non_urgent_observation',
        clinicalRelevance: 'review_worthy',
        persistence: 'recurrent_episode',
        changeFromPersonalBaselineMgDl: 24,
        evidenceDensity: 'moderate',
        actionability: 'PREPARE_CLINICIAN_DISCUSSION',
        evidenceMaturity: 'internal_governed_rule',
        interruptionCost: 'eligible',
      ),
    ),
  );
}

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
  final visualCompanion = _BrowserAuditCompanionService();

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
      child: _BrowserAuditApp(visualCompanion: visualCompanion),
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
  final CompanionService visualCompanion;

  const _BrowserAuditApp({required this.visualCompanion});

  @override
  Widget build(BuildContext context) {
    final surface = Uri.base.queryParameters['surface'] ?? 'dashboard';
    final router = GoRouter(
      initialLocation: _pathForSurface(surface),
      routes: [
        ShellRoute(
          builder: (context, state, child) => MainShell(child: child),
          routes: [
            GoRoute(
              path: '/dashboard',
              builder: (context, state) => DashboardCompanionEntryScreen(
                companionService: visualCompanion,
              ),
            ),
            GoRoute(
              path: '/journal',
              builder: (context, state) => const JournalScreen(),
            ),
            GoRoute(
              path: '/summary',
              builder: (context, state) => const AISummaryScreen(),
            ),
            GoRoute(
              path: '/profile',
              builder: (context, state) => const ProfileScreen(),
            ),
          ],
        ),
        GoRoute(
          path: '/importer',
          builder: (context, state) => const ImportScreen(),
        ),
        GoRoute(
          path: '/document-import',
          builder: (context, state) => const DocumentImportPremiumScreen(),
        ),
        GoRoute(
          path: '/add-log',
          builder: (context, state) => const AddLogScreen(),
        ),
        GoRoute(
          path: '/medications',
          builder: (context, state) => const MedicationScreen(),
        ),
        GoRoute(
          path: '/reminders',
          builder: (context, state) => const RemindersScreen(),
        ),
        GoRoute(
          path: '/companion',
          builder: (context, state) => const CompanionPremiumScreen(),
        ),
        GoRoute(
          path: '/trend',
          builder: (context, state) => const _BrowserTrendSurface(),
        ),
        GoRoute(
          path: '/kpi',
          builder: (context, state) => const _BrowserKpiSurface(),
        ),
        GoRoute(
          path: '/insight',
          builder: (context, state) => _BrowserInsightSurface(
            service: visualCompanion,
          ),
        ),
        GoRoute(
          path: '/next-action',
          builder: (context, state) => _BrowserNextActionSurface(
            service: visualCompanion,
          ),
        ),
      ],
    );

    return MaterialApp.router(
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
      routerConfig: router,
    );
  }
}

String _pathForSurface(String surface) => switch (surface) {
  'dashboard' => '/dashboard',
  'journal' => '/journal',
  'summary' => '/summary',
  'profile' => '/profile',
  'importer' => '/importer',
  'document-import' => '/document-import',
  'add-log' => '/add-log',
  'medications' => '/medications',
  'reminders' => '/reminders',
  'companion' => '/companion',
  'trend' => '/trend',
  'kpi' => '/kpi',
  'insight' => '/insight',
  'next-action' => '/next-action',
  _ => '/dashboard',
};

class _BrowserTrendSurface extends StatelessWidget {
  const _BrowserTrendSurface();

  @override
  Widget build(BuildContext context) {
    final profile = context.watch<PatientProfileData?>();
    return Scaffold(
      backgroundColor: const Color(0xFFF4FBF9),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: DashboardTrendSection(
            unit: profile?.unitPreference ?? 'mg/dL',
            low: profile?.targetRangeLow,
            high: profile?.targetRangeHigh,
          ),
        ),
      ),
    );
  }
}

class _BrowserKpiSurface extends StatelessWidget {
  const _BrowserKpiSurface();

  @override
  Widget build(BuildContext context) {
    final profile = context.watch<PatientProfileData?>();
    return Scaffold(
      backgroundColor: const Color(0xFFF4FBF9),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: DashboardAdaptiveKpiSection(
            unit: profile?.unitPreference ?? 'mg/dL',
            low: profile?.targetRangeLow,
            high: profile?.targetRangeHigh,
          ),
        ),
      ),
    );
  }
}

class _BrowserInsightSurface extends StatelessWidget {
  final CompanionService service;

  const _BrowserInsightSurface({required this.service});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF4FBF9),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: DashboardInsightSection(service: service),
        ),
      ),
    );
  }
}

class _BrowserNextActionSurface extends StatelessWidget {
  final CompanionService service;

  const _BrowserNextActionSurface({required this.service});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF4FBF9),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: DashboardNextActionSection(service: service),
        ),
      ),
    );
  }
}
