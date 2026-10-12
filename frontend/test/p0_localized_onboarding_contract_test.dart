import 'dart:io';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test(
    'onboarding keeps explicit language and country without a tone picker',
    () {
      final source = File(
        'lib/features/auth/onboarding_chat_screen.dart',
      ).readAsStringSync();
      expect(source, contains('onboardingChooseLanguage'));
      expect(source, contains('onboardingChooseCountry'));
      expect(source, isNot(contains('onboardingChooseTone')));
      expect(source, contains('preferredLanguage: drift.Value(_language!)'));
      expect(
        source,
        isNot(contains("preferredLanguage: const drift.Value('fr')")),
      );
    },
  );

  test('locale preference persists pre-auth experience locally', () {
    final source = File(
      'lib/services/locale_preference_service.dart',
    ).readAsStringSync();
    expect(source, contains('FlutterSecureStorage'));
    expect(source, contains('iamina.ui_language'));
    expect(source, contains('iamina.country'));
    expect(source, contains('iamina.local_tone'));
    expect(source, contains('setExperience'));
  });
}
