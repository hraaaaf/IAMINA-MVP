import 'package:amina/data/drift/database.dart';
import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:amina/features/auth/onboarding_chat_screen.dart';
import 'package:amina/features/profile/profile_screen.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:amina/services/api_client.dart';
import 'package:amina/services/auth_service.dart';
import 'package:amina/services/app_lock_service.dart';
import 'package:amina/services/consent_service.dart';
import 'package:amina/services/locale_preference_service.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:drift/native.dart';
import 'package:drift/drift.dart' as drift;
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

class _ReadyCountryPreferences extends LocalePreferenceService {
  _ReadyCountryPreferences(this.selected)
      : super(ApiClient(baseUrl: 'http://localhost:8000'));

  final String? selected;

  @override
  bool get loaded => true;

  @override
  bool get countryScopeReady => true;

  @override
  String? get country => selected;
}

void main() {
  test('A to B to A country isolation: legacy browser value never proves owner',
      () async {
    FlutterSecureStorage.setMockInitialValues({
      'iamina.country': 'MA',
    });
    const storage = FlutterSecureStorage();
    final service = LocalePreferenceService(
      ApiClient(baseUrl: 'http://localhost:8000'),
      storage: storage,
      systemLocale: const Locale('fr'),
    );
    addTearDown(service.dispose);

    await service.refresh();
    expect(service.country, isNull);
    await service.bindCountryScope('amina_vault_v1_native_734');
    expect(service.countryScopeReady, isTrue);
    expect(service.country, isNull);
    await service.setExperience(language: 'fr', country: 'FR', tone: 'neutral');
    expect(service.country, 'FR');

    await service.bindCountryScope(null);
    expect(service.country, isNull);
    await service.bindCountryScope('amina_vault_v1_native_735');
    expect(service.countryScopeReady, isTrue);
    expect(service.country, isNull);
    await service.setExperience(language: 'fr', country: 'ES', tone: 'neutral');
    expect(service.country, 'ES');

    await service.bindCountryScope('amina_vault_v1_native_734');
    expect(service.country, 'FR');
    expect(await storage.read(key: 'iamina.country'), 'MA');
    expect(await storage.read(key: 'iamina.country.v1.amina_vault_v1_native_734'), 'FR');
    expect(await storage.read(key: 'iamina.country.v1.amina_vault_v1_native_735'), 'ES');
  });

  test('unbound country cannot be saved under a global key', () async {
    FlutterSecureStorage.setMockInitialValues({});
    const storage = FlutterSecureStorage();
    final service = LocalePreferenceService(
      ApiClient(baseUrl: 'http://localhost:8000'),
      storage: storage,
      systemLocale: const Locale('fr'),
    );
    addTearDown(service.dispose);
    await expectLater(
      service.setExperience(language: 'fr', country: 'MA', tone: 'neutral'),
      throwsStateError,
    );
    expect(await storage.read(key: 'iamina.country'), isNull);
  });

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

  for (final lang in ['fr', 'ar']) {
    testWidgets('returning Web profile can postpone country without data loss in $lang',
        (tester) async {
      tester.view.physicalSize = const Size(390, 844);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      final db = AppDatabase.testPatientVault(
        NativeDatabase.memory(), PatientVaultScope.nativeDjango(734),
      );
      addTearDown(db.close);
      await db.into(db.patientProfiles).insert(
        PatientProfilesCompanion.insert(
          userId: const drift.Value(734),
          preferredLanguage: drift.Value(lang),
          updatedAt: DateTime.utc(2026, 10, 30),
          diabetesType: const drift.Value('type2'),
          treatment: const drift.Value('tablets'),
        ),
      );
      final before = (await db.getProfileForLocalUserId(734))!;
      final consent = ConsentService()..seedInitialProfile(before);
      final auth = AuthService();
      final preferences = _ReadyCountryPreferences(null);
      addTearDown(consent.dispose);
      addTearDown(auth.dispose);
      addTearDown(preferences.dispose);

      await tester.pumpWidget(MaterialApp(
        locale: Locale(lang),
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        supportedLocales: AppLocalizations.supportedLocales,
        home: MultiProvider(
          providers: [
            Provider<AppDatabase>.value(value: db),
            ChangeNotifierProvider<ConsentService>.value(value: consent),
            ChangeNotifierProvider<AuthService>.value(value: auth),
            ChangeNotifierProvider<AppLockService>(
              create: (_) => AppLockService(),
            ),
            ChangeNotifierProvider<LocalePreferenceService>.value(
              value: preferences,
            ),
          ],
          child: const ProfileScreen(),
        ),
      ));
      await tester.pumpAndSettle();
      expect(find.byKey(const ValueKey('d5-country-legacy-prompt')),
          findsOneWidget);
      expect(find.byKey(const ValueKey('d5-country-choose')), findsOneWidget);
      expect(find.byKey(const ValueKey('d5-country-later')), findsOneWidget);
      await tester.tap(find.byKey(const ValueKey('d5-country-later')));
      await tester.pumpAndSettle();
      expect(find.byKey(const ValueKey('d5-country-legacy-prompt')),
          findsNothing);
      expect(find.byKey(const ValueKey('profile-medical-section')),
          findsOneWidget);
      final after = await db.getProfileForLocalUserId(734);
      expect(after?.diabetesType, before.diabetesType);
      expect(after?.treatment, before.treatment);
      expect(after?.aiConsentGivenAt, before.aiConsentGivenAt);
      expect(tester.takeException(), isNull);
    });
  }

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
