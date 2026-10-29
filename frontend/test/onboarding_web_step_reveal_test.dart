import 'package:amina/data/drift/database.dart';
import 'package:amina/features/auth/onboarding_chat_screen.dart';
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

// Synthetic, zero-patient viewport contract. No browser storage, API or
// clinical transport is required for the navigation-only assertions.
class _LocalPreferences extends LocalePreferenceService {
  _LocalPreferences() : super(ApiClient(baseUrl: 'http://localhost:8000'));

  @override
  Future<void> setLanguageOnly(String language) async {}

  @override
  Future<String?> suggestCountryFromIp() async => null;

  @override
  Future<void> setExperience({
    required String language,
    required String country,
    required String tone,
  }) async {}
}

void main() {
  for (final size in <Size>[
    const Size(390, 844),
    const Size(768, 1024),
    const Size(1280, 900),
  ]) {
    testWidgets('Web FR step reveal, optional D7 multi-choice at $size',
        (tester) async {
      tester.view.physicalSize = size;
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      final db = AppDatabase(NativeDatabase.memory());
      final prefs = _LocalPreferences();
      final auth = AuthService();
      addTearDown(db.close);
      addTearDown(prefs.dispose);
      addTearDown(auth.dispose);
      final router = GoRouter(
        initialLocation: '/onboarding',
        routes: [
          GoRoute(
            path: '/onboarding',
            builder: (_, __) => const OnboardingChatScreen(),
          ),
          GoRoute(
            path: '/dashboard',
            builder: (_, __) => const Scaffold(body: Text('Dashboard')),
          ),
        ],
      );
      addTearDown(router.dispose);

      await tester.pumpWidget(MultiProvider(
        providers: [
          Provider<AppDatabase>.value(value: db),
          ChangeNotifierProvider<AuthService>.value(value: auth),
          ChangeNotifierProvider<LocalePreferenceService>.value(value: prefs),
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

      void expectRevealed(String key) {
        final finder = find.byKey(Key(key));
        expect(finder, findsOneWidget);
        final rect = tester.getRect(finder);
        expect(rect.top, greaterThanOrEqualTo(-1));
        expect(rect.top, lessThan(size.height - 60));
      }

      await tester.tap(find.text('Français'));
      await tester.pumpAndSettle();
      expectRevealed('onboarding-country-step');

      final search = find.byKey(const Key('onboarding-country-search'));
      await tester.tap(search);
      await tester.pumpAndSettle();
      await tester.enterText(find.byType(TextField).last, 'Maroc');
      await tester.pumpAndSettle();
      await tester.tap(find.text('Maroc').last);
      await tester.pumpAndSettle();
      expectRevealed('onboarding-type-step');

      await tester.tap(find.text('Diabète Type 2'));
      await tester.pumpAndSettle();
      expectRevealed('onboarding-treatment-step');

      final treatment = find.byKey(const Key('onboarding-treatment-step'));
      final before = tester.getRect(treatment).top;
      await tester.tap(find.byKey(const Key('d7-treatment-oral_meds')));
      await tester.pumpAndSettle();
      final after = tester.getRect(treatment).top;
      expect(after, closeTo(before, 1)); // No forced scroll after a chip.

      // The patient controls when a multi-choice declaration is finished.
      final next = find.byKey(const Key('onboarding-treatment-next'));
      await tester.ensureVisible(next);
      await tester.pumpAndSettle();
      await tester.tap(next);
      await tester.pumpAndSettle();
      expectRevealed('onboarding-unit-step');

      // No implicit completion, clinical change, or navigation on scroll.
      expect(find.byKey(const Key('onboarding-sticky-start')), findsOneWidget);
      expect(find.text('Dashboard'), findsNothing);
      expect(tester.takeException(), isNull);
    });
  }

  testWidgets('Web Arabic RTL moves to country without a keyboard jump',
      (tester) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    final db = AppDatabase(NativeDatabase.memory());
    final prefs = _LocalPreferences();
    final auth = AuthService();
    addTearDown(db.close);
    addTearDown(prefs.dispose);
    addTearDown(auth.dispose);
    final router = GoRouter(
      initialLocation: '/onboarding',
      routes: [
        GoRoute(
          path: '/onboarding',
          builder: (_, __) => const OnboardingChatScreen(),
        ),
      ],
    );
    addTearDown(router.dispose);
    await tester.pumpWidget(MultiProvider(
      providers: [
        Provider<AppDatabase>.value(value: db),
        ChangeNotifierProvider<AuthService>.value(value: auth),
        ChangeNotifierProvider<LocalePreferenceService>.value(value: prefs),
      ],
      child: MaterialApp.router(
        routerConfig: router,
        locale: const Locale('ar'),
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
    await tester.tap(find.text('العربية'));
    await tester.pumpAndSettle();
    final country = find.byKey(const Key('onboarding-country-step'));
    expect(country, findsOneWidget);
    expect(tester.getRect(country).top, inInclusiveRange(0, 720));
    expect(Directionality.of(tester.element(country)), TextDirection.rtl);
    expect(tester.takeException(), isNull);
  });
}
