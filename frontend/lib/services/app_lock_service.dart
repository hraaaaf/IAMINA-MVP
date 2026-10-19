import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import 'app_lock_authenticator.dart';
import 'app_lock_authenticator_factory.dart';
import 'auth_service.dart';

typedef ProtectedLocalStateProbe = Future<bool> Function();

class AppLockService extends ChangeNotifier {
  static const _credentialKey = 'iamina_app_lock_credential_v1';
  static const _requiredKey = 'iamina_app_lock_required_v1';
  static const _ownerKey = 'iamina_app_lock_native_owner_v1';
  static const _requiredValue = 'required';
  static const Duration defaultGracePeriod = Duration(seconds: 60);

  final FlutterSecureStorage _storage;
  final AppLockAuthenticator _authenticator;
  final AuthService? _authService;
  final ProtectedLocalStateProbe? _protectedLocalStateProbe;
  final DateTime Function() _now;
  final Duration gracePeriod;

  bool _initialized = false;
  bool _configured = false;
  bool _required = false;
  bool _unlocked = false;
  bool _recoveryRequired = false;
  AppLockCredential? _credential;
  int? _nativeOwnerId;
  DateTime? _backgroundedAt;

  AppLockService({
    FlutterSecureStorage? storage,
    AppLockAuthenticator? authenticator,
    AuthService? authService,
    ProtectedLocalStateProbe? protectedLocalStateProbe,
    DateTime Function()? now,
    this.gracePeriod = defaultGracePeriod,
  }) : _storage = storage ?? const FlutterSecureStorage(),
       _authenticator = authenticator ?? createPlatformAppLockAuthenticator(),
¶»§q«^