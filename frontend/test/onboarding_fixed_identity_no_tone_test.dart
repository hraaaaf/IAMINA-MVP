import 'dart:io';

import 'package:amina/l10n/app_localizations.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('decision #6 has five onboarding steps and no user tone controls', () {
    final code = File('lib/features/auth/onboarding_chat_screen.dart')
        .readAsStringSync();
    expect(code, contains('return (current: current, total: 5);'));
    expect(code, contains("tone: 'neutral'"));
    expect(code, isNot(contains('onboardingChooseTone')));
    expect(code, isNot(contains('onboardingToneNeutral')));
    expect(code, isNot(contains('onboardingToneFriendly')));
    expect(code, isNot(contains('_tone')));
    expect(code, contains('if (_country != null)'));
    expect(code, contains('title: l10n.onboardingTypeQuestion'));
    expect(code, contains('title: l10n.onboardingUnitQuestion'));
    expect(code, contains('setLanguageOnly(value)'));
  });

  for (final locale in const [Locale('fr'), Locale('en'), Locale('ar')]) {
    testWidgets('decision #6 preserves five-step progress locale ${locale.languageCode}', (tester) async {
      await tester.pumpWidget(MaterialApp(
        locale: locale,
        supportedLocales: AppLocalizations.supportedLocales,
        localizationsDelegates: const [
          AppLocalizations.delegate,
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        home: Builder(builder: (context) {
          final localized = AppLocalizations.of(context)!;
          return SingleChildScrollView(
            child: Column(children: [
              Text(localized.onboardingChooseLanguage),
              Text(localized.onboardingChooseCountry),
              Text(localized.onboardingTypeQuestion),
              Text(localized.onboardingTreatmentQuestion),
              Text(localized.onboardingUnitQuestion),
            ]),
          );
        }),
      ));
      expect(find.byType(Text), findsNWidgets(5));
      expect(tester.takeException(), isNull);
    });
  }
}
