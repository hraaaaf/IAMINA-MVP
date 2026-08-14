import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

String _read(String path) => File(path).readAsStringSync();

void main() {
  test('global rendering fallback follows the active locale', () {
    final main = _read('lib/main.dart');
    final copy = _read('lib/core/localization/app_shell_localized_copy.dart');

    expect(main, contains('app_shell_localized_copy.dart'));
    expect(main, contains('AppLocalizations.of(context)!.renderError'));
    expect(main, isNot(contains("'Une erreur de rendu est survenue'")));

    expect(copy, contains("en: 'A rendering error occurred'"));
    expect(copy, contains("fr: 'Une erreur de rendu est survenue'"));
    expect(copy, contains("ar: 'حدث خطأ أثناء عرض الواجهة'"));
  });
}
