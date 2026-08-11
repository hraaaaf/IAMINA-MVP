import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('onboarding copy exists in every supported ARB locale', () {
    const keys = <String>[
      'onboardingChooseLanguage',
      'onboardingChooseCountry',
      'onboardingChooseTone',
      'onboardingTypeQuestion',
      'onboardingTreatmentQuestion',
      'onboardingUnitQuestion',
      'onboardingReady',
      'onboardingStart',
    ];

    for (final locale in <String>['fr', 'en', 'ar']) {
      final data =
          jsonDecode(File('lib/l10n/app_$locale.arb').readAsStringSync())
              as Map<String, dynamic>;
      for (final key in keys) {
        expect(data[key], isA<String>(), reason: '$locale is missing $key');
        expect((data[key] as String).trim(), isNotEmpty);
      }
    }
  });
}
