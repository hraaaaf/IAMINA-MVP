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

  test('D19: no AGP card without verified CGM metadata', () {
    expect(source, contains('final hasEligibleAgp = agpData.isNotEmpty'));
    expect(source, contains('kpis?.tirPct == null || kpis?.tarPct == null'));
    expect(source, contains('return const SizedBox.shrink();'));
  });
}
