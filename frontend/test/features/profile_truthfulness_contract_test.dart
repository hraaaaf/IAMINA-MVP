import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

String _read(String path) => File(path).readAsStringSync();

void main() {
  test('new profile does not preselect medical facts or inject target defaults', () {
    final source = _read('lib/features/profile/profile_screen.dart');

    expect(source, contains('String? _diabetesType;'));
    expect(source, contains('String? _treatment;'));
    expect(source, isNot(contains("String _diabetesType = 'type1'")));
    expect(source, isNot(contains("String _treatment = 'insulin'")));
    expect(source, isNot(contains("profile.diabetesType ?? 'type1'")));
    expect(source, isNot(contains("profile.treatment ?? 'insulin'")));
    expect(source, isNot(contains('?? 70.0')));
    expect(source, isNot(contains('?? 180.0')));
  });

  test('profile save requires explicit medical selections and a valid range', () {
    final source = _read('lib/features/profile/profile_screen.dart');

    expect(source, contains('final diabetesType = _diabetesType;'));
    expect(source, contains('final treatment = _treatment;'));
    expect(source, contains('final validRange ='));
    expect(source, contains('low.isFinite'));
    expect(source, contains('high.isFinite'));
    expect(source, contains('low > 0'));
    expect(source, contains('high > 0'));
    expect(source, contains('low < high'));
    expect(
      source,
      contains('if (diabetesType == null || treatment == null || !validRange)'),
    );
    expect(source, contains('drift.Value(diabetesType)'));
    expect(source, contains('drift.Value(treatment)'));
  });

  test('profile persists the active locale and keeps FR EN AR choice available', () {
    final profile = _read('lib/features/profile/profile_screen.dart');
    final onboarding = _read('lib/features/auth/onboarding_chat_screen.dart');

    expect(profile, isNot(contains("preferredLanguage: const drift.Value('fr')")));
    expect(profile, contains('Localizations.localeOf(context).languageCode'));
    expect(profile, contains("context.push('/onboarding')"));
    expect(onboarding, contains("_selectLanguage('fr')"));
    expect(onboarding, contains("_selectLanguage('en')"));
    expect(onboarding, contains("_selectLanguage('ar')"));
  });
}
