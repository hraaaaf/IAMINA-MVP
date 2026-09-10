import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/date_symbol_data_local.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';

import 'core/theme/amina_visual_language.dart';
import 'core/theme/app_theme.dart';
import 'data/drift/database.dart';
import 'features/dashboard/dashboard_companion_entry_screen.dart';
import 'features/navigation/main_shell.dart';
import 'l10n/app_localizations.dart';
import 'services/api_client.dart';
import 'services/auth_service.dart';
import 'services/companion_service.dart';
import 'services/consent_service.dart';
import 'services/modules_provider.dart';
import 'services/sync_service.dart';

const String _certEmail = String.fromEnvironment('IAMINA_CERT_EMAIL');
const String _certPassword = String.fromEnvironment('IAMINA_CERT_PASSWORD');

double _certScrollOffsetFromUri() {
  final parsed = double.tryParse(Uri.base.queryParameters['scroll'] ?? '') ?? 0;
  if (!parsed.isFinite || parsed < 0) return 0;
  return parsed;
}

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await initializeDateFormatting();
  Intl.defaultLocale = 'fr';

  if (_certEmail.isEmpty || _certPassword.isEmpty) {
    throw StateError('Certification credentials are required');
  }

  final db = AppDatabase.defaults();
  await db.seedDemoData();

  final auth = AuthService();
  await auth.initialize();
  await auth.signInWithEmail(_certEmail, _certPassword);

  final api = ApiClient(authService: auth);
  final sync = SyncService(db, api)..init();
  final modules = ModulesProvider(api);
  await modules.refresh();
  final companion = CompanionService(authService: auth);
  final profile = await (db.select(db.patientProfiles)..limit(1))
      .getSingleOrNull();
  final consent = ConsentService()
    ..seedInitialProfile(profile)
    ..attachStream(db.watchProfile());

  runApp(
    MultiProvider(
      providers: [
        Provider<AppDatabase>.value(value: db),
        ChangeNotifierProvider<AuthService>.value(value: auth),
        Provider<ApiClient>.value(value: api),
        Provider<SyncService>.value(value: sync),
        ChangeNotifierProvider<ConsentService>.value(value: consent),
        ChangeNotifierProvider<ModulesProvider>.value(value: modules),
        StreamProvider<PatientProfileData?>(
          create: (_) => db.watchProfile(),
          initialData: profile,
        ),
        ChangeNotifierProvider<TweaksNotifier>(
          create: (_) => TweaksNotifier(),
        ),
      ],
      child: _DashboardBackendCertApp(companion: companion),
    ),
  );
}

class _DashboardBackendCertApp extends StatefulWidget {
  final CompanionService companion;

  const _DashboardBackendCertApp({required this.companion});

  @override
  State<_DashboardBackendCertApp> createState() =>
      _DashboardBackendCertAppState();
}

class _DashboardBackendCertAppState extends State<_DashboardBackendCertApp> {
  late final ScrollController _scrollController;

  @override
  void initState() {
    super.initState();
    _scrollController = ScrollController(
      initialScrollOffset: _certScrollOffsetFromUri(),
      keepScrollOffset: false,
      debugLabel: 'dashboard-cert-scroll',
    );
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final router = GoRouter(
      initialLocation: '/dashboard',
      routes: [
        ShellRoute(
          builder: (context, state, child) => MainShell(child: child),
          routes: [
            GoRoute(
              path: '/dashboard',
              builder: (context, state) => PrimaryScrollController(
                controller: _scrollController,
                automaticallyInheritForPlatforms: TargetPlatform.values.toSet(),
                scrollDirection: Axis.vertical,
                child: DashboardCompanionEntryScreen(
                  companionService: widget.companion,
                ),
              ),
            ),
          ],
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
