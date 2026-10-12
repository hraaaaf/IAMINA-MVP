import 'dart:convert';
import 'dart:io';

import 'package:amina/services/api_client.dart';
import 'package:flutter_test/flutter_test.dart';

/// Pre-deployment contract only. This is NOT an installed-browser upgrade test.
void main() {
  test('upgrade trial uses one new release id across PWA entrypoints', () {
    final pubspec = File('pubspec.yaml').readAsStringSync();
    final match = RegExp(
      r'^version:\s*(\d+\.\d+\.\d+\+\d+)\s*$',
      multiLine: true,
    ).firstMatch(pubspec);
    expect(match, isNotNull);
    final release = match!.group(1);
    expect(release, '0.1.0+2');
    expect(release, isNot('0.1.0+1'));

    final worker = File('web/iamina_service_worker.js').readAsStringSync();
    final bootstrap = File('web/flutter_bootstrap.js').readAsStringSync();

    expect(worker, contains("const IAMINA_CACHE_SCHEMA = '$release';"));
    expect(
      bootstrap,
      contains("const IAMINA_FALLBACK_RELEASE = '$release';"),
    );
    expect(worker, contains("'./main.dart.js',"));
  });

  test('cutover frontend still encodes health text in POST body, never URL', () {
    const marker = 'SYNTHETIC_UPGRADE_TEST_PRIVATE_GLUCOSE_175';
    final request = buildPatientSseRequest('https://example.invalid', marker);
    expect(request.method, 'POST');
    expect(request.url.path, '/api/v1/ai/chat/stream');
    expect(request.url.query, isEmpty);
    expect(request.url.toString(), isNot(contains(marker)));
    final body = jsonDecode(request.body) as Map<String, dynamic>;
    expect(body['message'], marker);
  });

  test('PWA app-shell cache must not intercept patient API responses', () {
    final worker = File('web/iamina_service_worker.js').readAsStringSync();
    expect(
      worker,
      contains("if (url.pathname.startsWith('/api/')) return;"),
    );
    expect(worker, contains("if (request.method !== 'GET') return;"));
  });
}
