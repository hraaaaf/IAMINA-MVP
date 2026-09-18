import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('PWA release identity advances with the canonical app version', () {
    final pubspec = File('pubspec.yaml').readAsStringSync();
    final worker = File('web/iamina_service_worker.js').readAsStringSync();
    final bootstrap = File('web/flutter_bootstrap.js').readAsStringSync();

    expect(pubspec, contains('version: 0.1.0+2'));
    expect(worker, contains("const IAMINA_CACHE_SCHEMA = '0.1.0+2';"));
    expect(bootstrap, contains("const IAMINA_FALLBACK_RELEASE = '0.1.0+2';"));
  });

  test('PWA keeps release-atomic update safety and API cache exclusion', () {
    final source = File('web/iamina_service_worker.js').readAsStringSync();

    expect(source, contains('async function cacheFirstStatic'));
    expect(source, contains('async function cacheFirstNavigation'));
    expect(source, isNot(contains('self.skipWaiting()')));
    expect(source, contains('self.clients.claim()'));
    expect(source, contains("if (url.pathname.startsWith('/api/')) return;"));
  });
}
