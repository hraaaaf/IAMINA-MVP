import 'package:amina/data/drift/database.dart';
import 'package:amina/features/auth/onboarding_chat_screen.dart';
import 'package:amina/features/profile/profile_screen.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:amina/services/api_client.dart';
import 'package:amina/services/auth_service.dart';
import 'package:amina/services/locale_preference_service.dart';
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

class _SuggestedCountryPreferences extends LocalePreferenceService {
  _SuggestedCountryPreferences(this.suggested)
      : super(ApiClient(baseUrl: 'http://localhost:8000'));

  final String? suggested;
  int persistedCountryCount = 0;
  String? persistedCountry;

  @override
  Future<String?> suggestCountryFromIp() async => suggested;

  @override
  Future<void> setLanguageOnly(String language) async {}

  @override
  Future<void> setExperience({
    required String language,
    required String country,
    required String tone,
  }) async {
    persistedCountryCount += 1;
    persistedCountry = country;
  }
}

void main() {
  test('legacy country prompt never blocks a stored profile', () {
    expect(shouldShowReturningCountryPrompt(
      hasProfile: true,
      preferenceLoaded: true,
      confirmedCountry: null,
      dismissed: false,
    ), isTrue);
    expect(shouldShowReturningCountryPrompt(
      hasProfile: true,
      preferenceLoaded: true,
      confirmedCountry: null,
      dismissed: true,
    ), isFalse);
    expect(shouldShowReturningCountryPrompt(
      hasProfile: true,
      preferenceLoaded: true,
      confirmedCountry: 'FR',
      dismissed: false,
    ), isFalse);
    expect(shouldShowReturningCountryPrompt(
      hasProfile: false,
      preferenceLoaded: true,
      confirmedCountry: null,
      dismissed: false,
    ), isFalse);
    expect(shouldShowReturningCountryPrompt(
      hasProfile: true,
      preferenceLoaded: false,
      confirmedCountry: null,
      dismissed: false,
    ), isFalse);
  });

  testWidgets('IP suggestion cannot finish onboarding until explicitly confirmed',
      (tester) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    final db = AppDatabase(NativeDatabase.memory());
    final preferences = _SuggestedCountryPreferences('MA');
    final auth = AuthService();
    addTearDown(db.close);
    addTearDown(preferences.dispose);
    addTearDown(auth.dispose);

    final router = GoRouter(initialLocation: '/onboarding', routes: [
      GoRoute(path: '/onboarding', builder: (_, __) => const OnboardingChatScreen()),
      GoRoute(path: '/dashboard',
          builder: (_, __) => const Scaffold(body: Text('D5 Dashboard'))),
    ]);
    addTearDown(router.dispose);
    await tester.pumpWidget(MultiProvider(
      providers: [
        Provider<AppDatabase>.value(value: db),
        ChangeNotifierProvider<AuthService>.value(value: auth),
        ChangeNotifierProvider<LocalePreferenceService>.value(value: preferences),
      ],
      child: MaterialApp.router(
        routerConfig: router,
        locale: const Locale('fr'),
        localizationsDelegates: const [
          AppLocalizations.delegate,
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        supportedLocales: AppLocalizations.supportedLocales,
      ),
    ));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Français'));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('onboarding-confirm-suggested-country')),
        findsOneWidget);
    expect(find.text('Maroc'), findsWidgets);

    await tester.tap(find.byKey(const Key('onboarding-sticky-start')));
    await tester.pumpAndSettle();
    expect(preferences.persistedCountryCount, 0);
    expect(find.text('D5 Dashboard'), findsNothing);

    await tester.ensureVisible(
        find.byKey(const Key('onboarding-confirm-suggested-country')));
    await tester.tap(
        find.byKey(const Key('onboarding-confirm-suggested-country')));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('onboarding-confirm-suggested-country')),
        findsNothing);
    await tester.tap(find.byKey(const Key('onboarding-sticky-start')));
    await tester.pumpAndSettle();
    expect(preferences.persistedCountryCount, 1);
    expect(preferences.persistedCountry, 'MA');
    expect(find.text('D5 Dashboard'), findsOneWidget);
  });

  testWidgets('IP unavailable remains manual, never creates a default country',
      (tester) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    final db = AppDatabase(NativeDatabase.memory());
    final preferences = _SuggestedCountryPreferences(null);
    final auth = AuthService();
    addTearDown(db.close);
    addTearDown(preferences.dispose);
    addTearDown(auth.dispose);
    final router = GoRouter(initialLocation: '/onboarding', routes: [
      GoRoute(path: '/onboarding', builder: (_, __) => const OnboardingChatScreen()),
      GoRoute(path: '/dashboard',
          builder: (_, __) => const Scaffold(body: Text('D5 Dashboard'))),
    ]);
    addTearDown(router.dispose);
    await tester.pumpWidget(MultiProvider(
      providers: [
        Provider<AppDatabase>.value(value: db),
        ChangeNotifierProvider<AuthService>.value(value: auth),
        ChangeNotifierProvider<LocalePreferenceService>.value(value: preferences),
      ],
      child: MaterialApp.router(
        routerConfig: router,
        locale: const Locale('fr'),
        localizationsDelegates: const [
          AppLocalizations.delegate,
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        supportedLocales: AppLocalizations.supportedLocales,
      ),
    ));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Français'));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('onboarding-confirm-suggested-country')),
        findsNothing);
    await tester.tap(find.byKey(const Key('onboarding-sticky-start')));
    await tester.pumpAndSettle();
    expect(preferences.persistedCountryCount, 0);
    expect(find.text('D5 Dashboard'), findsNothing);
  });
}
