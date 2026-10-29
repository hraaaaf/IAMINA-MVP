// D11 CI-only routed Flutter Web UI FUE: actual signup/login/logout/recovery
// widgets against disposable native Django/PostgreSQL HTTP accounts.
// NO production entrypoint, fabricated medical measurements, external models,
// real patient accounts, or synthetic clinical-seed calls are used here.
// ignore: avoid_web_libraries_in_flutter
import 'dart:html' as html;

import 'package:amina/core/theme/app_theme.dart';
import 'package:amina/data/drift/database.dart';
import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:amina/features/auth/login_screen.dart';
import 'package:amina/features/navigation/main_shell.dart';
import 'package:amina/features/profile/profile_screen.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:amina/services/api_client.dart';
import 'package:amina/services/app_lock_service.dart';
import 'package:amina/services/auth_service.dart';
import 'package:amina/services/consent_service.dart';
import 'package:amina/services/modules_provider.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter/semantics.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

const ciApiBase = String.fromEnvironment('API_BASE_URL');

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  html.document.title = 'IAMINA_D11_UI_STARTING';

  // This suite is only allowed on the loopback CI test server.
  if (!ciApiBase.startsWith('http://127.0.0.1:') ||
      !kRemoteAccountEnrollmentEnabled) {
    html.document.title = 'IAMINA_D11_UI_FAIL:fixture_config';
    return;
  }

  final locale = Uri.base.queryParameters['locale'] ?? 'fr';
  if (locale != 'fr' && locale != 'ar') {
    html.document.title = 'IAMINA_D11_UI_FAIL:locale';
    return;
  }

  // Ensure Flutter Web's *actual* widget semantics are available for the
  // Playwright user-pointer + keyboard journey (not a driver that calls
  // widget handlers or AuthService methods directly).
  SemanticsBinding.instance.ensureSemantics();

  try {
    final auth = AuthService();
    await auth.initialize();

    // A synthetic-only audit vault is used solely to satisfy the existing
    // LoginScreen/ProfileScreen providers. No patient clinical rows are
    // created; the true native/PG account-isolation proof runs separately.
    final db = AppDatabase.forPatientVault(PatientVaultScope.auditOnly());
    final api = ApiClient(authService: auth);
    final modules = ModulesProvider(api);
    final consent = ConsentService()..seedInitialProfile(null);
    final lock = AppLockService(authService: auth);

    final router = GoRouter(
      initialLocation: '/login',
      refreshListenable: auth,
      redirect: (_, state) {
        final path = state.uri.path;
        if (!auth.isRemoteCredentialVerified && path != '/login' &&
            path != '/reset-password') return '/login';
        // LoginScreen itself routes successful login to /dashboard and
        // successful registration to /onboarding. Never preempt those
        // user-visible navigation steps when AuthService notifies GoRouter.
        return null;
      },
      routes: [
        GoRoute(path: '/login', builder: (_, __) => const LoginScreen()),
        GoRoute(
          path: '/onboarding',
          builder: (context, __) => Scaffold(
            body: Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Text('D11_UI_NATIVE_SIGNUP_DONE'),
                  FilledButton(
                    onPressed: () => context.go('/dashboard'),
                    child: const Text('D11_UI_CONTINUE'),
                  ),
                ],
              ),
            ),
          ),
        ),
        ShellRoute(
          builder: (_, __, child) => MainShell(child: child),
          routes: [
            GoRoute(
              path: '/dashboard',
              builder: (_, __) => const Scaffold(
                body: Center(
                  child: Text('D11_UI_VERIFIED_ACCOUNT_NO_DEMO_ROWS'),
                ),
              ),
            ),
            GoRoute(
              path: '/profile',
              builder: (_, __) => const ProfileScreen(),
            ),
          ],
        ),
        GoRoute(
          path: '/reset-password',
          builder: (_, __) => const Scaffold(
            body: Text('D11_UI_RESET_LINK_ROUTE'),
          ),
        ),
      ],
    );

    runApp(MultiProvider(
      providers: [
        ChangeNotifierProvider<AuthService>.value(value: auth),
        ChangeNotifierProvider<ModulesProvider>.value(value: modules),
        ChangeNotifierProvider<ConsentService>.value(value: consent),
        ChangeNotifierProvider<AppLockService>.value(value: lock),
        Provider<AppDatabase>.value(value: db),
        Provider<ApiClient>.value(value: api),
        Provider<PatientProfileData?>.value(value: null),
      ],
      child: MaterialApp.router(
        debugShowCheckedModeBanner: false,
        routerConfig: router,
        theme: AminaTheme.light,
        locale: Locale(locale),
        localizationsDelegates: const [
          AppLocalizations.delegate,
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        supportedLocales: AppLocalizations.supportedLocales,
      ),
    ));
    html.document.title = 'IAMINA_D11_UI_READY';
  } catch (error) {
    // No credentials or browser-local patient identifiers in title/logs.
    html.document.title = 'IAMINA_D11_UI_FAIL:bootstrap';
  }
}
