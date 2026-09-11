import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('multi-day trend uses daily observed ranges instead of dot clouds', () {
    final painter = File(
      'lib/features/dashboard/widgets/dashboard_trend_painter.dart',
    ).readAsStringSync();
    final copy = File(
      'lib/core/localization/dashboard_trend_localized_copy.dart',
    ).readAsStringSync();

    expect(painter, contains("static const Duration _rawPointWindow = Duration(hours: 36)"));
    expect(painter, contains('bool get _useDailyRanges'));
    expect(painter, contains('_paintDailyRanges'));
    expect(painter, contains('_paintRecordedPoints'));
    expect(painter, contains('final minValue = values.reduce(math.min)'));
    expect(painter, contains('final maxValue = values.reduce(math.max)'));
    expect(painter, isNot(contains('_paintRecordedTrajectory')));
    expect(painter, isNot(contains('curveTo')));
    expect(copy, contains('plage minimale–maximale observée'));
    expect(copy, contains('Aucune ligne ni valeur manquante n’est inventée'));
  });
}
