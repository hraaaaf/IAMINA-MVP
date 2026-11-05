import 'package:amina/services/w01_revocation_probe.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

const _syntheticBearer = 'iamina.synthetic-test-only-not-a-real-credential';
const _url = kW01PreviewWebOrigin;

http.Response _json(int code) => http.Response(
  code == 200 ? '{"items":[]}' : '{"detail":"Unauthorized"}',
  code,
  headers: {'content-type': 'application/json; charset=utf-8'},
);

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('preview-only gate enabled in isolated CI test invocation', () {
    expect(kW01RevocationProbeEnabled, isTrue);
  });

  test('same native bearer accepted, revoked, then rejected on clinical GET',
      () async {
    final calls = <String>[];
    final result = await runW01RevocationProbe(
      bearer: _syntheticBearer,
      baseUrl: _url,
      client: MockClient((request) async {
        expect(request.headers['authorization'], 'Bearer $_syntheticBearer');
        expect(request.url.origin, _url);
        calls.add('${request.method} ${request.url.path}');
        if (calls.length == 1) return _json(200);
        if (calls.length == 2) return _json(200);
        return _json(401);
      }),
    );
    expect(calls, [
      'GET /api/v1/logs',
      'POST /api/v1/auth/logout',
      'GET /api/v1/logs',
    ]);
    expect(result.passed, isTrue);
    expect(result.beforeStatus, 200);
    expect(result.logoutStatus, 200);
    expect(result.afterStatus, 401);
  });

  test('rejects local-only, missing or non-native credentials', () async {
    for (final token in <String?>[null, '', 'firebase-token']) {
      final result = await runW01RevocationProbe(
        bearer: token,
        baseUrl: _url,
        client: MockClient((_) async {
          fail('No network request without native bearer');
        }),
      );
      expect(result.passed, isFalse);
      expect(result.failureCode, 'no_native_bearer');
    }
  });

  test('will never send a bearer to another host', () async {
    final result = await runW01RevocationProbe(
      bearer: _syntheticBearer,
      baseUrl: 'https://iamina-certified.vercel.app',
      client: MockClient((_) async {
        fail('No request may reach production');
      }),
    );
    expect(result.failureCode, 'wrong_preview_origin');
  });

  test('fails closed when initial clinical GET is unauthorized', () async {
    var calls = 0;
    final result = await runW01RevocationProbe(
      bearer: _syntheticBearer,
      baseUrl: _url,
      client: MockClient((_) async {
        calls++;
        return _json(401);
      }),
    );
    expect(calls, 1);
    expect(result.beforeStatus, 401);
    expect(result.passed, isFalse);
  });

  test('does not count a Vercel HTML login page as authenticated', () async {
    final result = await runW01RevocationProbe(
      bearer: _syntheticBearer,
      baseUrl: _url,
      client: MockClient((_) async => http.Response(
        '<html>Sign in</html>',
        200,
        headers: {'content-type': 'text/html'},
      )),
    );
    expect(result.failureCode, 'active_bearer_not_verified');
    expect(result.passed, isFalse);
  });

  test('fails closed when remote logout does not succeed', () async {
    var calls = 0;
    final result = await runW01RevocationProbe(
      bearer: _syntheticBearer,
      baseUrl: _url,
      client: MockClient((_) async {
        calls++;
        return _json(calls == 1 ? 200 : 503);
      }),
    );
    expect(calls, 2);
    expect(result.logoutStatus, 503);
    expect(result.passed, isFalse);
  });

  test('fails closed when the old bearer still reads clinical records', () async {
    var calls = 0;
    final result = await runW01RevocationProbe(
      bearer: _syntheticBearer,
      baseUrl: _url,
      client: MockClient((_) async {
        calls++;
        return _json(200);
      }),
    );
    expect(calls, 3);
    expect(result.afterStatus, 200);
    expect(result.passed, isFalse);
    expect(result.failureCode, 'old_bearer_not_rejected');
  });

  test('fails closed on transport errors with no token exposure', () async {
    final result = await runW01RevocationProbe(
      bearer: _syntheticBearer,
      baseUrl: _url,
      client: MockClient((_) async => throw StateError('network down')),
    );
    expect(result.passed, isFalse);
    expect(result.failureCode, 'transport_unavailable');
    expect(result.toString().contains(_syntheticBearer), isFalse);
  });
}
