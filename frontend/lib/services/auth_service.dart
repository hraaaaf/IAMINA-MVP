import 'dart:async';
import 'dart:convert';
import 'dart:developer' as developer;

import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import 'package:uuid/uuid.dart';

import '../data/drift/patient_vault_scope.dart';

import 'auth_storage_change_stub.dart'
    if (dart.library.html) 'auth_storage_change_web.dart'
    as storage_events;
import 'auth_epoch.dart';
import 'firebase_migration_policy.dart';

const String kAuthBaseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'http://localhost:8000',
);

const bool kOfflineDemo = bool.fromEnvironment(
  'IAMINA_OFFLINE_DEMO',
  defaultValue: false,
);

const bool kRemoteAccountEnrollmentEnabled = bool.fromEnvironment(
  'IAMINA_REMOTE_ACCOUNT_ENROLLMENT',
  defaultValue: false,
);

bool demoUsesLocalAuditSession({
  required bool offlineDemo,
  required bool remoteAccountEnrollmentEnabled,
}) => offlineDemo || remoteAccountEnrollmentEnabled;

typedef AuthFailureLogger =
    void Function(String operation, String errorType, StackTrace stackTrace);

enum RegistrationFailureCode { weakPassword, accountExists, rejected }

class RegistrationFailure implements Exception {
  final RegistrationFailureCode code;
  final int statusCode;

  const RegistrationFailure(this.code, this.statusCode);
}

RegistrationFailure registrationFailureForStatus(int statusCode) {
  if (statusCode == 400) {
    return RegistrationFailure(
      RegistrationFailureCode.weakPassword,
      statusCode,
    );
  }
  if (statusCode == 409) {
    return RegistrationFailure(
      RegistrationFailureCode.accountExists,
      statusCode,
    );
  }
  return RegistrationFailure(RegistrationFailureCode.rejected, statusCode);
}

class AuthService extends ChangeNotifier {
  static const _tokenKey = 'iamina_native_access_token';
  // Authenticated native ID and exact bearer must match. Legacy bearer: unknown ID.
  static const _nativeIdentityKey = 'iamina_native_account_binding_v1';
  // A durable denial marker; sign-out writes this before best-effort deletes.
  // If storage writes themselves fail, a safe restart cannot be guaranteed.
  static const _revokedSessionMarkerKey = 'iamina_web_session_revoked_v1';
  static const _localSessionKey = 'iamina_local_session_v1';
  static const _localSessionValue = 'enrolled';
  static const _localDeviceIdKey = 'iamina_local_device_id_v1';
  static final RegExp _nativeBearerShape = RegExp(
    r'^iamina\.[A-Za-z0-9_.-]+:[A-Za-z0-9]+:[A-Za-z0-9_-]+$',
  );

  final FirebaseAuth? _firebaseAuth;
  final FlutterSecureStorage _storage;
  final http.Client _httpClient;
  final AuthFailureLogger _failureLogger;
  String? _nativeToken;
  int? _nativeAccountId;
  bool _localSessionEnrolled = false;
  bool _initialized = false;
  bool _auditSession = false;
  bool _remoteCredentialVerified = false;
  // W02: invalidates HTTP responses and storage commits after a new attempt,
  // logout or explicit switch of local identity.
  int _authAttemptSequence = 0;
  // Serializes credential writes and removal on this service instance.
  Future<void> _credentialMutationTail = Future<void>.value();
  late final VoidCallback _detachAuthStorageChanges;

  void _requireCurrentAuthAttempt(int attempt) {
    if (attempt != _authAttemptSequence) {
      throw StateError('Superseded authentication operation');
    }
  }

  Future<void> _serializeCredentialMutation(Future<void> Function() mutation) {
    final pending = _credentialMutationTail.then((_) => mutation());
    // Keep the serial queue usable even when a single operation fails.
    _credentialMutationTail = pending.then<void>(
      (_) {},
      onError: (Object _, StackTrace __) {},
    );
    return pending;
  }

  AuthService({
    FirebaseAuth? auth,
    FlutterSecureStorage? storage,
    http.Client? httpClient,
    AuthFailureLogger? failureLogger,
  }) : _firebaseAuth = _getAuthInstance(
         auth,
         failureLogger ?? _defaultFailureLogger,
       ),
       _storage = storage ?? const FlutterSecureStorage(),
       _httpClient = httpClient ?? http.Client(),
       _failureLogger = failureLogger ?? _defaultFailureLogger {
    _detachAuthStorageChanges = storage_events.watchAuthStorageChanges(() {
      if (_nativeToken != null) {
        unawaited(_verifyCurrentWebRemotePrincipal());
      }
    });
  }

  static FirebaseAuth? _getAuthInstance(
    FirebaseAuth? provided,
    AuthFailureLogger failureLogger,
  ) {
    if (!kFirebaseMigrationEnabled) return null;
    try {
      return provided ?? FirebaseAuth.instance;
    } catch (error, stackTrace) {
      failureLogger(
        'firebase_instance',
        error.runtimeType.toString(),
        stackTrace,
      );
      return null;
    }
  }

  static void _defaultFailureLogger(
    String operation,
    String errorType,
    StackTrace stackTrace,
  ) {
    developer.log(
      'Safe auth fallback invoked for $errorType.',
      name: 'iamina.auth.$operation',
      stackTrace: stackTrace,
    );
  }

  static bool _isExpectedNativeBearerShape(String? token) =>
      token != null && _nativeBearerShape.hasMatch(token);

  static int get authEpoch => AuthEpoch.value;

  bool get isInitialized => _initialized;
  bool get isAuthenticated =>
      _auditSession ||
      _localSessionEnrolled ||
      (_firebaseAuth?.currentUser != null);
  bool get isRemoteCredentialVerified => _remoteCredentialVerified;

  /// Previously authenticated Django ID bound to this exact bearer.
  /// Offline restoration does not verify that the bearer is still active.
  int? get boundNativeAccountId =>
      _auditSession || _nativeToken == null ? null : _nativeAccountId;
  bool get hasRemoteApiCredential =>
      _nativeToken != null && _nativeToken!.isNotEmpty;
  bool get isAnonymous =>
      _auditSession ||
      (!_localSessionEnrolled &&
          _nativeToken == null &&
          (_firebaseAuth?.currentUser?.isAnonymous ?? false));
  bool get isAuditSession => _auditSession;
  User? get firebaseUser => _firebaseAuth?.currentUser;

  // Browser tabs have separate in-memory identity but shared secure storage.
  // Revalidate persisted owner immediately before token egress / vault choice.
  Future<bool> _verifyCurrentWebRemotePrincipal() async {
    if (!kIsWeb || _nativeToken == null) return true;
    final attempt = _authAttemptSequence;
    final capturedToken = _nativeToken;
    final capturedAccount = _nativeAccountId;
    var valid = false;
    try {
      final revoked = await _storage.read(key: _revokedSessionMarkerKey);
      final storedToken = await _storage.read(key: _tokenKey);
      final binding = await _storage.read(key: _nativeIdentityKey);
      if (binding != null) {
        final parsed = jsonDecode(binding);
        valid =
            revoked == null &&
            storedToken == capturedToken &&
            parsed is Map<String, dynamic> &&
            parsed['token'] == capturedToken &&
            parsed['user_id'] == capturedAccount &&
            capturedAccount != null;
      }
    } catch (_) {
      // Failure to check stored identity must refuse the cached credential.
      valid = false;
    }
    if (attempt != _authAttemptSequence || _nativeToken != capturedToken) {
      return false;
    }
    if (!valid) {
      ++_authAttemptSequence;
      _nativeToken = null;
      _nativeAccountId = null;
      _localSessionEnrolled = false;
      _remoteCredentialVerified = false;
      _notifyAuthChanged();
    }
    return valid;
  }

  /// Offline, fail-closed lookup: never invent a remote identity from a local
  /// marker, Firebase hash, old bearer, or previous owner's SQLite profile.
  /// Selecting a vault is not proof of an active server login/app-lock unlock.
  Future<PatientVaultScope?> resolvePatientVaultScope() async {
    if (!_initialized) {
      throw StateError('Authentication must be initialized');
    }
    if (_auditSession) return PatientVaultScope.auditOnly();
    if (!await _verifyCurrentWebRemotePrincipal()) return null;
    if (_nativeToken != null) {
      final accountId = _nativeAccountId;
      return accountId == null
          ? null
          : PatientVaultScope.nativeDjango(accountId);
    }
    if (_firebaseAuth?.currentUser != null) return null;
    if (!_localSessionEnrolled) return null;
    final attempt = _authAttemptSequence;
    final deviceId = await _storage.read(key: _localDeviceIdKey);
    if (attempt != _authAttemptSequence ||
        _auditSession ||
        !_localSessionEnrolled ||
        _nativeToken != null) {
      return null;
    }
    if (deviceId == null) return null;
    try {
      return PatientVaultScope.deviceLocal(deviceId);
    } on ArgumentError {
      return null;
    }
  }

  /// Inspect a dormant device-only vault for lock-recovery purposes only.
  /// This does NOT enroll a user or grant access to patient data.
  Future<PatientVaultScope?> dormantDeviceVaultForProtectedStateProbe() async {
    if (!_initialized || _auditSession) return null;
    final attempt = _authAttemptSequence;
    final deviceId = await _storage.read(key: _localDeviceIdKey);
    if (attempt != _authAttemptSequence || _auditSession) return null;
    if (deviceId == null) return null;
    try {
      return PatientVaultScope.deviceLocal(deviceId);
    } on ArgumentError {
      return null;
    }
  }

  Future<void> initialize() async {
    final attempt = ++_authAttemptSequence;
    try {
      // Reads can also race with sign-out; the same queue protects restore.
      await _serializeCredentialMutation(() async {
        _requireCurrentAuthAttempt(attempt);
        final revoked = await _storage.read(key: _revokedSessionMarkerKey);
        _requireCurrentAuthAttempt(attempt);
        if (revoked != null) {
          // Deletion may have failed before restart. Deny token AND local vault.
          _nativeToken = null;
          _nativeAccountId = null;
          _localSessionEnrolled = false;
          _remoteCredentialVerified = false;
          return;
        }
        final local = await _storage.read(key: _localSessionKey);
        _requireCurrentAuthAttempt(attempt);
        final storedToken = await _storage.read(key: _tokenKey);
        _requireCurrentAuthAttempt(attempt);
        // Web-only safety boundary: a cached remote bearer is not proof of a
        // current session after restart. A failed logout tombstone WRITE and
        // DELETE must never resurrect the prior patient's vault on Web.
        // Device-local sessions without a remote token retain offline support.
        if (kIsWeb && storedToken != null) {
          _nativeToken = null;
          _nativeAccountId = null;
          _localSessionEnrolled = false;
          _remoteCredentialVerified = false;
          return;
        }
        _localSessionEnrolled = local == _localSessionValue;
        if (_isExpectedNativeBearerShape(storedToken)) {
          _nativeToken = storedToken;
          _nativeAccountId = null;
          // Local-first startup does not prove the cached bearer is still valid.
          final binding = await _storage.read(key: _nativeIdentityKey);
          _requireCurrentAuthAttempt(attempt);
          if (binding != null) {
            try {
              final parsed = jsonDecode(binding);
              if (parsed is Map<String, dynamic> &&
                  parsed['token'] == storedToken &&
                  parsed['user_id'] is int &&
                  (parsed['user_id'] as int) > 0) {
                _nativeAccountId = parsed['user_id'] as int;
              }
            } on FormatException {
              // Malformed binding cannot become a patient identity.
            }
          }
          _remoteCredentialVerified = false;
          await _ensureLocalEnrollment();
          _requireCurrentAuthAttempt(attempt);
        } else if (storedToken != null) {
          await _storage.delete(key: _tokenKey);
          _requireCurrentAuthAttempt(attempt);
          await _storage.delete(key: _nativeIdentityKey);
          _requireCurrentAuthAttempt(attempt);
          _nativeToken = null;
          _nativeAccountId = null;
          _remoteCredentialVerified = false;
        }
      });
    } catch (error, stackTrace) {
      _failureLogger('initialize', error.runtimeType.toString(), stackTrace);
      _nativeToken = null;
      _nativeAccountId = null;
      _localSessionEnrolled = false;
      _remoteCredentialVerified = false;
    } finally {
      _initialized = true;
      _notifyAuthChanged();
    }
  }

  /// Enrol this installation for local-first use without contacting a server.
  /// This provides device-local continuity, not strong user authentication.
  Future<void> enrollLocalDevice() async {
    final attempt = ++_authAttemptSequence;
    if (!_initialized) {
      throw StateError('Local enrollment requires initialized authentication');
    }
    await _serializeCredentialMutation(() async {
      _requireCurrentAuthAttempt(attempt);
      final existingId = await _storage.read(key: _localDeviceIdKey);
      _requireCurrentAuthAttempt(attempt);
      if (existingId == null || existingId.isEmpty) {
        await _storage.write(key: _localDeviceIdKey, value: const Uuid().v4());
        _requireCurrentAuthAttempt(attempt);
      }
      // Explicitly leave any previous remote principal before local enrollment.
      _nativeToken = null;
      _nativeAccountId = null;
      _localSessionEnrolled = false;
      _remoteCredentialVerified = false;
      _notifyAuthChanged();
      try {
        // An earlier failed sign-out may have left A persisted. Remove both
        // credential keys BEFORE clearing the durable revocation marker.
        await _storage.delete(key: _tokenKey);
        _requireCurrentAuthAttempt(attempt);
        await _storage.delete(key: _nativeIdentityKey);
        _requireCurrentAuthAttempt(attempt);
        await _ensureLocalEnrollment();
        _requireCurrentAuthAttempt(attempt);
        await _storage.delete(key: _revokedSessionMarkerKey);
        _requireCurrentAuthAttempt(attempt);
      } catch (_) {
        _localSessionEnrolled = false;
        _notifyAuthChanged();
        rethrow;
      }
      _notifyAuthChanged();
    });
  }

  void enterAuditSession() {
    ++_authAttemptSequence;
    if (!_initialized) {
      throw StateError('Audit session requires initialized authentication');
    }
    _auditSession = true;
    _notifyAuthChanged();
  }

  Future<String?> getIdToken() async {
    if (_auditSession) return null;
    if (!await _verifyCurrentWebRemotePrincipal()) return null;
    final native = _nativeToken;
    if (native != null && native.isNotEmpty) return native;
    return _firebaseAuth?.currentUser?.getIdToken();
  }

  Future<String?> refreshToken() async {
    ++_authAttemptSequence;
    if (_auditSession) return null;
    if (_nativeToken != null) {
      _nativeToken = null;
      _nativeAccountId = null;
      _remoteCredentialVerified = false;
      // Retire the session before a storage/plugin await can resume its
      // pending clinical synchronizer under an unbound credential.
      _notifyAuthChanged();
      await _serializeCredentialMutation(() async {
        await _storage.write(key: _revokedSessionMarkerKey, value: 'revoked');
        await _storage.delete(key: _tokenKey);
        await _storage.delete(key: _nativeIdentityKey);
      });
      return null;
    }
    return _firebaseAuth?.currentUser?.getIdToken(true);
  }

  Future<void> signInWithEmail(String email, String password) async {
    final attempt = ++_authAttemptSequence;
    final normalized = email.trim().toLowerCase();
    final nativeResponse = await _postJson('/api/v1/auth/login', {
      'email': normalized,
      'password': password,
    });
    _requireCurrentAuthAttempt(attempt);
    if (nativeResponse.statusCode >= 200 && nativeResponse.statusCode < 300) {
      await _acceptAuthResponse(nativeResponse, attempt);
      return;
    }
    if (nativeResponse.statusCode == 401 && _firebaseAuth != null) {
      final credential = await _firebaseAuth.signInWithEmailAndPassword(
        email: normalized,
        password: password,
      );
      final firebaseToken = await credential.user?.getIdToken(true);
      _requireCurrentAuthAttempt(attempt);
      if (firebaseToken == null || firebaseToken.isEmpty) {
        throw StateError('Firebase migration credential unavailable');
      }
      final exchange = await _postJson('/api/v1/auth/firebase', {
        'id_token': firebaseToken,
      });
      _requireCurrentAuthAttempt(attempt);
      if (exchange.statusCode >= 200 && exchange.statusCode < 300) {
        await _acceptAuthResponse(exchange, attempt);
        return;
      }
    }
    throw StateError('Authentication failed');
  }

  Future<void> registerWithEmail(String email, String password) async {
    final attempt = ++_authAttemptSequence;
    if (!kRemoteAccountEnrollmentEnabled) {
      throw StateError('Remote account enrollment is disabled');
    }
    final response = await _postJson('/api/v1/auth/register', {
      'email': email.trim().toLowerCase(),
      'password': password,
    });
    _requireCurrentAuthAttempt(attempt);
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw registrationFailureForStatus(response.statusCode);
    }
    await _acceptAuthResponse(response, attempt);
  }

  Future<void> signOut() async {
    ++_authAttemptSequence;
    _auditSession = false;
    final token = _nativeToken;

    // Local sign-out is authoritative. Never let optional remote revocation keep
    // an enrolled device authenticated while the network is slow or unavailable.
    _nativeToken = null;
    _nativeAccountId = null;
    _localSessionEnrolled = false;
    _remoteCredentialVerified = false;
    // Cancel stale session egress SYNCHRONOUSLY. Awaiting secure storage first
    // left an A→logout window where old SyncService still had A's epoch.
    _notifyAuthChanged();
    Object? storageError;
    StackTrace? storageStack;
    Future<void> attemptStore(Future<void> Function() operation) async {
      try {
        await operation();
      } catch (error, stack) {
        storageError ??= error;
        storageStack ??= stack;
        _failureLogger(
          'logout_local_storage',
          error.runtimeType.toString(),
          stack,
        );
      }
    }

    await _serializeCredentialMutation(() async {
      // Continue deleting credentials even when marker WRITE fails.
      await attemptStore(
        () => _storage.write(key: _revokedSessionMarkerKey, value: 'revoked'),
      );
      await attemptStore(() => _storage.delete(key: _tokenKey));
      await attemptStore(() => _storage.delete(key: _nativeIdentityKey));
      await attemptStore(() => _storage.delete(key: _localSessionKey));
    });
    // Stable device-only vault locator remains for protected local recovery.
    try {
      await _firebaseAuth?.signOut();
    } catch (error, stack) {
      storageError ??= error;
      storageStack ??= stack;
      _failureLogger('logout_firebase', error.runtimeType.toString(), stack);
    }
    // Best-effort remote revocation is attempted after storage failure too.
    if (token != null) {
      try {
        final response = await _httpClient.post(
          Uri.parse('$kAuthBaseUrl/api/v1/auth/logout'),
          headers: {'Authorization': 'Bearer $token'},
        );
        if (response.statusCode < 200 || response.statusCode >= 300) {
          _failureLogger(
            'logout_remote_status',
            'HTTP_${response.statusCode}',
            StackTrace.current,
          );
        }
      } catch (error, stackTrace) {
        _failureLogger('logout', error.runtimeType.toString(), stackTrace);
      }
    }
    if (storageError != null) {
      Error.throwWithStackTrace(storageError!, storageStack!);
    }
  }

  Future<void> signInAnonymously() async {
    if (demoUsesLocalAuditSession(
      offlineDemo: kOfflineDemo,
      remoteAccountEnrollmentEnabled: kRemoteAccountEnrollmentEnabled,
    )) {
      enterAuditSession();
      return;
    }
    if (_firebaseAuth == null) {
      throw StateError('Firebase migration is disabled');
    }
    await _firebaseAuth.signInAnonymously();
    _notifyAuthChanged();
  }

  Future<void> sendPasswordResetEmail(String email) async {
    final response = await _postJson('/api/v1/auth/password/reset/request', {
      'email': email.trim().toLowerCase(),
    });
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw StateError('Password recovery request failed');
    }
  }

  Future<void> confirmPasswordReset({
    required String uid,
    required String token,
    required String newPassword,
  }) async {
    final response = await _postJson('/api/v1/auth/password/reset/confirm', {
      'uid': uid,
      'token': token,
      'new_password': newPassword,
    });
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw StateError('Password recovery confirmation failed');
    }
  }

  Future<void> _ensureLocalEnrollment() async {
    if (_localSessionEnrolled) return;
    await _storage.write(key: _localSessionKey, value: _localSessionValue);
    _localSessionEnrolled = true;
  }

  Future<http.Response> _postJson(String path, Map<String, dynamic> body) {
    return _httpClient.post(
      Uri.parse('$kAuthBaseUrl$path'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(body),
    );
  }

  Future<void> _acceptAuthResponse(http.Response response, int attempt) async {
    _requireCurrentAuthAttempt(attempt);
    final payload = jsonDecode(response.body);
    if (payload is! Map<String, dynamic>) {
      throw StateError('Malformed authentication response');
    }
    final token = payload['access_token'];
    final user = payload['user'];
    final id = user is Map<String, dynamic> ? user['id'] : null;
    if (token is! String || !_isExpectedNativeBearerShape(token)) {
      throw StateError('Missing IAMINA access token');
    }
    if (id is! int || id <= 0) {
      throw StateError('Missing authenticated IAMINA user ID');
    }
    await _serializeCredentialMutation(() async {
      _requireCurrentAuthAttempt(attempt);
      // Remove the previous principal before any credential write awaits.
      _nativeToken = null;
      _nativeAccountId = null;
      _remoteCredentialVerified = false;
      _localSessionEnrolled = false;
      _auditSession = false;
      _notifyAuthChanged();
      try {
        // Binding-first + token-last. Revalidate after every plugin await.
        await _storage.write(
          key: _nativeIdentityKey,
          value: jsonEncode({'token': token, 'user_id': id}),
        );
        _requireCurrentAuthAttempt(attempt);
        await _storage.write(key: _localSessionKey, value: _localSessionValue);
        _requireCurrentAuthAttempt(attempt);
        await _storage.write(key: _tokenKey, value: token);
        _requireCurrentAuthAttempt(attempt);
        // Only a fully persisted, current authentication may clear a prior
        // logout tombstone. Failure preserves denial across browser restart.
        await _storage.delete(key: _revokedSessionMarkerKey);
        _requireCurrentAuthAttempt(attempt);
        // In-memory bearer is the last commit marker; never before validation.
        _nativeToken = token;
        _nativeAccountId = id;
        _localSessionEnrolled = true;
        _remoteCredentialVerified = true;
        _notifyAuthChanged();
      } catch (_) {
        // Best effort. Serialized logout/next-login remains authoritative.
        _nativeToken = null;
        _nativeAccountId = null;
        _localSessionEnrolled = false;
        _remoteCredentialVerified = false;
        _notifyAuthChanged();
        try {
          await _storage.delete(key: _tokenKey);
          await _storage.delete(key: _nativeIdentityKey);
          await _storage.delete(key: _localSessionKey);
        } catch (error, stackTrace) {
          _failureLogger(
            'credential_cleanup',
            error.runtimeType.toString(),
            stackTrace,
          );
        }
        rethrow;
      }
    });
  }

  void _notifyAuthChanged() {
    AuthEpoch.advance();
    notifyListeners();
  }

  @override
  void dispose() {
    _detachAuthStorageChanges();
    _httpClient.close();
    super.dispose();
  }
}
