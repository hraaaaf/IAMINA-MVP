import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('Companion keeps service orchestration out of presentation part', () {
    final state = File(
      'lib/features/companion/companion_premium_screen.dart',
    ).readAsStringSync();
    final presentation = File(
      'lib/features/companion/companion_premium_screen_presentation.dart',
    ).readAsStringSync();

    expect(state, contains("part 'companion_premium_screen_presentation.dart';"));
    expect(state, contains('class _CompanionPremiumScreenState'));
    expect(state, contains('CompanionService'));
    expect(state, contains('void _reload()'));
    expect(state, contains('fetchOverview()'));
    expect(state, isNot(contains('class _Shell')));
    expect(state, isNot(contains('class _Overview')));
    expect(state, isNot(contains('class _SafetyCard')));
    expect(state, isNot(contains('class _PatternCard')));

    expect(presentation, contains('class _Shell'));
    expect(presentation, contains('class _Overview'));
    expect(presentation, contains('class _SafetyCard'));
    expect(presentation, contains('class _PatternCard'));
    expect(presentation, isNot(contains('fetchOverview()')));
    expect(presentation, isNot(contains("import 'package:")));
  });
}
