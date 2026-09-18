import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('IAMINA review service worker rotates cache per release', () {
    final source = File('web/iamina_service_worker.js').readAsStringSync();

    expect(source, contains("const IAMINA_CACHE_SCHEMA = '0.1.0+1';"));
    expect(source, contains("searchParams.get('release')"));
    expect(source, contains(r'`${IAMINA_CACHE_PREFIX}${IAMINA_RELEASE}`'));
    expect(source, contains("self.location.hostname.startsWith('iamina-review')"));
  });

  test('canonical service worker keeps safe waiting activation', () {
    final source = File('web/iamina_service_worker.js').readAsStringSync();

    expect(source, isNot(contains('self.skipWaiting()')));
    expect(source, contains('self.clients.claim()'));
  });

  test('Vercel review worker eagerly activates fresh hosted code', () {
    final source = File(
      'web/iamina_service_worker_review.js',
    ).readAsStringSync();

    expect(source, contains('self.skipWaiting()'));
    expect(source, contains('await self.clients.claim()'));
    expect(source, contains("self.clients.matchAll({ type: 'window' })"));
    expect(source, contains('client.navigate(client.url)'));
  });

  test('bootstrap discovers uncached exact release before registration', () {
    final source = File('web/flutter_bootstrap.js').readAsStringSync();

    expect(source, contains('iamina_release.txt?release_probe='));
    expect(source, contains("cache: 'no-store'"));
    expect(source, contains('iamina_service_worker.js?release_probe='));
  });
}
