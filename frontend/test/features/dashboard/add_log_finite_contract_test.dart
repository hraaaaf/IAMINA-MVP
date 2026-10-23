import 'package:amina/features/dashboard/widgets/add_log_sheet.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('decision #12 no patient glucose is ever prefilled or guessed', () {
    for (final value in ['', ' ', 'not-a-reading', '0', '-1']) {
      expect(parsePositiveFiniteGlucoseInput(value), isNull);
      expect(normalizeFiniteGlucoseMgdl(value, 'mg/dL'), isNull);
    }
  });

  test('decision #12 rejects NaN, infinities and overflow in both units', () {
    for (final value in ['NaN', 'Infinity', '-Infinity', '1e999']) {
      expect(parsePositiveFiniteGlucoseInput(value), isNull);
      for (final unit in ['mg/dL', 'mmol/L']) {
        expect(normalizeFiniteGlucoseMgdl(value, unit), isNull);
      }
    }
    // Finite input can still overflow during mmol/L conversion.
    expect(
      normalizeFiniteGlucoseMgdl('1e308', 'mmol/L'),
      isNull,
    );
    expect(
      normalizeFiniteGlucoseMgdl('1e308', 'mg/dL'),
      1e308,
    );
  });

  test('decision #12 preserves existing valid inputs and unit conversion', () {
    expect(parsePositiveFiniteGlucoseInput(' 5,5 '), 5.5);
    expect(normalizeFiniteGlucoseMgdl('5,5', 'mmol/L'), 99.0);
    expect(normalizeFiniteGlucoseMgdl('126', 'mg/dL'), 126.0);
    expect(normalizeFiniteGlucoseMgdl('126', 'g/L'), isNull);
    expect(normalizeFiniteGlucoseMgdl('', 'mmol/L'), isNull);
  });
}
