import 'dart:convert';
import 'dart:developer' as developer;

import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import 'package:uuid/uuid.dart';

import '../data/drift/patient_vault_scope.dart';

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

typedef AuthFailureLogger = void Function(
  String operation,
  String errorType,
  StackTrace stackTrace,
);

enum RegistrationFailureCode {
  weakPassword,
  accountExists,
  rejected,
}

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
  return RegistrationFailure(
    RegistrationFailureCode.rejected,
    statusCode,
  );
}

class AuthService extends ChangeNotifier {
  static const _tokenKey = 'iamina_native_access_token';
  // Authenticated native ID and exact bearer must match. Legacy bearer: unknown ID.
  static const _nativeIdentityKey = 'iamina_native_account_binding_v1';
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
  // Increment on a new remote attempt or explicit local identity transition.
  // A delayed HTTP response must never reopen a superseded patient's vault.
  int _authAttemptSequence = 0;

  void _requireCurrentAuthAttempt(int attempt) {
    if (attempt != _authAttemptSequence) {
      throw StateError('Superseded authentication response');
    }
  }

  AuthService({
    FirebaseAuth? auth,
    FlutterSecureStorage? storage,
    http.Client? httpClient,
    AuthFailureLogger? failureLogger,
  })  : _firebaseAuth = _getAuthInstance(
          auth,
          failureLogger ?? _defaultFailureLogger,
        ),
        _storage = storage ?? const FlutterSecureStorage(),
        _httpClient = httpClient ?? http.Client(),
        _failureLogger = failureLogger ?? _defaultFailureLogger;

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

  /// Offline, fail-closed lookup: never invent a remote identity from a local
  /// marker, Firebase hash, old bearer, or previous owner's SQLite profile.
  /// Selecting a vault is not proof of an active server login/app-lock unlock.
  Future<PatientVaultScope?> resolvePatientVaultScope() async {
    if (!_initialized) {
      throw StateError('Authentication must be initialized');
    }
    if (_auditSession) return PatientVaultScope.auditOnly();
    if (_nativeToken != null) {
      final accountId = _nativeAccountId;
      return accountId == null
          ? null
          : PatientVaultScope.nativeDjango(accountId);
    }
    if (_firebaseAuth?.currentUser != null) return null;
    if (!_localSessionEnrolled) return null;
    final deviceId = await _storage.read(key: _localDeviceIdKey);
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
    final deviceId = await _storage.read(key: _localDeviceIdKey);
    if (deviceId == null) return null;
    try {
      return PatientVaultScope.deviceLocal(deviceId);
    } on ArgumentError {
      return null;
    }
  }

  Future<void> initialize() async {
    try {
      _localSessionEnrolled =
          await _storage.read(key: _localSessionKey) == _localSessionValue;
      final storedToken = await _storage.read(key: _tokenKey);
      if (_isExpectedNativeBearerShape(storedToken)) {
        _nativeToken = storedToken;
        _nativeAccountId = null;
        // Local-first startup: no network required to validate a cached binding.
        final binding = await _storage.read(key: _nativeIdentityKey);
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
            // Invalid cached binding must never become a patient ID.
          }
        }
        _remoteCredentialVerified = false;
        await _ensureLocalEnrollment();
      } else if (storedToken != null) {
        await _storage.delete(key: _tokenKey);
        await _storage.delete(key: _nativeIdentityKey);
        _nativeToken = null;
        _nativeAccountId = null;
        _remoteCredentialVerified = false;
      }
    } catch (error, stackTrace) {
      _failureLogger(
        'initialize',
        error.runtimeType.toString(),
        stackTrace,
      );
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
    ++_authAttemptSequence;
    if (!_initialized) {
      throw StateError('Local enrollment requires initialized authentication');
    }
    final existingId = await _storage.read(key: _localDeviceIdKey);
    if (existingId == null || existingId.isEmpty) {
      await _storage.write(key: _localDeviceIdKey, value: const Uuid().v4());
    }
    await _ensureLocalEnrollment();
    _remoteCredentialVerified = false;
    _notifyAuthChanged();
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
      await _storage.delete(key: _tokenKey);
      await _storage.delete(key: _nativeIdentityKey);
      return null;
    }
    return _firebaseAuth?.currentUser?.getIdToken(true);
  }

  Future<void> signInWithEmail(String email, String password) async {
    final attempt = ++_authAttemptSequence;
    final normalized = email.trim().toLowerCase();
    final nativeResponse = await _postJson(
      '/api/v1/auth/login',
      {'email': normalized, 'password': password},
    );
    _requireCurrentAuthAttempt(attempt);
    if (nativeResponse.statusCode >= 200 && nativeResponse.statusCode < 300) {
      await _acceptAuthResponse(nativeResponse);
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
      final exchange = await _postJson(
        '/api/v1/auth/firebase',
        {'id_token': firebaseToken},
      );
      _requireCurrentAuthAttempt(attempt);
      if (exchange.statusCode >= 200 && exchange.statusCode < 300) {
        await _acceptAuthResponse(exchange);
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
    final response = await _postJson(
      '/api/v1/auth/register',
      {'email': email.trim().toLowerCase(), 'password': password},
    );
    _requireCurrentAuthAttempt(attempt);
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw registrationFailureForStatus(response.statusCode);
    }
    await _acceptAuthResponse(response);
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
    await _storage.delete(key: _tokenKey);
    await _storage.delete(key: _nativeIdentityKey);
    await _storage.delete(key: _localSessionKey);
    // Preserve the stable local-only vault locator: deleting it orphaned
    // offline clinical records without removing their SQLite database.
    // The revoked session cannot resolve it until explicit re-enrollment;
    // the existing app-lock remains mandatory for reopening the vault.
    await _firebaseAuth?.signOut();

    if (token != null) {
      try {
        await _httpClient.post(
          Uri.parse('$kAuthBaseUrl/api/v1/auth/logout'),
          headers: {'Authorization': 'Bearer $token'},
        );
      } catch (error, stackTrace) {
        _failureLogger(
          'logout',
          error.runtimeType.toString(),
          stackTrace,
        );
      }
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
    final response = await _postJson(
      '/api/v1/auth/password/reset/request',
      {'email': email.trim().toLowerCase()},
    );
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw StateError('Password recovery request failed');
    }
  }

  Future<void> confirmPasswordReset({
    required String uid,
    required String token,
    required String newPassword,
  }) async {
    final response = await _postJson(
      '/api/v1/auth/password/reset/confirm',
      {'uid': uid, 'token': token, 'new_password': newPassword},
    );
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

  Future<void> _acceptAuthResponse(http.Response response) async {
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
    // A completed native response retires any previous local/remote account
    // before the first persistence await. Failures leave no old patient open.
    _nativeToken = null;
    _nativeAccountId = null;
    _remoteCredentialVerified = false;
    _localSessionEnrolled = false;
    _auditSession = false;
    _notifyAuthChanged();
    // Write binding first. Interrupted writes cannot pair a new token
    // with a previous account's cached patient ID.
    await _storage.write(
      key: _nativeIdentityKey,
      value: jsonEncode({'token': token, 'user_id': id}),
    );
    await _storage.write(key: _tokenKey, value: token);
    await _storage.write(key: _localSessionKey, value: _localSessionValue);
    _nativeToken = token;
    _nativeAccountId = id;
    _localSessionEnrolled = true;
    _remoteCredentialVerified = true;
    _notifyAuthChanged();
  }

  void _notifyAuthChanged() {
    AuthEpoch.advance();
    notifyListeners();
  }

  @override
  void dispose() {
    _httpClient.close();
    super.dispose();
  }
}
