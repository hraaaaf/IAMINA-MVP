import 'dart:async';

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

class _LocalPreferences extends LocalePreferenceService {
  _LocalPreferences() : super(ApiClient(baseUrl: 'http://localhost:8000'));

  // This viewport test isolates layout/navigation from secure-storage I/O.
  // The real setLanguageOnly country-write behavior is covered separately by
  // onboarding_explicit_country_boundary_test.dart with mocked storage.
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

// The IP estimate is advisory and may arrive before or after manual input.
class _PendingCountryPreferences extends _LocalPreferences {
  final Completer<String?> ipCountry = Completer<String?>();
  @override
  Future<String?> suggestCountryFromIp() => ipCountry.future;
}

Widget _w01OnboardingTestApp({
  required AppDatabase db,
  required LocalePreferenceService prefs,
  required AuthService auth,
}) {
  final router = GoRouter(
    initialLocation: '/onboarding',
    routes: [
      GoRoute(path: '/onboarding',
        builder: (_, __) => const OnboardingChatScreen()),
      GoRoute(path: '/dashboard',
        builder: (_, __) => const Scaffold(body: Text('Dashboard'))),
    ],
  );
  // The test owns router lifecycle with the outer widget tree.
  return MultiProvider(
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
  );
}

void main() {
  testWidgets('completed first use keeps Commencer fully visible at 390x844',
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
        GoRoute(path: '/onboarding', builder: (_, __) => const OnboardingChatScreen()),
        GoRoute(path: '/dashboard', builder: (_, __) => const Scaffold(body: Text('Dashboard'))),
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

    Future<void> select(String label) async {
      final choice = find.text(label);
      await tester.ensureVisible(choice);
      await tester.pumpAndSettle();
      await tester.tap(choice);
      await tester.pumpAndSettle();
    }

    await select('Français');
    final search = find.byKey(const Key('onboarding-country-search'));
    expect(search, findsOneWidget);
    await tester.tap(search);
    await tester.pumpAndSettle();
    // Validate real Flutter autocomplete filtering, not merely that a
    // country can be selected from an unfiltered alphabetical list.
    expect(find.text('Afghanistan'), findsWidgets);
    await tester.enterText(find.byType(TextField).last, 'Maroc');
    await tester.pumpAndSettle();
    expect(find.text('Maroc'), findsWidgets);
    expect(find.text('Afghanistan'), findsNothing);
    expect(find.text('France'), findsNothing);
    await tester.tap(find.text('Maroc').last);
    await tester.pumpAndSettle();
    expect(find.text('Quel ton préférez-vous ?'), findsNothing);
    await select('Diabète Type 2');
    await select('Médicaments oraux pris');

    final start = find.byKey(const Key('onboarding-sticky-start'));
    expect(start, findsOneWidget);
    expect(find.text('Commencer'), findsOneWidget);
    final rect = tester.getRect(start);
    expect(rect.top, greaterThanOrEqualTo(0));
    expect(rect.bottom, lessThanOrEqualTo(844));
    expect(tester.takeException(), isNull);

    await tester.tap(start);
    await tester.pumpAndSettle();
    expect(find.text('Dashboard'), findsOneWidget);
  });

  testWidgets('D7 patient can skip both medical choices at 390x844',
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
        GoRoute(path: '/onboarding',
            builder: (_, __) => const OnboardingChatScreen()),
        GoRoute(path: '/dashboard',
            builder: (_, __) => const Scaffold(body: Text('Dashboard'))),
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
    await tester.tap(find.text('Français'));
    await tester.pumpAndSettle();

    final search = find.byKey(const Key('onboarding-country-search'));
    await tester.tap(search);
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextField).last, 'Maroc');
    await tester.pumpAndSettle();
    await tester.tap(find.text('Maroc').last);
    await tester.pumpAndSettle();

    // Medical options are still visible, not answered or coerced to a default.
    expect(find.text('Diabète Type 2'), findsOneWidget);
    final start = find.byKey(const Key('onboarding-sticky-start'));
    expect(start, findsOneWidget);
    await tester.tap(start);
    await tester.pumpAndSettle();

    expect(find.text('Dashboard'), findsOneWidget);
    final profile = await db.getProfileForLocalUserId(1);
    expect(profile, isNotNull);
    expect(profile!.diabetesType, isNull);
    expect(profile.treatment, isNull);
    expect(tester.takeException(), isNull);
  });


  testWidgets('W01 language choice scrolls to editable IP-suggested country on iPhone',
      (tester) async {
    tester.view.physicalSize = const Size(390, 640);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final db = AppDatabase(NativeDatabase.memory());
    final prefs = _PendingCountryPreferences();
    final auth = AuthService();
    addTearDown(db.close);
    addTearDown(prefs.dispose);
    addTearDown(auth.dispose);
    await tester.pumpWidget(_w01OnboardingTestApp(
      db: db, prefs: prefs, auth: auth));
    await tester.pumpAndSettle();
    // Vercel's coarse country has arrived before the user chooses language.
    prefs.ipCountry.complete('MA');
    await tester.pumpAndSettle();

    await tester.tap(find.text('Français'));
    await tester.pumpAndSettle();
    final search = find.byKey(const Key('onboarding-country-search'));
    expect(search, findsOneWidget);
    final viewport = tester.getRect(search);
    expect(viewport.top, greaterThanOrEqualTo(0));
    expect(viewport.top, lessThan(640));
    expect(find.textContaining('Proposé selon votre connexion'), findsOneWidget);
    final field = tester.widget<TextField>(find.byType(TextField).last);
    expect(field.controller!.text, 'Maroc');

    // A prefilled estimate must never prevent the patient from changing it.
    await tester.tap(search);
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextField).last, 'France');
    await tester.pumpAndSettle();
    await tester.tap(find.text('France').last);
    await tester.pumpAndSettle();
    expect(tester.widget<TextField>(find.byType(TextField).last)
      .controller!.text, 'France');
    expect(tester.takeException(), isNull);
  });

  testWidgets('W01 late IP estimate cannot replace manual country', (tester) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final db = AppDatabase(NativeDatabase.memory());
    final prefs = _PendingCountryPreferences();
    final auth = AuthService();
    addTearDown(db.close);
    addTearDown(prefs.dispose);
    addTearDown(auth.dispose);
    await tester.pumpWidget(_w01OnboardingTestApp(
      db: db, prefs: prefs, auth: auth));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Français'));
    await tester.pumpAndSettle();
    final search = find.byKey(const Key('onboarding-country-search'));
    await tester.tap(search);
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextField).last, 'France');
    await tester.pumpAndSettle();
    await tester.tap(find.text('France').last);
    await tester.pumpAndSettle();

    prefs.ipCountry.complete('MA');
    await tester.pumpAndSettle();
    expect(tester.widget<TextField>(find.byType(TextField).last)
      .controller!.text, 'France');
    expect(find.textContaining('Proposé selon votre connexion'), findsNothing);
    expect(tester.takeException(), isNull);
  });

}
