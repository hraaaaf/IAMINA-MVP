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
    // D22 Gate A: keep local-first DB orchestration in state, but block
    // personalized KPI/AI requests until target authority is proven.
    expect(screen, isNot(contains('context.read<ApiClient>()')));
    expect(screen, isNot(contains('api.getKpis(')));
    expect(screen, isNot(contains('api.getAiSummary(')));
    expect(screen, contains('_buildD22SafetyNotice()'));
    expect(screen, contains('d22-ai-summary-target-unverified'));
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
