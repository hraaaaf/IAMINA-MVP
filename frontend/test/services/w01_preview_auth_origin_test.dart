import 'package:amina/services/auth_service.dart';
import 'package:amina/services/api_client.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

void main() {
  const formerAlias =
      'https://iamina-review-git-preview-w0-f972e4-achraf-benmoussa-s-projects.vercel.app';
  final immutable = Uri.parse(
    'https://iamina-review-i7ykgen4b-achraf-benmoussa-s-projects.vercel.app/login',
  );

  test('W01 login and clinical transport use current immutable Web origin', () {
    final credential = resolveAuthApiOrigin(
      isWeb: true,
      remoteAccountLogin: true,
      pageUri: immutable,
      configuredBaseUrl: formerAlias,
    );
    final clinical = resolvePatientApiOrigin(
      isWeb: true,
      remoteAccountLogin: true,
      pageUri: immutable,
      configuredBaseUrl: formerAlias,
    );
    expect(credential, immutable.origin);
    expect(clinical, credential);
    expect(
      Uri.parse('$credential/api/v1/auth/login').origin,
      immutable.origin,
    );
    expect(
      Uri.parse('$credential/api/v1/auth/logout').origin,
      immutable.origin,
    );
    expect(credential, isNot(formerAlias));
  });

  test('native and local-first use configured backend, never implicit Web', () {
    for (final mode in [(false, true), (true, false), (false, false)]) {
      expect(
        resolveAuthApiOrigin(
          isWeb: mode.$1,
          remoteAccountLogin: mode.$2,
          pageUri: immutable,
          configuredBaseUrl: formerAlias,
        ),
        formerAlias,
      );
    }
  });

  test('remote Web credentials refuse insecure remote origins', () {
    expect(
      () => resolveAuthApiOrigin(
        isWeb: true,
        remoteAccountLogin: true,
        pageUri: Uri.parse('http://example.invalid/login'),
        configuredBaseUrl: formerAlias,
      ),
      throwsStateError,
    );
    expect(
      resolveAuthApiOrigin(
        isWeb: true,
        remoteAccountLogin: true,
        pageUri: Uri.parse('http://localhost:7378/login'),
        configuredBaseUrl: formerAlias,
      ),
      'http://localhost:7378',
    );
  });

  test('HTTP 401 is invalid credentials, HTTP 503 is service unavailable', () async {
    for (final code in [401, 503]) {
      final service = AuthService(
        httpClient: MockClient((request) async {
          expect(request.url.path, '/api/v1/auth/login');
          expect(request.body, contains('synthetic@example.invalid'));
          return http.Response(
            code == 401
                ? '{"detail":"Invalid authentication credential"}'
                : '{"detail":"synthetic"}',
            code,
          );
        }),
      );
      try {
        await expectLater(
          service.signInWithEmail('synthetic@example.invalid', 'sample-only'),
          throwsA(code == 401
              ? isA<AuthCredentialsRejected>()
              : isA<AuthSignInServiceUnavailable>()),
        );
        expect(service.isRemoteCredentialVerified, isFalse);
        expect(service.boundNativeAccountId, isNull);
      } finally {
        service.dispose();
      }
    }
  });
  test('Vercel SSO 401 is service unavailable, not a wrong password', () async {
    final service = AuthService(
      httpClient: MockClient((request) async {
        expect(request.url.path, '/api/v1/auth/login');
        return http.Response('<html>Protected by Vercel</html>', 401);
      }),
    );
    try {
      await expectLater(
        service.signInWithEmail('synthetic@example.invalid', 'sample-only'),
        throwsA(isA<AuthSignInServiceUnavailable>()),
      );
      expect(service.isRemoteCredentialVerified, isFalse);
    } finally {
      service.dispose();
    }
  });

  test('D11 local Flutter and Django may use separate loopback ports', () {
    final page = Uri.parse('http://127.0.0.1:7383/login');
    const backend = 'http://127.0.0.1:8000';
    expect(
      resolveAuthApiOrigin(
        isWeb: true,
        remoteAccountLogin: true,
        pageUri: page,
        configuredBaseUrl: backend,
        useConfiguredLoopbackBackend: true,
      ),
      backend,
    );
    expect(
      resolveAuthApiOrigin(
        isWeb: true,
        remoteAccountLogin: true,
        pageUri: page,
        configuredBaseUrl: backend,
      ),
      page.origin,
    );
    expect(
      () => resolveAuthApiOrigin(
        isWeb: true,
        remoteAccountLogin: true,
        pageUri: page,
        configuredBaseUrl: 'https://untrusted.example.invalid',
        useConfiguredLoopbackBackend: true,
      ),
      throwsStateError,
    );
  });


}
