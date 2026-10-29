import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  final source = File(
    'lib/features/journal/ai_summary_screen_presentation.dart',
  ).readAsStringSync();

  test('D19: manual daily averages cannot become a clinical CGM AGP', () {
    expect(source, contains('final agpData = summary.agpProfile;'));
    expect(source, isNot(contains(': summary.dailyAverages;')));
    expect(source, contains('if (hasEligibleAgp)'));
    expect(source, contains('kpis?.tirPct != null'));
    expect(source, contains('kpis?.tarPct != null'));
    expect(source, contains('kpis?.tbrPct != null'));
  });

  test('D19: missing CGM metric is never rendered as invented zero', () {
    expect(source, contains('tir == null'));
    expect(source, contains('l10n.insufficientData'));
    expect(source, contains('if (kpis.tirPct != null)'));
    expect(source, contains('if (kpis.gmi != null)'));
    expect(source, contains('if (kpis.cvPct != null)'));
    expect(source, isNot(contains('kpis.tirPct ?? 0.0')));
    expect(source, isNot(contains('kpis.gmi ?? 0.0')));
    expect(source, isNot(contains('kpis.cvPct ?? 0.0')));
    expect(source, contains('if (cards.isEmpty) return const SizedBox.shrink();'));
  });

  test('D19: AI Summary greeting remains available without Firebase app', () {
    // Local-only sessions do not initialize optional Firebase migration.
    expect(source, contains('Optional Firebase migration identity must never gate'));
    expect(source, contains('FirebaseAuth.instance.currentUser'));
    expect(source, contains('} catch (_) {'));
  });

  test('D19: hero actions fit mobile and are keyboard focusable', () {
    expect(source, contains('if (constraints.maxWidth < 430)'));
    expect(source, contains('crossAxisAlignment: CrossAxisAlignment.stretch'));
    expect(source, contains('return InkWell('));
  });

  test('D19: Arabic first-use report uses a bundled offline font', () {
    expect(source, contains('fontFamilyFallback: kOfflineFontFallbacks'));
    expect(source, contains("'NotoSansArabic'"));
  });

  test('D19: the shared first-use AR secondary CTA uses local glyphs', () {
    final shared = File('lib/core/widgets/first_use_panel.dart').readAsStringSync();
    expect(shared, contains('secondaryActionLabel!'));
    expect(shared, contains('fontFamilyFallback: kOfflineFontFallbacks'));
    expect(shared, contains("'NotoSansArabic'"));
  });

  test('D19: no AGP card without verified CGM metadata', () {
    expect(source, contains('final hasEligibleAgp = agpData.isNotEmpty'));
    expect(source, contains('kpis?.tirPct == null || kpis?.tarPct == null'));
    expect(source, contains('return const SizedBox.shrink();'));
  });
}
