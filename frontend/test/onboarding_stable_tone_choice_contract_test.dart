import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('V1 #6 removes both user tone selectors and uses five progression steps', () {
    final onboarding = File(
      'lib/features/auth/onboarding_chat_screen.dart',
    ).readAsStringSync();
    expect(onboarding, contains('onboardingChooseCountry'));
    expect(onboarding, contains('onboardingTypeQuestion'));
    // D7 has replaced the old treatment question with declared-treatment copy.
    expect(onboarding, contains('MedicalTreatmentMultiSelector('));
    expect(onboarding, contains('onboardingUnitQuestion'));
    expect(onboarding, isNot(contains('onboardingChooseTone')));
    expect(onboarding, isNot(contains('onboardingToneNeutral')));
    expect(onboarding, isNot(contains('onboardingToneFriendly')));
    expect(onboarding, isNot(contains('_tone')));
    expect(onboarding, contains('return (current: current, total: 5);'));
    expect(onboarding, contains("tone: 'neutral'"));
    expect(onboarding, contains('setLanguageOnly(value)'));
    expect(onboarding, contains('country: _country!'));
  });

  test('V1 #6 updates profile copy in FR EN AR, leaves technical legacy storage', () {
    final profile = File(
      'lib/features/profile/profile_screen_presentation.dart',
    ).readAsStringSync();
    expect(profile, contains('Langue et pays. Vos réglages'));
    expect(profile, contains('Language and country. Medical settings'));
    expect(profile, contains('اللغة والبلد. تبقى الإعدادات'));
    expect(profile, isNot(contains('Langue, pays et ton')));
    expect(profile, isNot(contains('Language, country and tone')));
    final legacy = File(
      'lib/services/locale_preference_service.dart',
    ).readAsStringSync();
    expect(legacy, contains("static const _toneKey = 'iamina.local_tone';"));
  });
}
