import 'package:amina/l10n/app_localizations_ar.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('Arabic nutrition ranges isolate the numeric span in LTR order', () {
    final text = AppLocalizationsAr().journalNutritionCarbsRange('22.1', '26.4');
    expect(text, contains('\u206622.1–26.4\u2069'));
    expect(text, isNot(contains('26.4–22.1')));
  });
}
