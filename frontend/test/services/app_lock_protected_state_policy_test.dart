import 'package:amina/services/app_lock_protected_state_policy.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('remote bearer does not force app-lock recovery on a fresh browser', () {
    expect(
      authSessionCountsAsProtectedLocalState(
        auditAllowed: false,
        isAuthenticated: true,
        hasRemoteApiCredential: true,
      ),
      isFalse,
    );
  });

  test('local-only authenticated marker remains protected local state', () {
    expect(
      authSessionCountsAsProtectedLocalState(
        auditAllowed: false,
        isAuthenticated: true,
        hasRemoteApiCredential: false,
      ),
      isTrue,
    );
  });

  test('anonymous and audit sessions never imply prior protected local state', () {
    expect(
      authSessionCountsAsProtectedLocalState(
        auditAllowed: false,
        isAuthenticated: false,
        hasRemoteApiCredential: false,
      ),
      isFalse,
    );
    expect(
      authSessionCountsAsProtectedLocalState(
        auditAllowed: true,
        isAuthenticated: true,
        hasRemoteApiCredential: false,
      ),
      isFalse,
    );
  });
}
