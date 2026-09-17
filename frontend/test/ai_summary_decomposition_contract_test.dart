import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('AI summary keeps API/DB orchestration out of presentation part', () {
    final screen = File(
      'lib/features/journal/ai_summary_screen.dart',
    ).readAsStringSync();
    final presentation = File(
      'lib/features/journal/ai_summary_screen_presentation.dart',
    ).readAsStringSync();

    expect(screen, contains("part 'ai_summary_screen_presentation.dart';"));
    expect(screen, contains('class _AISummaryScreenState'));
    expect(screen, contains('context.read<ApiClient>()'));
    expect(screen, contains('context.read<AppDatabase>()'));
    expect(screen, isNot(contains('Widget _buildNarrowLayout(')));
    expect(screen, isNot(contains('Widget _buildWideLayout(')));

    expect(
      presentation,
      contains('extension _AISummaryScreenPresentation on _AISummaryScreenState'),
    );
    expect(presentation, contains('Widget _buildNarrowLayout('));
    expect(presentation, contains('Widget _buildWideLayout('));
    expect(presentation, contains('List<Widget> _buildAnalyticsSection('));
    expect(presentation, contains('List<Widget> _buildInsightsSection('));
    expect(presentation, isNot(contains('ApiClient')));
    expect(presentation, isNot(contains('AppDatabase')));
    expect(presentation, isNot(contains("import 'package:")));
  });
}
