import 'package:amina/l10n/app_localizations.dart';
import 'package:amina/services/locale_preference_service.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('unsupported language is rejected before deterministic resolution', () {
    expect(LocalePreferenceService.supportedLocale(null), isNull);
    expect(LocalePreferenceService.supportedLocale('es-MA'), isNull);

    final fallback = LocalePreferenceService.resolveLocale(
      systemLocale: const Locale('es', 'MA'),
    );
    expect(fallback.locale.languageCode, 'fr');
    expect(fallback.source, LocaleResolutionSource.baseline);
  });

  test('confirmed languages and regional variants map independently', () {
    expect(
      LocalePreferenceService.supportedLocale('fr')?.languageCode,
      'fr',
    );
    expect(
      LocalePreferenceService.supportedLocale('en-GB')?.languageCode,
      'en',
    );
    expect(
      LocalePreferenceService.supportedLocale('ar-MA')?.languageCode,
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
