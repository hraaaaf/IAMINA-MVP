import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

import 'package:amina/core/theme/amina_visual_language.dart';
import 'package:amina/core/theme/app_theme.dart';
import 'package:amina/data/drift/database.dart';
import 'package:amina/data/models/companion_models.dart';
import 'package:amina/features/companion/companion_premium_screen.dart';
import 'package:amina/features/dashboard/dashboard_companion_entry_screen.dart';
import 'package:amina/features/dashboard/dashboard_screen.dart';
import 'package:amina/features/documents/document_import_screen.dart';
import 'package:amina/features/import/import_screen.dart';
import 'package:amina/features/journal/add_log_screen.dart';
import 'package:amina/features/journal/ai_summary_screen.dart';
import 'package:amina/features/journal/journal_screen.dart';
import 'package:amina/features/medications/medication_screen.dart';
import 'package:amina/features/profile/profile_screen.dart';
import 'package:amina/features/reminders/reminders_screen.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:amina/services/api_client.dart';
import 'package:amina/services/auth_service.dart';
import 'package:amina/services/companion_service.dart';
import 'package:amina/services/consent_service.dart';
import 'package:amina/services/modules_provider.dart';
import 'package:amina/services/sync_service.dart';

const _visualAuditEnabled = bool.fromEnvironment('IAMINA_VISUAL_AUDIT');

class _VisualCompanionService extends CompanionService {
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
    safetyNotice: 'governed_visual_fixture',
    sourceVersion: 'ui-visual-audit.v1',
  );
}

class _Deps {
  final AppDatabase db;
  final PatientProfileData? profile;
  final AuthService auth;
  final ApiClient api;
  final ConsentService consent;
  final ModulesProvider modules;
  final SyncService sync;
  final _VisualCompanionService visualCompanion;

  const _Deps({
    required this.db,
    required this.profile,
    required this.auth,
    required this.api,
    required this.consent,
    required this.modules,
    required this.sync,
    required this.visualCompanion,
  });
}

Future<_Deps> _createDeps() async {
  final db = AppDatabase(NativeDatabase.memory());
  await db.seedDemoData();
  final profile =
      await (db.select(db.patientProfiles)..limit(1)).getSingleOrNull();
  final auth = AuthService();
  final api = ApiClient(authService: auth);
  final consent = ConsentService()
    ..seedInitialProfile(profile)
    ..attachStream(db.watchProfile());
  final modules = ModulesProvider(api);
  final sync = SyncService(db, api);
  final visualCompanion = _VisualCompanionService();
  return _Deps(
    db: db,
    profile: profile,
    auth: auth,
    api: api,
    consent: consent,
    modules: modules,
    sync: sync,
    visualCompanion: visualCompanion,
  );
}

class _GoldenHarness extends StatelessWidget {
  final _Deps deps;
  final Widget child;
  final String captureKey;
  final Locale locale;

  const _GoldenHarness({
    required this.deps,
    required this.child,
    required this.captureKey,
    required this.locale,
  });

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        Provider<AppDatabase>.value(value: deps.db),
        ChangeNotifierProvider<AuthService>.value(value: deps.auth),
        Provider<ApiClient>.value(value: deps.api),
        Provider<SyncService>.value(value: deps.sync),
        ChangeNotifierProvider<ConsentService>.value(value: deps.consent),
        ChangeNotifierProvider<ModulesProvider>.value(value: deps.modules),
        ChangeNotifierProvider<TweaksNotifier>(create: (_) => TweaksNotifier()),
        StreamProvider<PatientProfileData?>(
          create: (_) => deps.db.watchProfile(),
          initialData: deps.profile,
        ),
      ],
      child: MaterialApp(
        debugShowCheckedModeBanner: false,
        theme: AminaVisualLanguage.harmonize(AminaTheme.light),
        darkTheme: AminaVisualLanguage.harmonize(AminaTheme.dark),
        themeMode: ThemeMode.light,
        locale: locale,
        localizationsDelegates: const [
          AppLocalizations.delegate,
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        supportedLocales: AppLocalizations.supportedLocales,
        home: RepaintBoundary(
          key: ValueKey<String>(captureKey),
          child: child,
        ),
      ),
    );
  }
}

class _CaptureSpec {
  final String name;
  final Size size;
  final Widget Function() builder;
  final Locale locale;

  const _CaptureSpec(
    this.name,
    this.size,
    this.builder, {
    this.locale = const Locale('fr'),
  });
}

Future<void> _capture(
  WidgetTester tester,
  _Deps deps,
  _CaptureSpec spec,
) async {
  tester.view.devicePixelRatio = 1.0;
  tester.view.physicalSize = spec.size;
  await tester.pumpWidget(
    _GoldenHarness(
      deps: deps,
      captureKey: spec.name,
      locale: spec.locale,
      child: spec.builder(),
    ),
  );
  await tester.pump();
  await tester.pump(const Duration(milliseconds: 1800));
  await expectLater(
    find.byKey(ValueKey<String>(spec.name)),
    matchesGoldenFile('ui_audit_output/${spec.name}.png'),
  );
  await tester.pumpWidget(const SizedBox.shrink());
  await tester.pump();
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('representative patient surfaces match the app visual system', (
    tester,
  ) async {
    if (!_visualAuditEnabled) return;

    final deps = await _createDeps();
    addTearDown(() async {
      tester.view.resetPhysicalSize();
      tester.view.resetDevicePixelRatio();
      deps.visualCompanion.dispose();
      await deps.db.close();
    });

    const compactMobile = Size(360, 560);
    const mobile = Size(390, 844);
    const desktop = Size(1440, 1000);
    final specs = <_CaptureSpec>[
      _CaptureSpec(
        'dashboard-360x560',
        compactMobile,
        () => DashboardCompanionEntryScreen(
          companionService: deps.visualCompanion,
        ),
      ),
      _CaptureSpec(
        'dashboard-ar-360x560',
        compactMobile,
        () => DashboardCompanionEntryScreen(
          companionService: deps.visualCompanion,
        ),
        locale: const Locale('ar'),
      ),
      _CaptureSpec(
        'dashboard-390x844',
        mobile,
        () => DashboardCompanionEntryScreen(
          companionService: deps.visualCompanion,
        ),
      ),
      _CaptureSpec('journal-390x844', mobile, () => const JournalScreen()),
      _CaptureSpec('summary-390x844', mobile, () => const AISummaryScreen()),
      _CaptureSpec('profile-390x844', mobile, () => const ProfileScreen()),
      _CaptureSpec('importer-390x844', mobile, () => const ImportScreen()),
      _CaptureSpec(
        'document-import-390x844',
        mobile,
        () => const DocumentImportScreen(),
      ),
      _CaptureSpec(
        'companion-390x844',
        mobile,
        () => const CompanionPremiumScreen(),
      ),
      _CaptureSpec('add-log-390x844', mobile, () => const AddLogScreen()),
      _CaptureSpec(
        'medications-390x844',
        mobile,
        () => const MedicationScreen(),
      ),
      _CaptureSpec(
        'reminders-390x844',
        mobile,
        () => const RemindersScreen(),
      ),
      _CaptureSpec(
        'dashboard-1440x1000',
        desktop,
        () => const DashboardScreen(),
      ),
      _CaptureSpec('journal-1440x1000', desktop, () => const JournalScreen()),
      _CaptureSpec('importer-1440x1000', desktop, () => const ImportScreen()),
      _CaptureSpec('profile-1440x1000', desktop, () => const ProfileScreen()),
    ];

    for (final spec in specs) {
      await _capture(tester, deps, spec);
    }
  });
}
