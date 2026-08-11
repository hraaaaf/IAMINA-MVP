import 'package:flutter_test/flutter_test.dart';
import 'package:amina/services/sync_service.dart';

void main() {
  test('omitted context does not fabricate negative or good states', () {
    final fields = journalContextFieldsForSync(
      isSick: false,
      isStressed: false,
      isActive: false,
      sleepQuality: null,
      fatigueLevel: null,
    );
    expect(fields, isEmpty);
  });

  test('only explicitly selected positive context is synchronized', () {
    final fields = journalContextFieldsForSync(
      isSick: true,
      isStressed: false,
      isActive: true,
      sleepQuality: 'bad',
      fatigueLevel: null,
    );
    expect(fields, {
      'is_sick': 'yes',
      'exercised': 'yes',
      'sleep_quality': 'bad',
    });
    expect(fields.containsKey('stressed'), isFalse);
    expect(fields.containsKey('fatigue_level'), isFalse);
  });

  test(
    'explicit legacy fatigue remains synchronized without fabricating ok',
    () {
      final fields = journalContextFieldsForSync(
        isSick: false,
        isStressed: false,
        isActive: false,
        sleepQuality: null,
        fatigueLevel: 2,
      );
      expect(fields, {'fatigue_level': 'tired'});
    },
  );
}
