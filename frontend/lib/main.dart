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
import 'services/audit_access_policy.dart';
import 'services/auth_service.dart';
import 'services/consent_service.dart';
import 'services/locale_preference_service.dart';
import 'services/modules_provider.dart';
import 'services/sync_service.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  try {
    await Firebase.initializeApp(
      options: DefaultFirebaseOptions.currentPlatform,
    );
  } catch (e) {
    debugPrint('Firebase init failed: $e');
  }

  final db = AppDatabase.defaults();
  final initialProfile =
      await (db.select(db.patientProfiles)..limit(1)).getSingleOrNull();
  final consentService = ConsentService()
    ..seedInitialProfile(initialProfile)
    ..attachStream(db.watchProfile());

  final auditAllowed = AuditAccessPolicy.isAllowed(Uri.base);
  final authService = AuthService();
  await authService.initialize();
  if (auditAllowed) {
    authService.enterAuditSession();
  }

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
  );

  runApp(
    MultiProvider(
      providers: [
        Provider<AppDatabase>.value(value: db),
        ChangeNotifierProvider<AuthService>.value(value: authService),
        Provider<ApiClient>.value(value: apiClient),
        Provider<SyncService>.value(value: syncService),
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
      child: AminaApp(router: routerHolder.router),
    ),
  );
}

class AminaApp extends StatefulWidget {
  final GoRouter router;
  const AminaApp({super.key, required this.router});

  @override
  State<AminaApp> createState() => _AminaAppState();
}

class _AminaAppState extends State<AminaApp> {
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
