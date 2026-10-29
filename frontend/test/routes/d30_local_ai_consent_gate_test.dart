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

  test('D30 signed-out and hosted-login-pending states have no AI consent route', () {
    const cases = [
      (isLoggedIn: false, requiresHostedRemoteLogin: false),
      (isLoggedIn: false, requiresHostedRemoteLogin: true),
      (isLoggedIn: true, requiresHostedRemoteLogin: true),
    ];
    for (final state in cases) {
      expect(
        shouldRequireRemoteAIConsentGate(
          isLoggedIn: state.isLoggedIn,
          isAnonymous: false,
          requiresHostedRemoteLogin: state.requiresHostedRemoteLogin,
          hasConsentService: true,
          hasRemoteApiCredential: true,
        ),
        isFalse,
        reason: 'No AI dialog before authentication or while hosted login is pending',
      );
    }
  });

  test('D30 anonymous and missing consent service do not expose an AI gate', () {
    expect(
      shouldRequireRemoteAIConsentGate(
        isLoggedIn: true,
        isAnonymous: true,
        requiresHostedRemoteLogin: false,
        hasConsentService: true,
        hasRemoteApiCredential: true,
      ),
      isFalse,
    );
    expect(
      shouldRequireRemoteAIConsentGate(
        isLoggedIn: true,
        isAnonymous: false,
        requiresHostedRemoteLogin: false,
        hasConsentService: false,
        hasRemoteApiCredential: true,
      ),
      isFalse,
    );
  });
}
