import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('AI summary keeps orchestration in state and UI classes in presentation', () {
    final state = File(
      'lib/features/journal/ai_summary_screen.dart',
    ).readAsStringSync();
    final presentation = File(
      'lib/features/journal/ai_summary_screen_presentation.dart',
    ).readAsStringSync();

    expect(state, contains("part 'ai_summary_screen_presentation.dart';"));
    expect(state, contains('class _AISummaryScreenState'));
    expect(state, contains('context.read<AppDatabase>()'));
    expect(state, contains('context.read<ApiClient>()'));
    expect(state, contains('Future<void> _fetchData()'));
    expect(state, isNot(contains('class _SummaryTopBar')));
    expect(state, isNot(contains('class _HeroInsightCard')));
    expect(state, isNot(contains('class _KpiCard')));
    expect(state, isNot(contains('class _InsightCardWidget')));
    expect(state, isNot(contains('class _ChatFab')));

    expect(
      presentation,
      contains('extension _AISummaryScreenPresentation on _AISummaryScreenState'),
    );
    expect(presentation, contains('class _SummaryTopBar'));
    expect(presentation, contains('class _HeroInsightCard'));
    expect(presentation, contains('class _KpiCard'));
    expect(presentation, contains('class _InsightCardWidget'));
    expect(presentation, contains('class _ChatFab'));
    expect(presentation, isNot(contains("import 'package:")));
  });
}
