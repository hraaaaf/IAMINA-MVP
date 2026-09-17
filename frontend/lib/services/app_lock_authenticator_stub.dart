import 'app_lock_authenticator.dart';

AppLockAuthenticator createPlatformAppLockAuthenticator() =>
    const _UnsupportedAppLockAuthenticator();

class _UnsupportedAppLockAuthenticator implements AppLockAuthenticator {
  const _UnsupportedAppLockAuthenticator();

  @override
  Future<AppLockCapability> capability() async => AppLockCapability.unavailable;

  @override
  Future<AppLockCredential> enroll() =>
      Future.error(const AppLockException('unsupported_platform'));

  @override
  Future<AppLockAssertion> unlock(AppLockCredential credential) =>
      Future.error(const AppLockException('unsupported_platform'));
}
