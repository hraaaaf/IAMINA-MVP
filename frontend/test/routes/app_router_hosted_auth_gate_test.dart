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

  test('hosted local-only session cannot enter app-lock before remote login', () {
    expect(
      shouldApplyAppLockGate(
        isLoggedIn: true,
        requiresHostedRemoteLogin: true,
        isAuditSession: false,
        hasLockService: true,
      ),
      isFalse,
    );
  });

  test('authenticated hosted session may enter app-lock after remote login', () {
    expect(
      shouldApplyAppLockGate(
        isLoggedIn: true,
        requiresHostedRemoteLogin: false,
        isAuditSession: false,
        hasLockService: true,
      ),
      isTrue,
    );
  });

  test('hosted local-only session cannot enter consent before remote login', () {
    expect(
      shouldApplyConsentGate(
        isLoggedIn: true,
        isAnonymous: false,
        requiresHostedRemoteLogin: true,
        hasConsentService: true,
      ),
      isFalse,
    );
  });

  test('authenticated hosted session may enter consent after remote login', () {
    expect(
      shouldApplyConsentGate(
        isLoggedIn: true,
        isAnonymous: false,
        requiresHostedRemoteLogin: false,
        hasConsentService: true,
      ),
      isTrue,
    );
  });

  test('anonymous demo session skips consent', () {
    expect(
      shouldApplyConsentGate(
        isLoggedIn: true,
        isAnonymous: true,
        requiresHostedRemoteLogin: false,
        hasConsentService: true,
      ),
      isFalse,
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
  test('real authenticated session without onboarding is gated', () {
    expect(
      shouldApplyOnboardingGate(
        isLoggedIn: true,
        isAnonymous: false,
        requiresHostedRemoteLogin: false,
        hasCompletedOnboarding: false,
        hasProfileState: true,
      ),
      isTrue,
    );
  });

  test('completed onboarding releases first-use gate', () {
    expect(
      shouldApplyOnboardingGate(
        isLoggedIn: true,
        isAnonymous: false,
        requiresHostedRemoteLogin: false,
        hasCompletedOnboarding: true,
        hasProfileState: true,
      ),
      isFalse,
    );
  });

  test('anonymous demo session skips onboarding gate', () {
    expect(
      shouldApplyOnboardingGate(
        isLoggedIn: true,
        isAnonymous: true,
        requiresHostedRemoteLogin: false,
        hasCompletedOnboarding: false,
        hasProfileState: true,
      ),
      isFalse,
    );
  });

  test('hosted local-only session waits for remote auth before onboarding', () {
    expect(
      shouldApplyOnboardingGate(
        isLoggedIn: true,
        isAnonymous: false,
        requiresHostedRemoteLogin: true,
        hasCompletedOnboarding: false,
        hasProfileState: true,
      ),
      isFalse,
    );
  });

}
