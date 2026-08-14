import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('global render fallback follows the active locale', () {
    final mainSource = File('lib/main.dart').readAsStringSync();
    final copy = File(
      'lib/core/localization/global_localized_copy.dart',
    ).readAsStringSync();

    expect(mainSource, isNot(contains('Une erreur de rendu est survenue')));
    expect(mainSource, contains('l10n.renderErrorTitle'));
    expect(copy, contains('A rendering error occurred'));
    expect(copy, contains('Une erreur de rendu est survenue'));
    expect(copy, contains('حدث خطأ في عرض الصفحة'));
  });
}
