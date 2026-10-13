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
import 'services/api_client.dart';
import 'services/app_lock_protected_state_policy.dart';
import 'services/app_lock_service.dart';
import 'services/audit_access_policy.dart';
import 'services/auth_service.dart';
import 'services/firebase_migration_policy.dart';
import 'services/medical_vault_protected_state.dart';
import 'services/locale_preference_service.dart';
import 'services/patient_vault_session_controller.dart';
import 'services/patient_vault_app_host.dart';


Future<bool> _hasProtectedLocalState({
  required AppDatabase db,
  required AuthService authService,
  required bool auditAllowed,
}) async {
  if (authSessionCountsAsProtectedLocalState(
    auditAllowed: auditAllowed,
    isAuthenticated: authService.isAuthenticated,
    hasRemoteApiCredential: authService.hasRemoteApiCredential,
  )) {
    return true;
  }

  return hasProtectedMedicalVaultRows(db);
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

  final auditAllowed = AuditAccessPolicy.isAllowed(Uri.base);
  final authService = AuthService();
  await authService.initialize();
  if (auditAllowed) authService.enterAuditSession();

  // The historical mixed-owner DB is inspected solely to keep device-lock
  // recovery fail-closed. Never pass it to any patient-facing Provider.
  final legacy = AppDatabase.defaults();
  bool legacyProtected = true;
  try {
    legacyProtected = await _hasProtectedLocalState(
      db: legacy, authService: authService, auditAllowed: auditAllowed,
    );
  } finally {
    await legacy.close();
  }

  // A missing app-lock credential must not be treated as a fresh install
  // merely because the quarantined pre-D7 database is empty. Inspect ONLY
  // the currently resolved patient vault; never transfer or expose its rows.
  var currentVaultProtected = false;
  if (!auditAllowed && !legacyProtected) {
    AppDatabase? protectedStateProbe;
    try {
      final scope = await authService.resolvePatientVaultScope();
      if (scope != null) {
        protectedStateProbe = AppDatabase.forPatientVault(scope);
        currentVaultProtected = await hasProtectedMedicalVaultRows(protectedStateProbe);
      }
    } catch (_) {
      // An inaccessible vault is not proof of a clean fresh installation.
      currentVaultProtected = true;
    } finally {
      await protectedStateProbe?.close();
    }
  }

  final appLockService = AppLockService(
    authService: authService,
    protectedLocalStateProbe: () async =>
        legacyProtected || currentVaultProtected,
  );
  await appLockService.initialize();
  // Switching A to B must revoke the previous device unlock immediately.
  authService.addListener(appLockService.lock);

  final apiClient = ApiClient(authService: authService);
  final localePreferenceService = LocalePreferenceService(
    apiClient,
    auditLocale: auditAllowed
        ? AuditAccessPolicy.requestedLocale(Uri.base)
        : null,
  )..refresh();

  final vaultController = PatientVaultSessionController.forAuth(authService);
  await vaultController.reconcile();

  runApp(PatientVaultAppHost(
    auth: authService,
    api: apiClient,
    appLock: appLockService,
    locale: localePreferenceService,
    controller: vaultController,
    auditAllowed: auditAllowed,
  ));
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
