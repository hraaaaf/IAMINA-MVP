import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

String _read(String path) => File(path).readAsStringSync();

void main() {
  test('dashboard top bar has an explicit compact composition', () {
    final source = _read('lib/features/dashboard/widgets/top_bar.dart');

    for (final required in <String>[
      'LayoutBuilder',
      'constraints.maxWidth < 760',
      '_buildCompact',
      'maxLines: 1',
      'TextOverflow.ellipsis',
      'EdgeInsetsDirectional.fromSTEB',
      'Expanded(child: _ParlerButton',
    ]) {
      expect(
        source,
        contains(required),
        reason: 'Missing responsive top-bar contract: $required',
      );
    }

    expect(
      source,
      isNot(contains('Expanded(\n              child: RichText')),
      reason: 'The old single-row breadcrumb composition must not return.',
    );
  });

  test('glucose hero fits compact widths and isolates numeric direction', () {
    final source = _read('lib/features/dashboard/widgets/hero_live.dart');

    for (final required in <String>[
      'constraints.maxWidth < 600',
      'FittedBox',
      'BoxFit.scaleDown',
      'AlignmentDirectional.centerStart',
      r"'\u2066$displayValue\u2069'",
      r"'\u2066$unit\u2069'",
      'if (!compact)',
      'fontSize: compact ? 68 : 88',
      'PositionedDirectional',
    ]) {
      expect(
        source,
        contains(required),
        reason: 'Missing mobile/RTL hero contract: $required',
      );
    }

    expect(
      source,
      isNot(contains('const Spacer()')),
      reason: 'The fixed hero spacer caused mobile clipping.',
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
