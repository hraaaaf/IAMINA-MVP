// D5 synthetic-only real Chrome FUE host. Uses the production Flutter screens,
// patient-vault scoped DB/storage, and a deterministic IP *test input*. This
// entrypoint is never included in production lib/main.dart or deployed.
import 'dart:html' as html; // Synthetic Web-only phase probe; never used in app main.

import 'package:drift/drift.dart' as drift;
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import 'core/theme/amina_visual_language.dart';
import 'core/theme/app_theme.dart';
import 'data/drift/database.dart';
import 'data/drift/patient_vault_scope.dart';
import 'features/auth/onboarding_chat_screen.dart';
import 'features/profile/profile_screen.dart';
import 'l10n/app_localizations.dart';
import 'services/api_client.dart';
import 'services/app_lock_service.dart';
import 'services/auth_service.dart';
import 'services/consent_service.dart';
import 'services/locale_preference_service.dart';
import 'services/modules_provider.dart';
import 'services/sync_service.dart';

class _D5DeterministicIp extends LocalePreferenceService {
  _D5DeterministicIp(super.api, this.suggestion, Locale locale)
      : super(auditLocale: locale);
  final String? suggestion;
  @override
  Future<String?> suggestCountryFromIp() async => suggestion;
}

// Fail visibly in the synthetic browser rather than producing an unexplained
// white screen. No stack trace or diagnostics are ever shipped to main.dart.
Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  var stage = 'initial';
  // Correlate the Flutter async bootstrap with the actual Chrome document.
  // A blank page with an unchanged index title means Dart was not entered.
  void mark(String value) {
    stage = value;
    html.document.title = 'D5_FUE_STAGE:$value';
  }
  mark('main');
  try {
    await _runD5(mark);
  } catch (error, stack) {
    html.document.title = 'D5_FUE_BOOT_FAILURE:$stage';
    debugPrint('D5_WEB_FUE_BOOT_FAILURE stage=$stage error=$error');
    debugPrintStack(stackTrace: stack);
    runApp(MaterialApp(
      home: Scaffold(
        body: SafeArea(
          child: SelectableText('D5_WEB_FUE_BOOT_FAILURE stage=$stage: $error'),
        ),
      ),
    ));
  }
}

Future<void> _runD5(void Function(String stage) mark) async {
  mark('query');
  final query = Uri.base.queryParameters;
  final language = query['locale'] == 'ar' ? 'ar' : 'fr';
  final owner = query['owner'] == 'b' ? 735 : 734;
  final mode = query['mode'] == 'returning' ? 'returning' : 'new';
  final suggestion = query['ip'] == 'ma' ? 'MA' : null;

  // Same isolation primitive as the app, not a shared synthetic demo DB.
  final scope = PatientVaultScope.nativeDjango(owner);
  final db = AppDatabase.forPatientVault(scope);
  final api = ApiClient();
  final auth = AuthService();
  final lock = AppLockService();
  final locale = _D5DeterministicIp(api, suggestion, Locale(language));
  mark('locale.refresh');
  await locale.refresh();
  mark('locale.bindCountryScope');
  await locale.bindCountryScope(scope.databaseName);
  mark('lock.initialize');
  await lock.initialize();

  mark('vault.getProfile');
  var profile = await db.getProfileForLocalUserId(db.activeProfileRowId);
  if (mode == 'returning' && profile == null) {
    // Returning synthetic user has a real persisted medical profile without
    // any claimed/implicitly migrated country. No consent is fabricated.
    mark('vault.insertSyntheticReturningProfile');
    await db.into(db.patientProfiles).insert(
      PatientProfilesCompanion.insert(
        userId: drift.Value(db.activeProfileRowId),
        preferredLanguage: drift.Value(language),
        updatedAt: DateTime.utc(2026, 10, 30),
        diabetesType: const drift.Value('type2'),
        treatment: const drift.Value('tablets'),
      ),
    );
    profile = await db.getProfileForLocalUserId(db.activeProfileRowId);
  }
  mark('dependencies');
  final consent = ConsentService()
    ..seedInitialProfile(profile)
    ..attachStream(db.watchProfileForLocalUserId(db.activeProfileRowId));
  final sync = SyncService(db, api);

  mark('runApp');
  runApp(MultiProvider(
    providers: [
      Provider<AppDatabase>.value(value: db),
      Provider<ApiClient>.value(value: api),
      ChangeNotifierProvider<AuthService>.value(value: auth),
      ChangeNotifierProvider<AppLockService>.value(value: lock),
      ChangeNotifierProvider<LocalePreferenceService>.value(value: locale),
      ChangeNotifierProvider<ConsentService>.value(value: consent),
      Provider<SyncService>.value(value: sync),
      ChangeNotifierProvider<ModulesProvider>(
        create: (_) => ModulesProvider(api),
      ),
      ChangeNotifierProvider<TweaksNotifier>(
        create: (_) => TweaksNotifier(),
      ),
      StreamProvider<PatientProfileData?>(
        create: (_) => db.watchProfileForLocalUserId(db.activeProfileRowId),
        initialData: profile,
      ),
    ],
    child: _D5BrowserApp(language: language, returning: mode == 'returning'),
  ));
}

class _D5BrowserApp extends StatefulWidget {
  const _D5BrowserApp({required this.language, required this.returning});
  final String language;
  final bool returning;

  @override
  State<_D5BrowserApp> createState() => _D5BrowserAppState();
}

class _D5BrowserAppState extends State<_D5BrowserApp> {
  late final GoRouter router = GoRouter(
    initialLocation: widget.returning ? '/profile' : '/onboarding',
    routes: [
      GoRoute(
        path: '/onboarding',
        builder: (_, __) => const OnboardingChatScreen(),
      ),
      GoRoute(
        path: '/preferences',
        builder: (_, __) => const OnboardingChatScreen(preferencesOnly: true),
      ),
      GoRoute(path: '/profile', builder: (_, __) => const ProfileScreen()),
      GoRoute(
        path: '/dashboard',
        builder: (_, __) => const Scaffold(
          body: Center(child: Text('D5_FUE_DASHBOARD')),
        ),
      ),
    ],
  );

  @override
  void dispose() {
    router.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => MaterialApp.router(
    debugShowCheckedModeBanner: false,
    theme: AminaVisualLanguage.harmonize(AminaTheme.light),
    locale: Locale(widget.language),
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
