import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

String _readSummaryLibrary() => [
  File('lib/features/journal/ai_summary_screen.dart').readAsStringSync(),
  File('lib/features/journal/ai_summary_screen_presentation.dart').readAsStringSync(),
].join('\n');

void main() {
  test('Summary never fabricates dated discussion plans or fallback tasks', () {
    final source = _readSummaryLibrary();

    expect(source, contains('if (actionCards.isEmpty) return const SizedBox.shrink();'));
    expect(source, isNot(contains('l10n.planDay(')));
    expect(source, isNot(contains('l10n.documentCarbMeals')));
    expect(source, isNot(contains('l10n.documentNightValues')));
    expect(source, isNot(contains('l10n.prepareTirReview')));
    expect(source, isNot(contains('dayOffset =')));
  });
}
