import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

String source(String path) => File('lib/$path').readAsStringSync();

void main() {
  test('D22 Gate A keeps historic targets unverified and uneditable', () {
    final onboard = source('features/auth/onboarding_chat_screen.dart');
    final profile = source('features/profile/profile_screen.dart');
    final ui = source('features/profile/profile_screen_presentation.dart');

    expect(onboard, isNot(contains('targetRangeLow: const drift.Value(70)')));
    expect(onboard, isNot(contains('targetRangeHigh: const drift.Value(180)')));
    expect(profile, contains('getProfileForLocalUserId(userId)'));
    expect(profile, contains('bool get _d22TargetsEditable => false'));
    expect(profile, isNot(contains('targetRangeLow: drift.Value(')));
    expect(profile, isNot(contains('targetRangeHigh: drift.Value(')));
    expect(ui, contains('d22-unverified-target-blocked'));
    expect(ui, contains('Objectifs non vérifiés'));
    expect(ui, contains('الأهداف غير مؤكدة'));
  });

  test('D22 Gate A removes target-based classifications from history', () {
    final dashboard = source('features/dashboard/dashboard_screen.dart');
    final premium = source('features/dashboard/dashboard_premium_screen.dart');
    final journal = source('features/journal/journal_screen.dart');
    final recent = source('features/dashboard/widgets/recent_entries.dart');
    final reports = source('features/journal/reports_screen_presentation.dart');

    expect(dashboard, contains('d22-manual-tir-unavailable'));
    expect(dashboard, isNot(contains('_fetchAiSummary()')));
    expect(dashboard, isNot(contains('api.getAiSummary(')));
    expect(premium, contains('const double? low = null;'));
    expect(premium, contains('child: Container('));
    final hero = source('features/dashboard/widgets/hero_section.dart');
    expect(hero, contains('Optional Firebase auth must not crash'));
    expect(journal, contains('final color = AminaTheme.textPrimary(context);'));
    expect(recent, isNot(contains('_valueColor(')));
    expect(reports, contains('const double? low = null;'));
    expect(reports, contains('const double? high = null;'));
    expect(reports, contains('Targets unverified: distribution unavailable.'));
  });

  test('D22 Gate A blocks ungoverned AI/KPI summary network requests', () {
    final summary = source('features/journal/ai_summary_screen.dart');
    final today = source('features/dashboard/widgets/dashboard_today_section.dart');

    expect(summary, contains('d22-ai-summary-target-unverified'));
    expect(summary, isNot(contains('api.getKpis(')));
    expect(summary, isNot(contains('api.getAiSummary(')));
    expect(summary, contains('Personalized analysis is temporarily unavailable'));
    expect(today, contains('Glucose targets unverified.'));
    expect(today, contains('return signals;'));
  });

  test('D22 Gate A does not label manual rows as CGM time in range', () {
    final engine = source('features/dashboard/clinical_engine.dart');
    expect(engine, contains('CGM TIR requires verified timed CGM source'));
    expect(engine, contains('throw UnsupportedError('));
  });
}
