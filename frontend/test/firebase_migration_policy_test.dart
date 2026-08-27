import 'package:amina/services/firebase_migration_policy.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('Firebase migration is disabled by default in Flutter', () {
    expect(kFirebaseMigrationEnabled, isFalse);
  });
}
