import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('audited page copy contains no embedded translations', () {
    final source = File('lib/l10n/audited_page_copy.dart').readAsStringSync();
    expect(source, contains('AppLocalizations'));
    expect(source, isNot(contains('String pick(')));
    expect(source, isNot(contains("fr:")));
    expect(source, isNot(contains("en:")));
    expect(source, isNot(contains("ar:")));
  });
}
