import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  final source = File(
    'lib/features/navigation/main_shell.dart',
  ).readAsStringSync();

  test('sidebar separation follows text direction', () {
    expect(source, contains('BorderDirectional('));
    expect(source, contains('end: BorderSide('));
    expect(source, isNot(contains('Border(right:')));
  });

  test('compact navigation controls expose names and 44 px targets', () {
    expect(source, contains('Semantics('));
    expect(source, contains('button: true'));
    expect(source, contains('selected: selected'));
    expect(source, contains('BoxConstraints(minHeight: 44)'));
  });

  test('mobile navigation labels remain permanently visible', () {
    expect(source, contains('class _GlassNavDestination'));
    expect(
      source,
      contains('final label = entry.label(AppLocalizations.of(context)!);'),
    );
    expect(source, contains('child: Text('));
    expect(source, contains('maxLines: 1'));
    expect(
      source,
      isNot(contains('NavigationDestinationLabelBehavior.onlyShowSelected')),
    );
  });

  test('navigation copy comes from canonical localizations', () {
    expect(source, contains('AppLocalizations.of(context)!.addEntry'));
    expect(source, isNot(contains("'Ajouter'")));
    expect(source, isNot(contains("'Utilisateur'")));
  });

  test('critical sidebar labels can wrap instead of being truncated', () {
    expect(source, contains('maxLines: 2'));
    expect(source, contains('softWrap: true'));
  });
}
