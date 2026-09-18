import 'package:amina/routes/app_router.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('hosted remote flow rejects local-only authenticated session', () {
    expect(
      hostedRemoteLoginRequired(
        remoteAccountEnrollmentEnabled: true,
        isLoggedIn: true,
        isAuditSession: false,
        hasRemoteApiCredential: false,
      ),
      isTrue,
    );
  });

  test('hosted remote flow accepts session with native API credential', () {
    expect(
      hostedRemoteLoginRequired(
        remoteAccountEnrollmentEnabled: true,
        isLoggedIn: true,
        isAuditSession: false,
        hasRemoteApiCredential: true,
      ),
      isFalse,
    );
  });

  test('audit session is not forced through hosted remote login', () {
    expect(
      hostedRemoteLoginRequired(
        remoteAccountEnrollmentEnabled: true,
        isLoggedIn: true,
        isAuditSession: true,
        hasRemoteApiCredential: false,
      ),
      isFalse,
    );
  });

  test('local-first build remains independent from remote account credential', () {
    expect(
      hostedRemoteLoginRequired(
        remoteAccountEnrollmentEnabled: false,
        isLoggedIn: true,
        isAuditSession: false,
        hasRemoteApiCredential: false,
      ),
      isFalse,
    );
  });
}
