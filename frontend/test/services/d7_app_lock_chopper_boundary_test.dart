import 'dart:async';

import 'package:amina/services/api_client.dart';
import 'package:amina/services/auth_service.dart';
import 'package:chopper/chopper.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:mocktail/mocktail.dart';

class _Auth extends Mock implements AuthService {}

/// Calls the real Chopper interceptors while recording attempted dispatch,
/// without creating any network connection or including patient data.
class _Chain implements Chain<Object?> {
  @override
  final Request request;
  final int statusCode;
  int dispatched = 0;

  _Chain(String method, String path, {this.statusCode = 200})
      : request = Request(method, Uri.parse(path), Uri.parse('https://test.invalid'));

  @override
  FutureOr<Response<Object?>> proceed(Request request) {
    dispatched++;
    return Response<Object?>(http.Response('', statusCode), null);
  }
}

void main() {
  test('Pilot A rejects profile and journal requests before bearer lookup', () async {
    final auth = _Auth();
    final profile = _Chain('PATCH', '/api/v1/profile');
    await expectLater(
      Future<Response<Object?>>.value(AuthInterceptor(
        auth, canUseClinicalTransport: () => false,
      ).intercept<Object?>(profile)),
      throwsStateError,
    );
    expect(profile.dispatched, 0);
    verifyNever(() => auth.getIdToken());

    final retry = _Chain('POST', '/api/v1/logs/batch');
    await expectLater(
      Future<Response<Object?>>.value(RetryInterceptor(
        auth, canUseClinicalTransport: () => false,
      ).intercept<Object?>(retry)),
      throwsStateError,
    );
    expect(retry.dispatched, 0);
  });

  test('Pilot A keeps public login transport working', () async {
    final auth = _Auth();
    when(() => auth.getIdToken()).thenAnswer((_) async => null);
    final login = _Chain('POST', '/api/v1/auth/login');
    final response = await AuthInterceptor(
      auth, canUseClinicalTransport: () => false,
    ).intercept<Object?>(login);
    expect(response.statusCode, 200);
    expect(login.dispatched, 1);
  });

  test('D7 real AuthInterceptor never dispatches if lock closes while token awaits',
      () async {
    final auth = _Auth();
    final token = Completer<String?>();
    when(() => auth.getIdToken()).thenAnswer((_) => token.future);
    var unlocked = true;
    final interceptor = AuthInterceptor(
      auth, canUsePatientSyncTransport: () => unlocked,
    );
    final chain = _Chain('PATCH', '/api/v1/profile');
    final result = Future<Response<Object?>>.value(
      interceptor.intercept<Object?>(chain),
    );
    unlocked = false;
    token.complete('synthetic-token');
    await expectLater(result, throwsStateError);
    expect(chain.dispatched, 0);
  });

  test('D7 actual AuthInterceptor permits login before device unlock', () async {
    final auth = _Auth();
    when(() => auth.getIdToken()).thenAnswer((_) async => null);
    final chain = _Chain('POST', '/api/v1/auth/login');
    final result = await AuthInterceptor(
      auth, canUsePatientSyncTransport: () => false,
    ).intercept<Object?>(chain);
    expect(result.statusCode, 200);
    expect(chain.dispatched, 1);
  });

  test('D7 actual RetryInterceptor cannot re-send a 401 after locking', () async {
    final auth = _Auth();
    final refreshed = Completer<String?>();
    when(() => auth.refreshToken()).thenAnswer((_) => refreshed.future);
    var unlocked = true;
    final chain = _Chain('PATCH', '/api/v1/profile', statusCode: 401);
    final result = Future<Response<Object?>>.value(
      RetryInterceptor(
        auth, canUsePatientSyncTransport: () => unlocked,
      ).intercept<Object?>(chain),
    );
    await Future<void>.delayed(Duration.zero);
    unlocked = false;
    refreshed.complete('new-token');
    await expectLater(result, throwsStateError);
    expect(chain.dispatched, 1); // only initial authorized request
  });

  test('W01 medical mutations never retry after an ambiguous 502 or 503', () async {
    final auth = _Auth();
    for (final method in ['POST', 'PATCH', 'PUT', 'DELETE']) {
      for (final failure in [502, 503]) {
        final chain = _Chain(method, '/api/v1/logs/batch', statusCode: failure);
        final response = await RetryInterceptor(
          auth, canUsePatientSyncTransport: () => true,
        ).intercept<Object?>(chain);
        expect(response.statusCode, failure);
        expect(chain.dispatched, 1, reason: '$method must have one effect maximum');
        expect(mayRetryAfterServerError(method), isFalse);
      }
    }
    expect(mayRetryAfterServerError('GET'), isTrue);
    expect(mayRetryAfterServerError('HEAD'), isTrue);
  });

  test('D7 safe GET retry cannot dispatch after the app-lock closes', () async {
    final auth = _Auth();
    var unlocked = true;
    final chain = _Chain('GET', '/api/v1/logs', statusCode: 503);
    final result = Future<Response<Object?>>.value(
      RetryInterceptor(
        auth, canUsePatientSyncTransport: () => unlocked,
      ).intercept<Object?>(chain),
    );
    await Future<void>.delayed(Duration.zero);
    unlocked = false;
    await expectLater(result, throwsStateError);
    expect(chain.dispatched, 1);
  });
}
