import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

String _read(String path) => File(path).readAsStringSync();

Set<String> _runtimeArbKeys(String path) {
  final decoded = jsonDecode(_read(path)) as Map<String, dynamic>;
  return decoded.keys.where((key) => !key.startsWith('@')).toSet();
}

void main() {
  test('English is explicitly selectable from onboarding', () {
    final onboarding = _read('lib/features/auth/onboarding_chat_screen.dart');

    expect(onboarding, contains("label: 'English'"));
    expect(onboarding, contains("selected: _language == 'en'"));
    expect(onboarding, contains("onTap: () => _selectLanguage('en')"));
    // Immediate language selection is deliberately independent of country:
    // complete setExperience is reserved for _finish after explicit selection.
    final selectionStart = onboarding.indexOf('void _selectLanguage(');
    final finishStart = onboarding.indexOf('Future<void> _finish(');
    expect(selectionStart, greaterThanOrEqualTo(0));
    expect(finishStart, greaterThan(selectionStart));
    final selectionOnly = onboarding.substring(selectionStart, finishStart);
    expect(selectionOnly, contains('setLanguageOnly(value)'));
    expect(selectionOnly, contains('_revealStep(_countryStepKey)'));
    expect(selectionOnly, isNot(contains('setExperience(')));
    expect(selectionOnly, isNot(contains("country: _country ?? 'MA'")));
  });

  test('explicit English selection is persisted and restored deterministically', () {
    final service = _read('lib/services/locale_preference_service.dart');

    expect(service, contains("static const _languageKey = 'iamina.ui_language'"));
    expect(service, contains("static const _explicitKey = 'iamina.locale_explicitly_selected'"));
    expect(service, contains("static const _supportedLanguages = {'ar', 'en', 'fr'}"));
    expect(service, contains('_storage.write(key: _languageKey, value: locale.languageCode)'));
    expect(service, contains("_storage.write(key: _explicitKey, value: 'true')"));
    // The non-clinical UI preference now uses a fail-soft read wrapper:
    // unreadable WebCrypto bytes must not blank a previously enrolled app.
    expect(service, contains('final localLanguage = await _readUiPreference(_languageKey)'));
    expect(service, contains("final isExplicit = await _readUiPreference(_explicitKey) == 'true'"));
    expect(service, contains('return await _storage.read(key: key)'));
    expect(service, contains('} catch (error) {'));
    expect(service, contains('return null;'));
    expect(service, contains('explicitLocalLanguage: isExplicit ? localLanguage : null'));
  });

  test('French, English and Arabic expose identical runtime ARB key sets', () {
    final fr = _runtimeArbKeys('lib/l10n/app_fr.arb');
    final en = _runtimeArbKeys('lib/l10n/app_en.arb');
    final ar = _runtimeArbKeys('lib/l10n/app_ar.arb');

    expect(en, fr);
    expect(ar, fr);
  });
}
