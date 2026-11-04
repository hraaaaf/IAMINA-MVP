import 'dart:io';

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

/// D8: synthetic Web preflight for the patient's *manual* glucose unit choice.
/// No unapproved country-to-unit map is installed or treated as a clinical rule.
class _D8LocalPreferences extends LocalePreferenceService {
  _D8LocalPreferences() : super(ApiClient(baseUrl: 'http://localhost:8000'));

  String? savedCountry;
  String? savedLanguage;
  int saveCount = 0;

  @override
  Future<String?> suggestCountryFromIp() async => null;

  @override
  Future<void> setLanguageOnly(String language) async {}

  @override
  Future<void> setExperience({
    required String language,
    required String country,
    required String tone,
  }) async {
    savedCountry = country;
    savedLanguage = language;
    saveCount += 1;
  }
}

void main() {
  test('D8: country choice and IP guess cannot secretly rewrite unit', () {
    final source =
        File('lib/features/auth/onboarding_chat_screen.dart').readAsStringSync();
    final ipStart = source.indexOf('Future<void> _suggestCountryFromIp()');
    final countryStart = source.indexOf('void _selectCountry(');
    final countryEnd = source.indexOf('void _confirmSuggestedCountry()');
    expect(ipStart, greaterThanOrEqualTo(0));
    expect(countryStart, greaterThan(ipStart));
    expect(countryEnd, greaterThan(countryStart));
    expect(source.substring(ipStart, countryEnd), isNot(contains('_unit =')));
    expect(source, contains('_unit = profile?.unitPreference ?? _unit;'));
    // The supported units remain manual, with no claimed regional authority.
    expect(source, contains("onTap: () => setState(() => _unit = 'mg/dL')"));
    expect(source, contains("onTap: () => setState(() => _unit = 'mmol/L')"));
    expect(source, isNot(contains('countryUnitDefaults')));
  });

  for (final scenario in <({
    String label,
    String language,
    String languageChoice,
    String query,
    String countryLabel,
    String countryCode,
    Size viewport,
    bool changeCountry,
  })>[
    (
      label: 'FR mobile country change does not override manually chosen mmol/L',
      language: 'fr',
      languageChoice: 'Français',
      query: 'Maroc',
      countryLabel: 'Maroc',
      countryCode: 'FR',
      viewport: Size(390, 844),
      changeCountry: true,
    ),
    (
      label: 'AR RTL mobile manually chosen mmol/L remains in patient vault',
      language: 'ar',
      languageChoice: 'العربية',
      query: 'المغر',
      countryLabel: 'المغرب',
      countryCode: 'MA',
      viewport: Size(390, 844),
      changeCountry: false,
    ),
    (
      label: 'FR desktop manually chosen mmol/L survives country selection',
      language: 'fr',
      languageChoice: 'Français',
      query: 'France',
      countryLabel: 'France',
      countryCode: 'FR',
      viewport: Size(1280, 900),
      changeCountry: false,
    ),
  ]) {
    testWidgets('D8 Web: ${scenario.label}', (tester) async {
      tester.view.physicalSize = scenario.viewport;
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      final db = AppDatabase(NativeDatabase.memory());
      final preferences = _D8LocalPreferences();
      final auth = AuthService();
      addTearDown(db.close);
      addTearDown(preferences.dispose);
      addTearDown(auth.dispose);
      final router = GoRouter(initialLocation: '/onboarding', routes: [
        GoRoute(
          path: '/onboarding',
          builder: (_, __) => const OnboardingChatScreen(),
        ),
        GoRoute(
          path: '/dashboard',
          builder: (_, __) => const Scaffold(body: Text('D8 Dashboard')),
        ),
      ]);
      addTearDown(router.dispose);

      await tester.pumpWidget(MultiProvider(
        providers: [
          Provider<AppDatabase>.value(value: db),
          ChangeNotifierProvider<AuthService>.value(value: auth),
          ChangeNotifierProvider<LocalePreferenceService>.value(
            value: preferences,
          ),
        ],
        child: MaterialApp.router(
          routerConfig: router,
          locale: Locale(scenario.language),
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

      final languageChoice = find.text(scenario.languageChoice);
      await tester.ensureVisible(languageChoice);
      await tester.pumpAndSettle();
      await tester.tap(languageChoice);
      await tester.pumpAndSettle();

      final countrySearch =
          find.byKey(const Key('onboarding-country-search'));
      await tester.ensureVisible(countrySearch);
      await tester.pumpAndSettle();
      await tester.tap(countrySearch);
      await tester.pumpAndSettle();
      await tester.enterText(find.byType(TextField).last, scenario.query);
      await tester.pumpAndSettle();
      await tester.tap(find.text(scenario.countryLabel).last);
      await tester.pumpAndSettle();

      final mmol = find.text('mmol/L');
      expect(mmol, findsOneWidget);
      await tester.ensureVisible(mmol);
      await tester.pumpAndSettle();
      await tester.tap(mmol);
      await tester.pumpAndSettle();
      if (scenario.language == 'ar') {
        expect(Directionality.of(tester.element(mmol)), TextDirection.rtl);
      }
      expect(preferences.saveCount, 0);

      if (scenario.changeCountry) {
        await tester.ensureVisible(countrySearch);
        await tester.pumpAndSettle();
        await tester.tap(countrySearch);
        await tester.pumpAndSettle();
        await tester.enterText(find.byType(TextField).last, 'France');
        await tester.pumpAndSettle();
        await tester.tap(find.text('France').last);
        await tester.pumpAndSettle();
        // The selected unit stays in the widget, even after a new country.
        final selectedMmol = find.text('mmol/L');
        expect(selectedMmol, findsOneWidget);
        expect(preferences.saveCount, 0);
      }

      final start = scenario.viewport.width < 900
          ? find.byKey(const Key('onboarding-sticky-start'))
          : find.widgetWithText(FilledButton, 'Commencer');
      await tester.ensureVisible(start);
      await tester.pumpAndSettle();
      await tester.tap(start);
      await tester.pumpAndSettle();

      expect(find.text('D8 Dashboard'), findsOneWidget);
      expect(preferences.saveCount, 1);
      expect(preferences.savedCountry, scenario.countryCode);
      expect(preferences.savedLanguage, scenario.language);
      final profile = await db.getProfileForLocalUserId(1);
      expect(profile, isNotNull);
      expect(profile!.unitPreference, 'mmol/L');
      // Deliberately no claim about target-range clinical provenance (D32).
      expect(tester.takeException(), isNull);
    });
  }
}
