import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:provider/provider.dart';
import 'package:go_router/go_router.dart';

import 'routes/app_router.dart';
import 'core/theme/app_theme.dart';
import 'l10n/app_localizations.dart';
import 'data/drift/database.dart';
import 'services/auth_service.dart';
import 'services/api_client.dart';
import 'services/sync_service.dart';
import 'services/consent_service.dart';
import 'services/modules_provider.dart';
import 'firebase_options.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  try {
    await Firebase.initializeApp(
      options: DefaultFirebaseOptions.currentPlatform,
    );
  } catch (e) {
    debugPrint('Firebase init failed: $e');
  }
  
  final db = AppDatabase.defaults();

  // ── Consent service — seed synchronously to prevent redirect flicker ──────
  final initialProfile =
      await (db.select(db.patientProfiles)..limit(1)).getSingleOrNull();
  final consentService = ConsentService()
    ..seedInitialProfile(initialProfile)
    ..attachStream(db.watchProfile());

  final authService = AuthService();
  final apiClient = ApiClient(authService: authService);
  final syncService = SyncService(db, apiClient)..init();

  // Build the router once with ConsentService so redirects fire correctly.
  final routerHolder = createAppRouterHolder(consentService: consentService);

  runApp(
    MultiProvider(
      providers: [
        Provider<AppDatabase>.value(value: db),
        Provider<AuthService>.value(value: authService),
        Provider<ApiClient>.value(value: apiClient),
        Provider<SyncService>.value(value: syncService),
        ChangeNotifierProvider<ConsentService>.value(value: consentService),
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
  /// The router is created once in main() and passed here so that
  /// ConsentService is wired before the first frame.
  final GoRouter router;
  const AminaApp({super.key, required this.router});

  @override
  State<AminaApp> createState() => _AminaAppState();
}

class _AminaAppState extends State<AminaApp> {
  @override
  Widget build(BuildContext context) {
    final tweaks = context.watch<TweaksNotifier>();

    return MaterialApp.router(
      title: 'IAmina',
      theme: AminaTheme.light,
      darkTheme: AminaTheme.dark,
      themeMode: tweaks.isDark ? ThemeMode.dark : ThemeMode.light,
      routerConfig: widget.router,
      
      // Global Error Catcher pour éviter les pages blanches silencieuses
      builder: (context, child) {
        ErrorWidget.builder = (FlutterErrorDetails details) {
          return Scaffold(
            body: Container(
              padding: const EdgeInsets.all(20),
              color: tweaks.isDark ? AminaTheme.darkPaper : AminaTheme.surfaceMuted,
              child: Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Icon(Icons.error_outline, color: AminaTheme.dangerRed, size: 48),
                    const SizedBox(height: 16),
                    Text(
                      'Une erreur de rendu est survenue',
                      style: TextStyle(
                        fontWeight: FontWeight.w900, 
                        fontSize: 18,
                        color: tweaks.isDark ? AminaTheme.dark100 : AminaTheme.ink900,
                      ),
                    ),
                    const SizedBox(height: 8),
                    SelectableText(
                      details.exception.toString(),
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        color: tweaks.isDark ? AminaTheme.dark400 : AminaTheme.textMuted, 
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
      supportedLocales: const [
        Locale('fr'),
        Locale('ar', 'MA'),
      ],
      debugShowCheckedModeBanner: false,
    );
  }
}
