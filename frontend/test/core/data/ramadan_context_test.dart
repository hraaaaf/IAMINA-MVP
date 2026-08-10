import 'package:amina/core/data/ramadan_context.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test(
    'Ramadan context is never inferred without an explicit complete period',
    () {
      final day = DateTime(2026, 2, 20, 12);
      expect(isRamadanProfileDate(day, null, null), isFalse);
      expect(isRamadanProfileDate(day, DateTime(2026, 2, 18), null), isFalse);
      expect(mealTypesForProfileDate(day, null, null), regularMealTypes);
    },
  );

  test('configured period is inclusive and switches vocabulary only', () {
    final start = DateTime(2026, 2, 18);
    final end = DateTime(2026, 3, 20);
    expect(
      isRamadanProfileDate(DateTime(2026, 2, 18, 23, 59), start, end),
      isTrue,
    );
    expect(
      isRamadanProfileDate(DateTime(2026, 3, 20, 0, 1), start, end),
      isTrue,
    );
    expect(isRamadanProfileDate(DateTime(2026, 3, 21), start, end), isFalse);
    expect(mealTypesForProfileDate(DateTime(2026, 3, 1), start, end), <String>[
      'suhoor',
      'iftar',
      'snack',
      'other',
    ]);
  });
}
