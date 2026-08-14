import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

import 'package:amina/core/theme/amina_visual_language.dart';
import 'package:amina/core/theme/app_theme.dart';
import 'package:amina/data/drift/database.dart';
import 'package:amina/features/companion/companion_screen.dart';
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
import 'package:amina/services/consent_service.dart';
import 'package:amina/services/modules_provider.dart';
import 'package:amina/services/sync_service.dart';

class _Deps {
  final AppDatabase db;
  final PatientProfileData? profile;
  final AuthService auth;
  final ApiClient api;
  final ConsentService consent;
  final ModulesProvider modules;
  final SyncService sync;

  const _Deps({
    required this.db,
    required this.profile,
    required this.auth,
    required this.api,
    required this.consent,
    required this.modules,
    required this.sync,
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
  return _Deps(
    db: db,
    profile: profile,
    auth: auth,
    api: api,
    consent: consent,
    modules: modules,
    sync: sync,
  );
}

class _GoldenHarness extends StatelessWidget {
  final _Deps deps;
  final Widget child;
  final String captureKey;

  const _GoldenHarness({
    required this.deps,
    required this.child,
    required this.captureKey,
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
        locale: const Locale('fr'),
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

  const _CaptureSpec(this.name, this.size, this.builder);
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
    final deps = await _createDeps();
    addTearDown(() async {
      tester.view.resetPhysicalSize();
      tester.view.resetDevicePixelRatio();
      await deps.db.close();
    });

    const mobile = Size(390, 844);
    const desktop = Size(1440, 1000);
    final specs = <_CaptureSpec>[
      _CaptureSpec(
        'dashboard-390x844',
        mobile,
        () => const DashboardCompanionEntryScreen(),
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
        () => const CompanionScreen(),
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
      _CaptureSpec(
        'summary-1440x1000',
        desktop,
        () => const AISummaryScreen(),
      ),
      _CaptureSpec('profile-1440x1000', desktop, () => const ProfileScreen()),
    ];

    for (final spec in specs) {
      await _capture(tester, deps, spec);
    }
  });
}
