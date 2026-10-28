import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:amina/services/auth_service.dart';

void main() {
  final qa = Uri.parse(
    'https://iamina-review-cvol3yzzn-achraf-benmoussa-s-projects.vercel.app/#/profile',
  );
  bool allowed(Uri uri, {
    bool sameOriginPreview = true,
    bool remoteEnrollment = true,
    bool verified = true,
  }) => mayEraseSyntheticPreviewAccount(
    sameOriginPreview: sameOriginPreview,
    remoteAccountEnrollmentEnabled: remoteEnrollment,
    hasVerifiedNativeCredential: verified,
    browserUri: uri,
  );

  test('requires the QA build flags and verified native identity', () {
    expect(allowed(qa), isTrue);
    expect(allowed(qa, sameOriginPreview: false), isFalse);
    expect(allowed(qa, remoteEnrollment: false), isFalse);
    expect(allowed(qa, verified: false), isFalse);
  });
  test('HTML SSO 200, invalid JSON and failed API cannot confirm erasure', () {
    expect(syntheticErasureResponseConfirmed(
      statusCode: 200, contentType: 'text/html',
      body: '<html>Vercel Authentication</html>'), isFalse);
    expect(syntheticErasureResponseConfirmed(
      statusCode: 503, contentType: 'application/json',
      body: '{"detail":"Account and all associated data deleted."}'), isFalse);
    expect(syntheticErasureResponseConfirmed(
      statusCode: 200, contentType: 'application/json',
      body: '{oops'), isFalse);
    expect(syntheticErasureResponseConfirmed(
      statusCode: 200, contentType: 'application/json',
      body: '{"detail":"different response"}'), isFalse);
    expect(syntheticErasureResponseConfirmed(
      statusCode: 200, contentType: 'application/json; charset=utf-8',
      body: '{"detail":"Account and all associated data deleted."}'), isTrue);
  });

  test('only exact @example.invalid emails may be erased', () {
    expect(syntheticPreviewEmailAllowed('w01-test@example.invalid'), isTrue);
    expect(syntheticPreviewEmailAllowed('w01.test_123@example.invalid'), isTrue);
    expect(syntheticPreviewEmailAllowed('real@example.com'), isFalse);
    expect(syntheticPreviewEmailAllowed('real@example.invalid.evil.com'), isFalse);
    expect(syntheticPreviewEmailAllowed('Real@example.invalid'), isFalse);
    expect(syntheticPreviewEmailAllowed('test+tag@example.invalid'), isFalse);
    expect(syntheticPreviewEmailAllowed('test@example.invalid '), isFalse);
    expect(syntheticPreviewEmailAllowed(null), isFalse);
  });

  test('restored QA identity requires live exact Django JSON user binding', () {
    const valid = '{"id":7,"email":"w01-a@example.invalid"}';
    bool check(String body, {int status = 200, String type = 'application/json', int id = 7}) =>
        syntheticIdentityResponseConfirmed(
          statusCode: status,
          contentType: type,
          body: body,
          expectedUserId: id,
        );
    expect(check(valid), isTrue);
    expect(check(valid, id: 8), isFalse);
    expect(check(valid, id: 0), isFalse);
    expect(check(valid, status: 401), isFalse);
    expect(check(valid, status: 403), isFalse);
    expect(check(valid, status: 503), isFalse);
    expect(check(valid, type: 'text/html'), isFalse);
    expect(check('<html>SSO</html>'), isFalse);
    expect(check('{invalid'), isFalse);
    expect(check('{"id":7,"email":"person@gmail.com"}'), isFalse);
    expect(check('{"id":"7","email":"w01-a@example.invalid"}'), isFalse);
    expect(check('{"id":7,"email":"evil@example.invalid.attacker"}'), isFalse);
  });

  test('successful synthetic re-verification keeps the bound vault/router epoch', () {
    // AuthService._notifyAuthChanged() advances AuthEpoch and tears down the
    // patient-scoped GoRouter. A QA credential recheck must not do this.
    final source = File('lib/services/auth_service.dart').readAsStringSync();
    final marker = 'Future<void> reverifySyntheticPreviewForErasure() async {';
    expect(source, contains(marker));
    final recheck = source.split(marker).last.split(
      '/// Test-only, single-attempt remote application erasure',
    ).first;
    expect(recheck, contains("'/api/v1/auth/me'"));
    expect(recheck, contains('syntheticIdentityResponseConfirmed('));
    expect(recheck, contains('_remoteCredentialVerified = true;'));
    expect(recheck, isNot(contains('_notifyAuthChanged();')));
    expect(recheck, isNot(contains('AuthEpoch.advance()')));
  });

  test('cannot erase on Production or arbitrary/insecure host', () {
    expect(allowed(Uri.parse('https://iamina-review.vercel.app/#/profile')), isFalse);
    expect(allowed(Uri.parse('https://iamina-certified-abcd-achraf-benmoussa-s-projects.vercel.app')), isFalse);
    expect(allowed(Uri.parse('https://example.com/')), isFalse);
    expect(allowed(Uri.parse('http://iamina-review-cvol3yzzn-achraf-benmoussa-s-projects.vercel.app')), isFalse);
  });
}
