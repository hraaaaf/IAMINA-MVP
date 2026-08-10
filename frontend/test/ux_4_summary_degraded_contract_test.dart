import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('UX-4 keeps degraded Summary integrated into the page shell', () {
    final source = File(
      'lib/features/journal/ai_summary_screen.dart',
    ).readAsStringSync();

    expect(
      source,
      contains('constraints: BoxConstraints(maxWidth: isWide ? 960 : 520)'),
    );
    expect(source, contains('_GreetingHeader(periodDays: _periodDays)'));
    expect(source, contains('AlignmentDirectional.topStart'));
    expect(source, contains('liveRegion: true'));
    expect(source, contains('l10n.analysisLoadError'));
    expect(source, contains('label: Text(l10n.retry)'));
    expect(
      source,
      contains("final periodLabel = '\$_periodDays \${l10n.dayShort}';"),
    );
    expect(source, isNot(contains('const Alignment(0, -0.30)')));
    expect(source, isNot(contains('maxWidth: isWide ? 480 : 420')));
  });
}
