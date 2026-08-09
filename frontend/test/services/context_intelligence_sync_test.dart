import 'package:flutter_test/flutter_test.dart';
import 'package:amina/services/sync_service.dart';

void main() {
  test('omitted context does not fabricate negative or good states', () {
    final fields = journalContextFieldsForSync(
      isSick: false,
      isStressed: false,
      isActive: false,
      sleepQuality: null,
    );
    expect(fields, isEmpty);
  });

  test('only explicitly selected positive context is synchronized', () {
    final fields = journalContextFieldsForSync(
      isSick: true,
      isStressed: false,
      isActive: true,
      sleepQuality: 'bad',
    );
    expect(fields, {
      'is_sick': 'yes',
      'exercised': 'yes',
      'sleep_quality': 'bad',
    });
    expect(fields.containsKey('stressed'), isFalse);
  });
}
