import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('patient API client never installs credential/body request loggers', () {
    final source = File('lib/services/api_client.dart').readAsStringSync();
    final start = source.indexOf('late final ChopperClient _client = ChopperClient(');
    expect(start, greaterThanOrEqualTo(0));

    final end = source.indexOf('converter: const JsonConverter()', start);
    expect(end, greaterThan(start));
    final interceptors = source.substring(start, end);

    // Auth and retry remain configured; only the diagnostic data sink is gone.
    expect(interceptors, contains('AuthInterceptor(_authService)'));
    expect(interceptors, contains('RetryInterceptor(_authService)'));
    expect(interceptors, contains('TimeoutInterceptor()'));

    // CurlInterceptor logs request headers and bodies, including Bearer tokens
    // and patient-supplied content. No patient HTTP payload logging in builds.
    expect(interceptors, isNot(contains('CurlInterceptor(')));
    expect(interceptors, isNot(contains('HttpLoggingInterceptor(')));
  });
}
