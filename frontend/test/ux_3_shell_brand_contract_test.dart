import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

String _read(String path) => File(path).readAsStringSync();

void main() {
  test('wide shell uses the canonical IAmina identity', () {
    final source = _read('lib/features/navigation/main_shell.dart');

    expect(source, contains('AppLocalizations.of(context)!.appTitle'));
    expect(source, contains('AppLocalizations.of(context)!.appSubtitle'));
    expect(source, isNot(contains('AppLocalizations.of(context)!.brandName')));
    expect(source, isNot(contains('AppLocalizations.of(context)!.brandTagShort')));
  });

  test('canonical shell identity already exists in FR EN AR catalogs', () {
    final fr = _read('lib/l10n/app_fr.arb');
    final en = _read('lib/l10n/app_en.arb');
    final ar = _read('lib/l10n/app_ar.arb');

    for (final catalog in [fr, en, ar]) {
      expect(catalog, contains('"appTitle": "IAmina"'));
    }
    expect(fr, contains('"appSubtitle": "Compagnon Diabète"'));
    expect(en, contains('"appSubtitle": "Diabetes Companion"'));
    expect(ar, contains('"appSubtitle": "رفيق داء السكري"'));
  });
}
