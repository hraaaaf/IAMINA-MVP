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

  test('cannot erase on Production or arbitrary/insecure host', () {
    expect(allowed(Uri.parse('https://iamina-review.vercel.app/#/profile')), isFalse);
    expect(allowed(Uri.parse('https://iamina-certified-abcd-achraf-benmoussa-s-projects.vercel.app')), isFalse);
    expect(allowed(Uri.parse('https://example.com/')), isFalse);
    expect(allowed(Uri.parse('http://iamina-review-cvol3yzzn-achraf-benmoussa-s-projects.vercel.app')), isFalse);
  });
}
