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
  })  : _storage = storage ?? const FlutterSecureStorage(),
        _authenticator =
            authenticator ?? createPlatformAppLockAuthenticator(),
        _authService = authService,
        _protectedLocalStateProbe = protectedLocalStateProbe,
        _now = now ?? DateTime.now {
    _authService?.addListener(_handleAuthChanged);
  }

  bool get isInitialized => _initialized;
  bool get isConfigured => _configured;
  bool get isRequired => _required;
  bool get isUnlocked => _unlocked;
  bool get recoveryRequired => _recoveryRequired;
  bool get needsSetup => _initialized && !_configured && !_recoveryRequired;

  Future<void> initialize() async {
    _configured = false;
    _required = false;
    _unlocked = false;
    _recoveryRequired = false;
    _credential = null;
    _nativeOwnerId = null;

    try {
      final requiredValue = await _storage.read(key: _requiredKey);
      final rawCredential = await _storage.read(key: _credentialKey);
      final rawOwner = await _storage.read(key: _ownerKey);
      final owner = int.tryParse(rawOwner ?? '');
      if (rawOwner != null && (owner == null || owner <= 0)) {
        throw const FormatException('Invalid lock owner');
      }
      _nativeOwnerId = owner;
      _required = requiredValue == _requiredValue;

      if (rawCredential != null && rawCredential.isNotEmpty) {
        try {
          _credential = AppLockCredential.decode(rawCredential);
          if (_authService?.boundNativeAccountId != null && owner == null) {
            throw const FormatException('Legacy lock owner ambiguous');
          }
          _configured = true;
          _required = true;
          if (requiredValue != _requiredValue) {
            await _storage.write(key: _requiredKey, value: _requiredValue);
          }
        } catch (_) {
          _credential = null;
          _configured = false;
          _recoveryRequired = true;
          _required = true;
        }
      } else if (_required) {
        _recoveryRequired = true;
      } else if (await _hasProtectedLocalState()) {
        // Secure app-lock state disappeared while patient-local state still
        // exists. Treat that as rollback/ambiguity, never as a fresh install.
        _required = true;
        _recoveryRequired = true;
      }
    } catch (_) {
      // Storage or protected-state ambiguity must not silently unlock or reset
      // a previously protected app.
      _credential = null;
      _configured = false;
      _required = true;
      _recoveryRequired = true;
    } finally {
      _initialized = true;
      notifyListeners();
    }
  }

  Future<bool> _hasProtectedLocalState() async {
    final probe = _protectedLocalStateProbe;
    if (probe == null) return false;
    try {
      return await probe();
    } catch (_) {
      // Failure to prove the installation is empty is not proof that it is
      // fresh. Fail closed into recovery instead of offering re-enrollment.
      return true;
    }
  }

  Future<AppLockCapability> capability() => _authenticator.capability();

  Future<void> recoverWithVerifiedRemoteAccount() async {
    if (!_initialized) {
      throw StateError('App lock requires initialized state');
    }
    final auth = _authService;
    // D10: recovery is not authorized without an unambiguous original owner.
    // A verified but unrelated account must not reset this installation lock.
    if (!_recoveryRequired ||
        _nativeOwnerId == null ||
        auth?.boundNativeAccountId != _nativeOwnerId ||
        auth == null ||
        !auth.isRemoteCredentialVerified ||
        !auth.hasRemoteApiCredential) {
      throw const AppLockException('verified_remote_recovery_required');
    }

    // A fresh, server-verified account login is the recovery authority. Remove
    // only the unverifiable app-lock material; patient-local clinical state is
    // retained and remains inaccessible until a new strong device lock enrolls.
    await _storage.delete(key: _credentialKey);
    await _storage.delete(key: _requiredKey);
    await _storage.delete(key: _ownerKey);
    _credential = null;
    _nativeOwnerId = null;
    _configured = false;
    _required = false;
    _recoveryRequired = false;
    _unlocked = false;
    notifyListeners();
  }

  Future<void> configure() async {
    if (!_initialized) {
      throw StateError('App lock requires initialized state');
    }
    if (_recoveryRequired) {
      throw const AppLockException('recovery_required');
    }
    final capability = await _authenticator.capability();
    if (capability == AppLockCapability.insecureContext) {
      throw const AppLockException('insecure_context');
    }
    if (capability != AppLockCapability.supported) {
      throw const AppLockException('strong_auth_unavailable');
    }

    final owner = _authService?.boundNativeAccountId;
    if (_authService?.hasRemoteApiCredential == true && owner == null) {
      throw const AppLockException('verified_owner_required');
    }
    final credential = await _authenticator.enroll();
    await _storage.write(key: _credentialKey, value: credential.encode());
    if (owner != null) await _storage.write(key: _ownerKey, value: '$owner');
    await _storage.write(key: _requiredKey, value: _requiredValue);

    _credential = credential;
    _nativeOwnerId = owner;
    _configured = true;
    _required = true;
    _recoveryRequired = false;
    _unlocked = true;
    notifyListeners();
  }

  Future<void> unlock() async {
    if (!_initialized) {
      throw StateError('App lock requires initialized state');
    }
    if (_recoveryRequired) {
      throw const AppLockException('recovery_required');
    }
    final credential = _credential;
    if (!_configured || credential == null) {
      throw const AppLockException('app_lock_not_configured');
    }

    final currentOwner = _authService?.boundNativeAccountId;
    if (_nativeOwnerId != null && currentOwner != _nativeOwnerId) {
      throw const AppLockException('app_lock_owner_mismatch');
    }
    if (_authService?.hasRemoteApiCredential == true &&
        _nativeOwnerId == null) {
      throw const AppLockException('app_lock_owner_ambiguous');
    }
    final assertion = await _authenticator.unlock(credential);
    final updated = credential.copyWith(signCount: assertion.signCount);
    await _storage.write(key: _credentialKey, value: updated.encode());

    _credential = updated;
    _unlocked = true;
    notifyListeners();
  }

  void lock() {
    if (!_unlocked) return;
    _unlocked = false;
    notifyListeners();
  }

  void noteBackgrounded() {
    _backgroundedAt ??= _now();
  }

  void noteResumed() {
    final backgroundedAt = _backgroundedAt;
    _backgroundedAt = null;
    if (backgroundedAt == null || !_configured || !_unlocked) return;
    final elapsed = _now().difference(backgroundedAt);
    if (elapsed >= gracePeriod) lock();
  }

  void noteDetached() {
    _backgroundedAt = null;
    lock();
  }

  void _handleAuthChanged() {
    final auth = _authService;
    if (auth != null && auth.isInitialized &&
        (!auth.isAuthenticated ||
            (_nativeOwnerId != null &&
                auth.boundNativeAccountId != _nativeOwnerId))) {
      lock();
    }
  }

  @override
  void dispose() {
    _authService?.removeListener(_handleAuthChanged);
    super.dispose();
  }
}
