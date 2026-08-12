import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

String _read(String path) => File(path).readAsStringSync();

void main() {
  test('dashboard top bar has a brand-led compact composition', () {
    final source = _read('lib/features/dashboard/widgets/top_bar.dart');

    for (final required in <String>[
      'LayoutBuilder',
      'constraints.maxWidth < 760',
      '_buildCompact',
      "title: 'IAmina'",
      'subtitle: copy.overview',
      'AminaMobilePageHeader',
      'AlignmentDirectional.centerStart',
      '_ParlerButton(onTap: onChatTap, compact: true)',
      'width: 44',
      'height: 44',
    ]) {
      expect(
        source,
        contains(required),
        reason: 'Missing brand-led responsive top-bar contract: $required',
      );
    }

    expect(
      source,
      isNot(contains('Expanded(child: _ParlerButton')),
      reason: 'Compact chat access should stay a bounded icon action, not consume the range row.',
    );
  });

  test('glucose hero fits compact widths and isolates numeric direction', () {
    final source = _read('lib/features/dashboard/widgets/hero_live.dart');
    final insightSource = _read('lib/features/dashboard/widgets/hero_insight.dart');

    for (final required in <String>[
      'FittedBox',
      'BoxFit.scaleDown',
      'AlignmentDirectional.centerStart',
      r"'\u2066$displayValue\u2069'",
      r"'\u2066$unit\u2069'",
      'PositionedDirectional',
      '_HeroSparkline',
      'Expanded(',
    ]) {
      expect(
        source,
        contains(required),
        reason: 'Missing mobile/RTL hero contract: $required',
      );
    }

    for (final required in <String>[
      'HorizontalLine(',
      'y: low',
      'y: high',
      'AlignmentDirectional.centerStart',
    ]) {
      expect(
        insightSource,
        contains(required),
        reason: 'Missing truthful sparkline/reference contract: $required',
      );
    }
  });

  test('mobile dashboard metrics stay compact and CGM metrics fail closed', () {
    final source = _read('lib/features/dashboard/widgets/kpi_cards.dart');

    for (final required in <String>[
      "value: '--'",
      'dashboardInsufficientData',
      '_CompactMetricCell',
      'IntrinsicHeight',
      'final cv = ClinicalEngine.calcCV(logs)',
      'accent: AminaTheme.teal600',
    ]) {
      expect(
        source,
        contains(required),
        reason: 'Missing compact/fail-closed metric contract: $required',
      );
    }

    expect(
      source,
      isNot(contains('ClinicalEngine.calcGMI(logs)')),
      reason: 'Compact dashboard must not derive GMI from mixed/manual local logs.',
    );
    expect(
      source,
      isNot(contains('dashboardGmiLimitedCoverage')),
      reason: 'Compact dashboard must not claim row-count coverage makes CGM GMI eligible.',
    );
    expect(
      source,
      isNot(contains('cv < 36')),
      reason: 'Compact dashboard must not apply a normative CGM CV threshold locally.',
    );
  });

  test('mobile add action has a bounded accessible footprint', () {
    final source = _read('lib/features/dashboard/widgets/speed_dial.dart');

    expect(source, contains('AuditedPageCopy.of(context).l10n.addEntry'));
    expect(source, contains('message: label'));
    expect(source, contains('label: label'));
    expect(source, isNot(contains("label: 'Ajouter une entrée'")));
    expect(source, contains('width: 60'));
    expect(source, contains('width: 48'));
    expect(source, contains('AlignmentDirectional.topStart'));
    expect(source, isNot(contains('width: 76')));
    expect(source, isNot(contains('width: 56 + ripple * 20')));
  });
}
