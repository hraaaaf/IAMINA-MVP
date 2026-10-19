import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('D11: MENA and French login never seed clinical demo values', () {
    for (final path in <String>[
      'lib/features/auth/login_screen_mena.dart',
      'lib/features/auth/login_screen_fr_certified.dart',
    ]) {
      final source = File(path).readAsStringSync();
      expect(source, isNot(contains('seedDemoData(')), reason: path);
      expect(source, contains('await auth.signInAnonymously()'), reason: path);
    }
  });

  test('D11: API client does not call the retired patient seeding endpoint', () {
    final source = File('lib/services/api_client.dart').readAsStringSync();
    expect(source, isNot(contains("Uri.parse('/api/v1/demo/seed')")));
    expect(source, isNot(contains('Future<bool> seedDemoData()')));
  });

  test('D11: audit-only namespace is checked before any deletion', () {
    final service = File('lib/services/offline_demo_audit_seed.dart')
        .readAsStringSync();
    final database = File('lib/data/drift/database.dart').readAsStringSync();
    expect(service, contains('PatientVaultScope.auditOnly().databaseName'));
    final method = database.indexOf('Future<void> seedDemoData() async');
    final guard = database.indexOf('if (patientVaultScope?.databaseName', method);
    final firstDelete = database.indexOf('await delete(logEntries).go()', method);
    expect(method, greaterThanOrEqualTo(0));
    expect(guard, greaterThan(method));
    expect(firstDelete, greaterThan(guard));
  });
}
