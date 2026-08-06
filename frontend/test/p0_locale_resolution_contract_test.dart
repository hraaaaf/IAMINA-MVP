import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:iamina/services/locale_preference_service.dart';

void main() {
  group('locale normalization', () {
    test('accepts supported regional locale variants', () {
      expect(
        LocalePreferenceService.supportedLocale('ar-MA'),
        const Locale('ar'),
      );
      expect(
        LocalePreferenceService.supportedLocale('fr_FR'),
        const Locale('fr'),
      );
      expect(
        LocalePreferenceService.supportedLocale(const Locale('en', 'GB')),
        const Locale('en'),
      );
    });

    test('rejects unsupported and malformed values', () {
      expect(LocalePreferenceService.supportedLocale('es-MA'), isNull);
      expect(LocalePreferenceService.supportedLocale(''), isNull);
      expect(LocalePreferenceService.supportedLocale(null), isNull);
    });
  });

  group('deterministic precedence', () {
    test('audit locale has absolute priority', () {
      final result = LocalePreferenceService.resolveLocale(
        auditLocale: const Locale('ar'),
        explicitLocalLanguage: 'en',
        accountLanguage: 'fr',
        storedLocalLanguage: 'fr',
        systemLocale: const Locale('en'),
      );
      expect(result.locale, const Locale('ar'));
      expect(result.source, LocaleResolutionSource.audit);
    });

    test('explicit device choice overrides account preference', () {
      final result = LocalePreferenceService.resolveLocale(
        explicitLocalLanguage: 'ar-MA',
        accountLanguage: 'fr',
        storedLocalLanguage: 'en',
        systemLocale: const Locale('fr'),
      );
      expect(result.locale, const Locale('ar'));
      expect(result.source, LocaleResolutionSource.explicitLocal);
    });

    test('account preference overrides non-explicit cache and system', () {
      final result = LocalePreferenceService.resolveLocale(
        accountLanguage: 'en-US',
        storedLocalLanguage: 'ar',
        systemLocale: const Locale('fr'),
      );
      expect(result.locale, const Locale('en'));
      expect(result.source, LocaleResolutionSource.account);
    });

    test('falls through invalid values without silently accepting them', () {
      final result = LocalePreferenceService.resolveLocale(
        explicitLocalLanguage: 'es',
        accountLanguage: 'de',
        storedLocalLanguage: 'ar-MA',
        systemLocale: const Locale('en'),
      );
      expect(result.locale, const Locale('ar'));
      expect(result.source, LocaleResolutionSource.storedLocal);
    });

    test('uses supported system locale then deterministic French baseline', () {
      final system = LocalePreferenceService.resolveLocale(
        systemLocale: const Locale('ar', 'MA'),
      );
      expect(system.locale, const Locale('ar'));
      expect(system.source, LocaleResolutionSource.system);

      final baseline = LocalePreferenceService.resolveLocale(
        systemLocale: const Locale('es', 'ES'),
      );
      expect(baseline.locale, const Locale('fr'));
      expect(baseline.source, LocaleResolutionSource.baseline);
    });
  });
}
