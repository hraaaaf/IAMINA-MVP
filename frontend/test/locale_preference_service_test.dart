import 'package:amina/l10n/app_localizations.dart';
import 'package:amina/services/locale_preference_service.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('unknown or missing language fails closed to French', () {
    expect(
      LocalePreferenceService.localeFromResolvedLanguage(null).languageCode,
      'fr',
    );
    expect(
      LocalePreferenceService.localeFromResolvedLanguage('ar-MA').languageCode,
      'fr',
    );
  });

  test('confirmed baseline languages map independently', () {
    expect(
      LocalePreferenceService.localeFromResolvedLanguage('fr').languageCode,
      'fr',
    );
    expect(
      LocalePreferenceService.localeFromResolvedLanguage('en').languageCode,
      'en',
    );
    expect(
      LocalePreferenceService.localeFromResolvedLanguage('ar').languageCode,
      'ar',
    );
  });

  testWidgets('Arabic locale produces RTL directionality', (tester) async {
    TextDirection? direction;

    await tester.pumpWidget(
      MaterialApp(
        locale: const Locale('ar'),
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        supportedLocales: AppLocalizations.supportedLocales,
        home: Builder(
          builder: (context) {
            direction = Directionality.of(context);
            return const SizedBox.shrink();
          },
        ),
      ),
    );

    expect(direction, TextDirection.rtl);
  });
}
