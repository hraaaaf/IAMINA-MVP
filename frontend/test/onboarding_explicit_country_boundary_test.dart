import 'dart:io';

import 'package:amina/services/api_client.dart';
import 'package:amina/services/locale_preference_service.dart';
import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() => FlutterSecureStorage.setMockInitialValues({}));

  test('selecting onboarding language never writes a guessed country', () async {
    const storage = FlutterSecureStorage();
    final service = LocalePreferenceService(
      ApiClient(),
      storage: storage,
      systemLocale: const Locale('fr'),
    );

    await service.setLanguageOnly('ar');
    expect(service.locale, const Locale('ar'));
    expect(service.resolutionSource, LocaleResolutionSource.explicitLocal);
    expect(await storage.read(key: 'iamina.ui_language'), 'ar');
    expect(await storage.read(key: 'iamina.country'), isNull);
    expect(await storage.read(key: 'iamina.local_tone'), isNull);

    // Only finishing all explicit onboarding choices may persist a country.
    await service.setExperience(
      language: 'ar', country: 'FR', tone: 'neutral',
    );
    expect(await storage.read(key: 'iamina.country'), 'FR');

    // Changing language again never overwrites the actual selected country.
    await service.setLanguageOnly('en');
    expect(await storage.read(key: 'iamina.ui_language'), 'en');
    expect(await storage.read(key: 'iamina.country'), 'FR');
    expect(await storage.read(key: 'iamina.local_tone'), 'neutral');
  });

  test('unsupported language never mutates local selection state', () async {
    const storage = FlutterSecureStorage();
    final service = LocalePreferenceService(
      ApiClient(), storage: storage, systemLocale: const Locale('fr'),
    );
    await expectLater(
      service.setLanguageOnly('es'),
      throwsArgumentError,
    );
    expect(await storage.read(key: 'iamina.ui_language'), isNull);
    expect(await storage.read(key: 'iamina.country'), isNull);
  });

  test('onboarding code never uses implicit MA while choosing only language', () {
    final source = File(
      'lib/features/auth/onboarding_chat_screen.dart',
    ).readAsStringSync();
    final first = source.indexOf('Future<void> _selectLanguage(');
    final last = source.indexOf('Future<void> _finish(');
    expect(first, greaterThanOrEqualTo(0));
    expect(last, greaterThan(first));
    final selection = source.substring(first, last);
    expect(selection, contains('setLanguageOnly(value)'));
    expect(selection, isNot(contains("country: _country ?? 'MA'")));
    expect(source, contains('country: _country!'));
  });
}
