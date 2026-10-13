import 'dart:io';

import 'package:amina/services/country_choices.dart';
import 'package:amina/services/api_client.dart';
import 'package:amina/services/locale_preference_service.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('country picker includes 249 ISO countries and no OTHER', () {
    expect(countryChoices.length, 249);
    expect(countryChoices.map((c) => c.code).toSet().length, 249);
    expect(countryByCode('ma')!.label('fr'), 'Maroc');
    expect(countryByCode('FR')!.label('ar'), 'فرنسا');
    expect(countryByCode('OTHER'), isNull);
    expect(countryByCode('ZZ'), isNull);
  });

  test('unknown country never persisted, explicit ISO remains editable', () async {
    FlutterSecureStorage.setMockInitialValues({});
    const storage = FlutterSecureStorage();
    final service = LocalePreferenceService(ApiClient(), storage: storage);
    await service.setLanguageOnly('fr');
    expect(service.country, isNull);
    expect(await storage.read(key: 'iamina.country'), isNull);
    await expectLater(
      service.setExperience(language: 'fr', country: 'OTHER', tone: 'neutral'),
      throwsArgumentError,
    );
    expect(await storage.read(key: 'iamina.country'), isNull);
    await service.setExperience(language: 'fr', country: 'gb', tone: 'neutral');
    expect(service.country, 'GB');
    expect(await storage.read(key: 'iamina.country'), 'GB');
    service.dispose();
  });

  test('onboarding contains searchable country input rather than chips', () {
    final code = File('lib/features/auth/onboarding_chat_screen.dart')
        .readAsStringSync();
    expect(code, contains('DropdownMenu<CountryChoice>'));
    expect(code, contains("Key('onboarding-country-search')"));
    expect(code, contains('suggestCountryFromIp()'));
    expect(code, isNot(contains('onboardingCountryMorocco')));
    expect(code, isNot(contains('onboardingCountryFrance')));
    expect(code, isNot(contains('onboardingCountryOther')));
  });
}
