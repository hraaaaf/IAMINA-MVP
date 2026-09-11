import 'package:firebase_core/firebase_core.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:provider/provider.dart';

import 'core/theme/amina_visual_language.dart';
import 'core/theme/app_theme.dart';
import 'data/drift/database.dart';
import 'features/auth/consent_screen.dart';
import 'features/auth/login_screen.dart';
import 'features/auth/onboarding_chat_screen.dart';
import 'features/auth/reset_password_screen.dart';
import 'features/companion/companion_conversation_screen.dart';
import 'features/import/cgm_screen.dart';
import 'features/journal/edit_log_screen.dart';
import 'firebase_options.dart';
import 'l10n/app_localizations.dart';
import 'services/api_client.dart';
import 'services/auth_service.dart';
import 'services/cgm_service.dart';
import 'services/companion_service.dart';
import 'services/consent_service.dart';
import 'services/locale_preference_service.dart';

class _AuditCgmService extends CgmService {
  @override
  Future<CgmConnectionState> getConnection() async =>
      const CgmConnectionState(connected: false);
}

class _SeededEditLog extends StatefulWidget {
  final AppDatabase db;

  const _SeededEditLog({required this.db});

  @override
  State<_SeededEditLog> createState() => _SeededEditLogState();
}

class _SeededEditLogState extends State<_SeededEditLog> {
  late final Future<void> _seed = widget.db.seedDemoData();

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<void>(
      future: _seed,
      builder: (context, snapshot) {
        if (snapshot.connectionState != ConnectionState.done) {
          return const Scaffold(body: Center(child: CircularProgressIndicator()));
        }
        return const EditLogScreen(logId: 1);
      },
    );
  }
}

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  try {
    await Firebase.initializeApp(options: DefaultFirebaseOptions.currentPlatform);
  } catch (error) {
    debugPrint('Global route audit Firebase init unavailable: $error');
  }

  final db = AppDatabase.defaults();
  final auth = AuthService();
  final api = ApiClient(authService: auth);
  final consent = ConsentService()
    ..seedInitialProfile(null)
    ..attachStream(db.watchProfile());
  final localePreferences = LocalePreferenceService(
    api,
    auditLocale: const Locale('fr'),
  );
  final companion = CompanionService(authService: auth);
  final cgm = _AuditCgmService();
  final surface = Uri.base.queryParameters['surface'] ?? 'login';

  runApp(
    MultiProvider(
      providers: [
        Provider<AppDatabase>.value(value: db),
        ChangeNotifierProvider<AuthService>.value(value: auth),
        Provider<ApiClient>.value(value: api),
        ChangeNotifierProvider<ConsentService>.value(value: consent),
        ChangeNotifierProvider<LocalePreferenceService>.value(
          value: localePreferences,
        ),
        StreamProvider<PatientProfileData?>(
          create: (_) => db.watchProfile(),
          initialData: null,
        ),
      ],
      child: MaterialApp(
        debugShowCheckedModeBanner: false,
        theme: AminaVisualLanguage.harmonize(AminaTheme.light),
        themeMode: ThemeMode.light,
        locale: const Locale('fr'),
        localizationsDelegates: const [
          AppLocalizations.delegate,
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        supportedLocales: AppLocalizations.supportedLocales,
        home: switch (surface) {
          'login' => const LoginScreen(),
          'reset-password' => const ResetPasswordScreen(
              uid: 'audit-user',
              token: 'audit-token',
            ),
          'consent' => const ConsentScreen(),
          'onboarding' => const OnboardingChatScreen(),
          'companion-chat' => CompanionConversationScreen(service: companion),
          'cgm' => CgmScreen(service: cgm),
          'edit-log' => _SeededEditLog(db: db),
          _ => const LoginScreen(),
        },
      ),
    ),
  );
}
