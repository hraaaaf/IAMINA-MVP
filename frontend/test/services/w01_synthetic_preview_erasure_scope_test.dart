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
  test('cannot erase on Production or arbitrary/insecure host', () {
    expect(allowed(Uri.parse('https://iamina-review.vercel.app/#/profile')), isFalse);
    expect(allowed(Uri.parse('https://iamina-certified-abcd-achraf-benmoussa-s-projects.vercel.app')), isFalse);
    expect(allowed(Uri.parse('https://example.com/')), isFalse);
    expect(allowed(Uri.parse('http://iamina-review-cvol3yzzn-achraf-benmoussa-s-projects.vercel.app')), isFalse);
  });
}
