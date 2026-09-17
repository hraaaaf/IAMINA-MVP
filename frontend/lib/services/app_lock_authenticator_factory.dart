import 'app_lock_authenticator.dart';
import 'app_lock_authenticator_stub.dart'
    if (dart.library.js_interop) 'app_lock_authenticator_web.dart' as platform;

AppLockAuthenticator createPlatformAppLockAuthenticator() =>
    platform.createPlatformAppLockAuthenticator();
