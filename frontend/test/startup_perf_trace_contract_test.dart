import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('PERF-WEB trace is opt-in and preserves fail-closed startup', () {
    final trace = File('lib/services/startup_perf_trace.dart').readAsStringSync();
    final main = File('lib/main.dart').readAsStringSync();
    final host = File('lib/services/patient_vault_app_host.dart').readAsStringSync();
    expect(trace, contains('defaultValue: false'));
    expect(trace, contains("Uri.base.queryParameters['startup_perf'] == '1'"));
    expect(main, contains('await authService.initialize();'));
    expect(main, contains('await legacy.close();'));
    expect(main, contains('await hasProtectedMedicalVaultRows(protectedStateProbe)'));
    expect(main, contains('await appLockService.initialize();'));
    expect(main, contains('await vaultController.reconcile();'));
    expect(main, contains("StartupPerfTrace.mark('runapp_begin')"));
    expect(host, contains('bundle.authEpoch == AuthService.authEpoch'));
    expect(host, contains('widget.controller.activeDatabase == bundle.db'));
  });

  test('PERF-WEB exposes only local numeric data with no auto network', () {
    final js = File('web/iamina_startup_perf.js').readAsStringSync();
    final html = File('web/index.html').readAsStringSync();
    expect(html, contains('perfScript.src = "iamina_startup_perf.js";'));
    expect(html, contains('get("startup_perf") === "1"'));
    expect(js, contains("get('startup_perf') !== '1'"));
    expect(js, contains("performance.getEntriesByType('mark')"));
    expect(js, contains("scope: 'local_only_no_patient_data'"));
    expect(js, isNot(contains('fetch(')));
    expect(js, isNot(contains('XMLHttpRequest')));
    expect(js, isNot(contains('sendBeacon')));
    expect(js, isNot(contains('localStorage')));
    expect(js, isNot(contains('indexedDB')));
  });
}
