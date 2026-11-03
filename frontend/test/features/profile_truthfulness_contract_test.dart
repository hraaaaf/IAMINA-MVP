import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

String _read(String path) => File(path).readAsStringSync();

String _readProfileLibrary() => [
  _read('lib/features/profile/profile_screen.dart'),
  _read('lib/features/profile/profile_screen_presentation.dart'),
].join('\n');

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

  test('D22 profile saves declared fields without requiring unknown targets', () {
    final source = _read('lib/features/profile/profile_screen.dart');

    expect(source, contains('final diabetesType = _diabetesType;'));
    expect(source, contains('final treatment = _treatment;'));
    expect(source, contains('drift.Value(diabetesType)'));
    expect(source, contains('drift.Value(treatment)'));
    final save = source.substring(source.indexOf('void _saveProfile()'));
    final writeScope = save.substring(0, save.indexOf('bool remoteMirrorConfirmed'));
    expect(writeScope, isNot(contains('targetRangeLow:')));
    expect(writeScope, isNot(contains('targetRangeHigh:')));
    expect(writeScope, contains('db.update(db.patientProfiles)'));
    expect(source, contains('bool get _d22TargetsEditable => false;'));
  });

  test('profile persists the active locale and keeps FR EN AR choice available', () {
    final profile = _readProfileLibrary();
    final onboarding = _read('lib/features/auth/onboarding_chat_screen.dart');

    expect(profile, isNot(contains("preferredLanguage: const drift.Value('fr')")));
    expect(profile, contains('Localizations.localeOf(context).languageCode'));
    expect(profile, contains("context.push('/preferences')"));
    expect(onboarding, contains('final bool preferencesOnly;'));
    expect(onboarding, contains('widget.preferencesOnly ? preferenceSteps : onboardingSteps'));
    expect(onboarding, contains('if (widget.preferencesOnly)'));
    expect(onboarding, contains("_selectLanguage('fr')"));
    expect(onboarding, contains("_selectLanguage('en')"));
    expect(onboarding, contains("_selectLanguage('ar')"));
  });
}
