import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('PWA serves release-critical shell files network-first when online', () {
    final source = File('web/iamina_service_worker.js').readAsStringSync();

    expect(source, contains("const IAMINA_CACHE_SCHEMA = '0.1.0+2';"));
    expect(source, contains("'/flutter_bootstrap.js'"));
    expect(source, contains("'/main.dart.js'"));
    expect(source, contains("new Request(request, { cache: 'no-store' })"));
    expect(source, contains('event.respondWith(networkFirstNavigation(request))'));
    expect(source, contains('event.respondWith(networkFirstStatic(request))'));
  });

  test('PWA update activates immediately and still excludes API responses', () {
    final source = File('web/iamina_service_worker.js').readAsStringSync();

    expect(source, contains('await self.skipWaiting()'));
    expect(source, contains('await self.clients.claim()'));
    expect(source, contains("if (url.pathname.startsWith('/api/')) return;"));

    final bootstrap = File('web/flutter_bootstrap.js').readAsStringSync();
    expect(bootstrap, contains("const IAMINA_FALLBACK_RELEASE = '0.1.0+2';"));
    expect(bootstrap, contains("addEventListener('controllerchange'"));
    expect(bootstrap, contains('window.location.reload()'));
  });
}
