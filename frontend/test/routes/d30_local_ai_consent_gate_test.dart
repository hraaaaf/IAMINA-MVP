import 'package:amina/routes/app_router.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('D30 local-only enrollment never forces optional remote AI consent', () {
    expect(
      shouldRequireRemoteAIConsentGate(
        isLoggedIn: true,
        isAnonymous: false,
        requiresHostedRemoteLogin: false,
        hasConsentService: true,
        hasRemoteApiCredential: false,
      ),
      isFalse,
    );
  });

  test('D30 remote-capable account retains the existing AI consent gate', () {
    expect(
      shouldRequireRemoteAIConsentGate(
        isLoggedIn: true,
        isAnonymous: false,
        requiresHostedRemoteLogin: false,
        hasConsentService: true,
        hasRemoteApiCredential: true,
      ),
      isTrue,
    );
  });

  test('D30 unauthenticated and pending remote login stay gated safely', () {
    for (final pending in [false, true]) {
      expect(
        shouldRequireRemoteAIConsentGate(
          isLoggedIn: !pending,
          isAnonymous: false,
          requiresHostedRemoteLogin: pending,
          hasConsentService: true,
          hasRemoteApiCredential: true,
        ),
        isFalse,
      );
    }
  });
}
