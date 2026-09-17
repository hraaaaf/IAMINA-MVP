import 'package:firebase_core/firebase_core.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import 'core/localization/app_shell_localized_copy.dart';
import 'core/theme/amina_visual_language.dart';
import 'core/theme/app_theme.dart';
import 'data/drift/database.dart';
import 'firebase_options.dart';
import 'l10n/app_localizations.dart';
import 'routes/app_router.dart';
import 'services/api_client.dart';
import 'services/app_lock_service.dart';
import 'services/audit_access_policy.dart';
import 'services/auth_service.dart';
import 'services/consent_evidence_store.dart';
import 'services/consent_service.dart';
import 'services/firebase_migration_policy.dart';
import 'services/locale_preference_service.dart';
import 'services/modules_provider.dart';
import 'services/offline_demo_audit_seed.dart';
import 'services/sync_service.dart';

Future<bool> _hasProtectedLocalState({
  required AppDatabase db,
  required AuthService authService,
  required bool auditAllowed,
}) async {
  if (!auditAllowed && authService.isAuthenticated) return true;

  if (await (db.select(db.patientProfiles)..limit(1)).getSingleOrNull() != null) {
    return true;
  }
  if (await (db.select(db.logEntries)..limit(1)).getSingleOrNull() != null) {
    return true;
  }
  if (await (db.select(db.chatMessages)..limit(1)).getSingleOrNull() != null) {
    return true;
  }
  if (await (db.select(db.medicationEvents)..limit(1)).getSingleOrNull() != null) {
    return true;
  }
  if (await (db.select(db.reminders)..limit(1)).getSingleOrNull() != null) {
    return true;
  }
  return false;
}

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  if (kFirebaseMigrationEnabled) {
    try {
      await Firebase.initializeApp(
        options: DefaultFirebaseOptions.currentPlatform,
      );
    } catch (e) {
      debugPrint('Firebase migration init failed: $e');
    }
  }

  final db = AppDatabase.defaults();
  final consentEvidenceStore = ConsentEvidenceStore();
  var hasVerifiedConsentEvidence = false;
  try {
    hasVerifiedConsentEvidence = await consentEvidenceStore.hasCurrentEvidence();
  } catch (e) {
    // Fail closed: storage failure must never turn a timestamp into consent.
    debugPrint('Consent evidence read failed: $e');
  }
  final initialProfile =
      await (db.select(db.patientProfiles)..limit(1)).getSingleOrNull();
  final consentService = ConsentService(
    hasVerifiedEvidence: hasVerifiedConsentEvidence,
  )
    ..seedInitialProfile(initialProfile)
    ..attachStream(db.watchProfile());

  final auditAllowed = AuditAccessPolicy.isAllowed(Uri.base);
  final authService = AuthService();
  await authService.initialize();
  if (auditAllowed) {
    authService.enterAuditSession();
  }

  final appLockService = AppLockService(
    authService: authService,
    protectedLocalStateProbe: () => _hasProtectedLocalState(
      db: db,
      authService: authService,
      auditAllowed: auditAllowed,
    ),
  );
  await appLockService.initialize();

  await seedOfflineDemoAuditData(
    db,
    auditAllowed: auditAllowed,
    offlineDemo: kOfflineDemo,
  );

  final apiClient = ApiClient(authService: authService);
  final syncService = SyncService(db, apiClient)..init();
  final localePreferenceService = LocalePreferenceService(
    apiClient,
    auditLocale: auditAllowed
        ? AuditAccessPolicy.requestedLocale(Uri.base)
        : null,
  )..refresh();

  final routerHolder = createAppRouterHolder(
    authService: authService,
    consentService: consentService,
    appLockService: appLockService,
  );

  runApp(
    MultiProvider(
      providers: [
        Provider<AppDatabase>.value(value: db),
        ChangeNotifierProvider<AuthService>.value(value: authService),
        ChangeNotifierProvider<AppLockService>.value(value: appLockService),
        Provider<ApiClient>.value(value: apiClient),
        Provider<SyncService>.value(value: syncService),
        Provider<ConsentEvidenceStore>.value(value: consentEvidenceStore),
        ChangeNotifierProvider<ConsentService>.value(value: consentService),
        ChangeNotifierProvider<LocalePreferenceService>.value(
          value: localePreferenceService,
        ),
        ChangeNotifierProvider<ModulesProvider>(
          create: (_) => ModulesProvider(apiClient)..refresh(),
        ),
        StreamProvider<PatientProfileData?>(
          create: (context) => db.watchProfile(),
          initialData: null,
        ),
        ChangeNotifierProvider<TweaksNotifier>(
          create: (_) => TweaksNotifier(),
        ),
      ],
      child: AminaApp(
        router: routerHolder.router,
        appLockService: appLockService,
      ),
    ),
  );
}

class AminaApp extends StatefulWidget {
  final GoRouter router;
  final AppLockService appLockService;

  const AminaApp({
    super.key,
    required this.router,
    required this.appLockService,
  });

  @override
  State<AminaApp> createState() => _AminaAppState();
}

class _AminaAppState extends State<AminaApp> with WidgetsBindingObserver {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    switch (state) {
      case AppLifecycleState.hidden:
      case AppLifecycleState.paused:
        widget.appLockService.noteBackgrounded();
      case AppLifecycleState.resumed:
        widget.appLockService.noteResumed();
      case AppLifecycleState.detached:
        widget.appLockService.noteDetached();
      case AppLifecycleState.inactive:
        // Authentication/system UI can make the app temporarily inactive.
        // Do not lock on this transient state.
        break;
    }
  }

  @override
  Widget build(BuildContext context) {
    final tweaks = context.watch<TweaksNotifier>();
    final localePreference = context.watch<LocalePreferenceService>();

    return MaterialApp.router(
      title: 'IAmina',
      theme: AminaVisualLanguage.harmonize(AminaTheme.light),
      darkTheme: AminaVisualLanguage.harmonize(AminaTheme.dark),
      themeMode: tweaks.isDark ? ThemeMode.dark : ThemeMode.light,
      routerConfig: widget.router,
      locale: localePreference.locale,
      builder: (context, child) {
        ErrorWidget.builder = (FlutterErrorDetails details) {
          return Scaffold(
            body: Container(
              padding: const EdgeInsets.all(20),
              color: tweaks.isDark
                  ? AminaTheme.darkPaper
                  : AminaTheme.surfaceMuted,
              child: Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Icon(
                      Icons.error_outline,
                      color: AminaTheme.dangerRed,
                      size: 48,
                    ),
                    const SizedBox(height: 16),
                    Text(
                      AppLocalizations.of(context)!.renderError,
                      style: TextStyle(
                        fontWeight: FontWeight.w900,
                        fontSize: 18,
                        color: tweaks.isDark
                            ? AminaTheme.dark100
                            : AminaTheme.ink900,
                      ),
                    ),
                    const SizedBox(height: 8),
                    SelectableText(
                      details.exception.toString(),
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        color: tweaks.isDark
                            ? AminaTheme.dark400
                            : AminaTheme.textMuted,
                        fontSize: 12,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          );
        };
        return child!;
      },
      localizationsDelegates: const [
        AppLocalizations.delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      supportedLocales: AppLocalizations.supportedLocales,
      debugShowCheckedModeBanner: false,
    );
  }
}
