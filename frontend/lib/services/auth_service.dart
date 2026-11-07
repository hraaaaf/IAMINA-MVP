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

// Sign-in to existing synthetic accounts is independent of account creation.
// Production retains its existing behavior through this default.
const bool kRemoteAccountSignInEnabled = bool.fromEnvironment(
  'IAMINA_REMOTE_ACCOUNT_SIGN_IN',
  defaultValue: kRemoteAccountEnrollmentEnabled,
);

/// For remote Web sign-in, always use the *current page's* exact origin.
/// Vercel immutable Preview URLs differ from branch aliases; sending login
/// credentials to an older alias breaks same-origin BFF/OIDC and CORS.
/// Non-Web or local-first clients preserve their configured transport.
String resolveAuthApiOrigin({
  required bool isWeb,
  required bool remoteAccountLogin,
  required Uri pageUri,
  required String configuredBaseUrl,
  bool useConfiguredLoopbackBackend = false,
}) {
  if (!isWeb || !remoteAccountLogin) return configuredBaseUrl;
  final host = pageUri.host.toLowerCase();
  final local = pageUri.scheme == 'http' &&
      (host == 'localhost' || host == '127.0.0.1');
  if (local && useConfiguredLoopbackBackend) {
    // Local D11 FUE serves Flutter on one loopback port and Django on another.
    // This exception never applies to a hosted Preview. Never forward patient
    // credentials from a local page to an arbitrary remote backend.
    final backend = Uri.tryParse(configuredBaseUrl);
    if (backend == null ||
        backend.scheme != 'http' ||
        (backend.host != 'localhost' && backend.host != '127.0.0.1') ||
        backend.userInfo.isNotEmpty) {
      throw StateError('Local remote login requires a loopback backend');
    }
    return configuredBaseUrl;
  }
  if (pageUri.scheme != 'https' && !local) {
    throw StateError('A secure browser origin is required for remote login');
  }
  if (host.isEmpty || pageUri.userInfo.isNotEmpty) {
    throw StateError('Missing secure patient origin');
  }
  return pageUri.origin;
}

/// Do not conflate invalid credentials (HTTP 401) with API or network faults.
class AuthCredentialsRejected implements Exception {
  const AuthCredentialsRejected();
}

class AuthSignInServiceUnavailable implements Exception {
  final int statusCode;
  const AuthSignInServiceUnavailable(this.statusCode);
}

/// Only the Django-native rejection is evidence of incorrect credentials.
/// A Vercel SSO/OIDC 401 or HTML protection page must be reported as an
/// unavailable service, never as a wrong patient password.
bool _isNativeCredentialRejection(http.Response response) {
  if (response.statusCode != 401) return false;
  try {
    final payload = jsonDecode(response.body);
    return payload is Map &&
        payload['detail'] == 'Invalid authentication credential';
  } catch (_) {
    return false;
  }
}


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
  // Durable fail-closed fence: retained when interrupted secure-storage
  // cleanup leaves a bearer that must never be restored on next startup.
  static const _logoutPendingKey = 'iamina_auth_logout_pending_v1';
  static const _logoutPendingValue = 'revoked';
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
  // null: no remote bearer at logout; true: HTTP 2xx confirmed; false:
  // remote revocation unconfirmed (offline, transport error, or HTTP failure).
  // This reports an observation, not a guarantee of crash-safe session expiry.
  bool? _lastRemoteLogoutConfirmed;
  // One Dart isolate can host multiple AuthService objects backed by the
  // same persisted credentials. Ordering and intent must span those objects:
  // an instance-local queue lets a sibling sign-out lose to a paused login.
  // This does NOT synchronize separate browser tabs / JS isolates.
  static int _credentialIntent = 0;
  // Keep only active writes in the shared queue. Retaining a completed Future
  // permanently would also retain its old async-zone boundary (notably in
  // sequential Flutter widget tests).
  static Future<void>? _credentialMutationTail;
  // A sign-out must also retire credentials already published by sibling
  // AuthService objects. Weak references avoid retaining unused instances.
  // Scope: one Dart isolate; browser tabs require a separate security design.
  static final List<WeakReference<AuthService>> _liveInstances = [];
  bool _disposed = false;

  static void _revokePublishedSessionsInIsolate() {
    for (final reference in List<WeakReference<AuthService>>.of(_liveInstances)) {
      final service = reference.target;
      if (service == null || service._disposed) {
        _liveInstances.remove(reference);
        continue;
      }
      service._auditSession = false;
      service._nativeToken = null;
      service._nativeAccountId = null;
      service._localSessionEnrolled = false;
      service._remoteCredentialVerified = false;
      // Notify each owner so its own observers/egress stop immediately.
      service._notifyAuthChanged();
    }
  }

  Future<T> _serializeCredentials<T>(Future<T> Function() mutation) {
    final previous = _credentialMutationTail;
    final result = (previous ?? Future<void>.value()).then((_) => mutation());
    // Keep the queue usable after a rejected/stale login or storage exception.
    final settled = result.then<void>(
      (_) {},
      onError: (Object _, StackTrace __) {},
    );
    _credentialMutationTail = settled;
    settled.whenComplete(() {
      if (identical(_credentialMutationTail, settled)) {
        _credentialMutationTail = null;
      }
    });
    return result;
  }

  void _requireCurrentCredentialIntent(int intent) {
    if (intent != _credentialIntent) {
      throw StateError('Authentication request superseded');
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
        _failureLogger = failureLogger ?? _defaultFailureLogger {
    _liveInstances.add(WeakReference<AuthService>(this));
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
  bool? get lastRemoteLogoutConfirmed => _lastRemoteLogoutConfirmed;
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
    // A device-ID read can resolve from an older storage snapshot after a
    // sign-out or account transition. Never return that revoked vault.
    final intent = _credentialIntent;
    final epoch = AuthEpoch.value;
    final deviceId = await _storage.read(key: _localDeviceIdKey);
    if (intent != _credentialIntent ||
        epoch != AuthEpoch.value ||
        !_initialized ||
        _auditSession ||
        !_localSessionEnrolled ||
        _nativeToken != null ||
        _firebaseAuth?.currentUser != null ||
        deviceId == null) {
      return null;
    }
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
    final intent = _credentialIntent;
    final epoch = AuthEpoch.value;
    final deviceId = await _storage.read(key: _localDeviceIdKey);
    // This probe does not unlock clinical data, but must not publish a stale
    // locator if logout or a newer session transition occurred mid-read.
    if (intent != _credentialIntent ||
        epoch != AuthEpoch.value ||
        !_initialized ||
        _auditSession ||
        deviceId == null) {
      return null;
    }
    try {
      return PatientVaultScope.deviceLocal(deviceId);
    } on ArgumentError {
      return null;
    }
  }

  Future<void> initialize() async {
    // Read-only hydration must not block sign-out: a secure-storage read can
    // remain suspended while logout must finish its cleanup immediately.
    // Stage the snapshot and commit it only if no newer auth intent won.
    final intent = _credentialIntent;
    try {
      final pendingRevocation = await _storage.read(key: _logoutPendingKey);
      _requireCurrentCredentialIntent(intent);
      if (pendingRevocation != null) {
        // A previous logout may have failed while erasing a persisted token.
        // Retry the full cleanup before reading any bearer or vault marker.
        // Keep the fence if *any* delete fails, so subsequent startups remain
        // fail-closed instead of reviving the old authenticated account.
        await _serializeCredentials(() async {
          _requireCurrentCredentialIntent(intent);
          await _storage.delete(key: _tokenKey);
          await _storage.delete(key: _nativeIdentityKey);
          await _storage.delete(key: _localSessionKey);
          await _storage.delete(key: _logoutPendingKey);
          _requireCurrentCredentialIntent(intent);
          _nativeToken = null;
          _nativeAccountId = null;
          _localSessionEnrolled = false;
          _remoteCredentialVerified = false;
        });
        return;
      }

      final enrolled =
          await _storage.read(key: _localSessionKey) == _localSessionValue;
      _requireCurrentCredentialIntent(intent);
      final storedToken = await _storage.read(key: _tokenKey);
      _requireCurrentCredentialIntent(intent);
      String? binding;
      if (_isExpectedNativeBearerShape(storedToken)) {
        // Local-first startup: no network required to validate a cached binding.
        binding = await _storage.read(key: _nativeIdentityKey);
        _requireCurrentCredentialIntent(intent);
      }

      // The only hydration writes/publication are ordered with signOut. If a
      // newer logout happened during a read, reject the old snapshot before
      // it can re-enrol a device or restore a previous owner's bearer.
      await _serializeCredentials(() async {
        _requireCurrentCredentialIntent(intent);
        _localSessionEnrolled = enrolled;
        _nativeToken = null;
        _nativeAccountId = null;
        _remoteCredentialVerified = false;
        if (_isExpectedNativeBearerShape(storedToken)) {
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
          await _ensureLocalEnrollment();
          _requireCurrentCredentialIntent(intent);
          _nativeToken = storedToken;
        } else if (storedToken != null) {
          await _storage.delete(key: _tokenKey);
          _requireCurrentCredentialIntent(intent);
          await _storage.delete(key: _nativeIdentityKey);
          _requireCurrentCredentialIntent(intent);
        }
      });
    } catch (error, stackTrace) {
      _failureLogger(
        'initialize',
        error.runtimeType.toString(),
        stackTrace,
      );
      // An older failed initialize must not erase a newer successful sign-in.
      // A newer sign-out already synchronously retired these credentials.
      if (intent == _credentialIntent) {
        _nativeToken = null;
        _nativeAccountId = null;
        _localSessionEnrolled = false;
        _remoteCredentialVerified = false;
      }
    } finally {
      _initialized = true;
      _notifyAuthChanged();
    }
  }

  /// Enrol this installation for local-first use without contacting a server.
  /// This provides device-local continuity, not strong user authentication.
  Future<void> enrollLocalDevice() async {
    if (!_initialized) {
      throw StateError('Local enrollment requires initialized authentication');
    }
    // Local enrollment is an auth intent too. Do not let an older, suspended
    // local marker write outlive sign-out or a newer remote sign-in.
    final intent = ++_credentialIntent;
    await _serializeCredentials(() async {
      _requireCurrentCredentialIntent(intent);
      final existingId = await _storage.read(key: _localDeviceIdKey);
      _requireCurrentCredentialIntent(intent);
      if (existingId == null || existingId.isEmpty) {
        await _storage.write(key: _localDeviceIdKey, value: const Uuid().v4());
        _requireCurrentCredentialIntent(intent);
      }
      await _ensureLocalEnrollment();
      _requireCurrentCredentialIntent(intent);
      _remoteCredentialVerified = false;
      _notifyAuthChanged();
    });
  }

  void enterAuditSession() {
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
    if (_auditSession) return null;
    if (_nativeToken != null) {
      _nativeToken = null;
      _nativeAccountId = null;
      _remoteCredentialVerified = false;
      // Retire the session before a storage/plugin await can resume its
      // pending clinical synchronizer under an unbound credential.
      _notifyAuthChanged();
      await _serializeCredentials(() async {
        await _storage.delete(key: _tokenKey);
        await _storage.delete(key: _nativeIdentityKey);
      });
      return null;
    }
    return _firebaseAuth?.currentUser?.getIdToken(true);
  }

  Future<void> signInWithEmail(String email, String password) async {
    final intent = ++_credentialIntent;
    final normalized = email.trim().toLowerCase();
    final nativeResponse = await _postJson(
      '/api/v1/auth/login',
      {'email': normalized, 'password': password},
    );
    if (nativeResponse.statusCode >= 200 && nativeResponse.statusCode < 300) {
      await _acceptAuthResponse(nativeResponse, intent);
      return;
    }
    final nativeInvalidCredentials = _isNativeCredentialRejection(nativeResponse);
    if (nativeInvalidCredentials && _firebaseAuth != null) {
      final credential = await _firebaseAuth.signInWithEmailAndPassword(
        email: normalized,
        password: password,
      );
      final firebaseToken = await credential.user?.getIdToken(true);
      if (firebaseToken == null || firebaseToken.isEmpty) {
        throw StateError('Firebase migration credential unavailable');
      }
      final exchange = await _postJson(
        '/api/v1/auth/firebase',
        {'id_token': firebaseToken},
      );
      if (exchange.statusCode >= 200 && exchange.statusCode < 300) {
        await _acceptAuthResponse(exchange, intent);
        return;
      }
    }
    if (nativeInvalidCredentials) {
      throw const AuthCredentialsRejected();
    }
    throw AuthSignInServiceUnavailable(nativeResponse.statusCode);
  }

  Future<void> registerWithEmail(String email, String password) async {
    if (!kRemoteAccountEnrollmentEnabled) {
      throw StateError('Remote account enrollment is disabled');
    }
    final intent = ++_credentialIntent;
    final response = await _postJson(
      '/api/v1/auth/register',
      {'email': email.trim().toLowerCase(), 'password': password},
    );
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw registrationFailureForStatus(response.statusCode);
    }
    await _acceptAuthResponse(response, intent);
  }

  Future<void> signOut() async {
    // Synchronous cancellation, before waiting for any persistent operation.
    ++_credentialIntent;
    final token = _nativeToken;
    _lastRemoteLogoutConfirmed = token == null ? null : false;

    // The token may already be published by *another* AuthService on this
    // isolate. Clear every live owner's in-memory authority before any await.
    // Also notifies each owner to cancel its own cached clinical egress.
    _revokePublishedSessionsInIsolate();
    Object? storageFailure;
    StackTrace? storageFailureStack;
    try {
      await _serializeCredentials(() async {
        // Commit the revocation fence *before* attempting non-atomic deletes.
        // If erasure fails, recovery on the next initialize sees this fence.
        // Never delete the stable local device vault identifier.
        try {
          await _storage.write(
            key: _logoutPendingKey,
            value: _logoutPendingValue,
          );
        } catch (fenceError, fenceStackTrace) {
          // A failed fence write must NOT prevent still-available credential
          // erasure. Try every deletion even when one fails, to avoid leaving
          // a local enrollment or bound identity behind unnecessarily.
          Object? firstDeleteError;
          StackTrace? firstDeleteStack;
          for (final key in <String>[
            _tokenKey,
            _nativeIdentityKey,
            _localSessionKey,
          ]) {
            try {
              await _storage.delete(key: key);
            } catch (deleteError, deleteStackTrace) {
              firstDeleteError ??= deleteError;
              firstDeleteStack ??= deleteStackTrace;
            }
          }
          // Never pretend that a failed durable fence is safe. If both the
          // fence write and credential deletion fail, a future process restart
          // remains a security NO-GO without a separate durable mechanism.
          if (firstDeleteError != null) {
            Error.throwWithStackTrace(firstDeleteError, firstDeleteStack!);
          }
          Error.throwWithStackTrace(fenceError, fenceStackTrace);
        }
        await _storage.delete(key: _tokenKey);
        await _storage.delete(key: _nativeIdentityKey);
        await _storage.delete(key: _localSessionKey);
        // Only a fully completed credential cleanup may clear the fence.
        await _storage.delete(key: _logoutPendingKey);
      });
    } catch (error, stackTrace) {
      // Local persistence errors cannot suppress the independent server-side
      // revocation attempt. The in-memory session was already retired above.
      storageFailure = error;
      storageFailureStack = stackTrace;
      _failureLogger('logout_storage', error.runtimeType.toString(), stackTrace);
    }

    // Preserve the stable local-only vault locator: deleting it orphaned
    // offline clinical records without removing their SQLite database.
    // The revoked session cannot resolve it until explicit re-enrollment;
    // the existing app-lock remains mandatory for reopening the vault.
    Object? firebaseFailure;
    StackTrace? firebaseFailureStack;
    try {
      await _firebaseAuth?.signOut();
    } catch (error, stackTrace) {
      firebaseFailure = error;
      firebaseFailureStack = stackTrace;
      _failureLogger('logout_firebase', error.runtimeType.toString(), stackTrace);
    }

    Object? remoteFailure;
    StackTrace? remoteFailureStack;
    if (token != null) {
      http.Response? response;
      try {
        response = await _httpClient.post(
          Uri.parse('$_effectiveAuthBaseUrl/api/v1/auth/logout'),
          headers: {'Authorization': 'Bearer $token'},
        );
      } catch (error, stackTrace) {
        // An offline/failed transport cannot block a completed LOCAL logout.
        // Explicitly keep remote confirmation false and report observability;
        // no claim of server-side revocation is made.
        _failureLogger('logout', error.runtimeType.toString(), stackTrace);
      }
      if (response != null) {
        if (response.statusCode >= 200 && response.statusCode < 300) {
          _lastRemoteLogoutConfirmed = true;
        } else {
          // Explicit HTTP refusal is a known failed server operation, not
          // merely an unavailable transport. Keep F05B-HTTP2 fail-closed.
          final error = StateError('Remote sign-out not confirmed');
          remoteFailure = error;
          remoteFailureStack = StackTrace.current;
          _failureLogger('logout', error.runtimeType.toString(),
              remoteFailureStack);
        }
      }
    }

    // Surface incomplete cleanup/revocation to callers without undoing the
    // synchronous local denial. Separate client Web startup revalidation is
    // required: this alone cannot survive a double persistent-storage fault.
    if (storageFailure != null) {
      Error.throwWithStackTrace(storageFailure, storageFailureStack!);
    }
    if (firebaseFailure != null) {
      Error.throwWithStackTrace(firebaseFailure, firebaseFailureStack!);
    }
    if (remoteFailure != null) {
      Error.throwWithStackTrace(remoteFailure, remoteFailureStack!);
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
    final intent = _credentialIntent;
    await _storage.write(key: _localSessionKey, value: _localSessionValue);
    // A later sign-out may have invalidated this write while it was pending.
    // Never republish local enrollment after that newer auth decision.
    _requireCurrentCredentialIntent(intent);
    _localSessionEnrolled = true;
  }

  String get _effectiveAuthBaseUrl => resolveAuthApiOrigin(
        isWeb: kIsWeb,
        remoteAccountLogin: kRemoteAccountSignInEnabled,
        pageUri: Uri.base,
        configuredBaseUrl: kAuthBaseUrl,
        useConfiguredLoopbackBackend: true,
      );

  Future<http.Response> _postJson(String path, Map<String, dynamic> body) {
    return _httpClient.post(
      Uri.parse('$_effectiveAuthBaseUrl$path'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(body),
    );
  }

  Future<void> _acceptAuthResponse(http.Response response, int intent) async {
    _requireCurrentCredentialIntent(intent);
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
    await _serializeCredentials(() async {
      _requireCurrentCredentialIntent(intent);
      // Retire any previous owner before storage persistence starts.
      _nativeToken = null;
      _nativeAccountId = null;
      _remoteCredentialVerified = false;
      _localSessionEnrolled = false;
      _auditSession = false;
      _notifyAuthChanged();
      // Ordered with signOut: a delayed A write may finish, but logout's
      // queued cleanup must win. A stale operation must not publish A.
      await _storage.write(
        key: _nativeIdentityKey,
        value: jsonEncode({'token': token, 'user_id': id}),
      );
      await _storage.write(key: _tokenKey, value: token);
      await _storage.write(key: _localSessionKey, value: _localSessionValue);
      _requireCurrentCredentialIntent(intent);
      _nativeToken = token;
      _nativeAccountId = id;
      _localSessionEnrolled = true;
      _remoteCredentialVerified = true;
      _notifyAuthChanged();
    });
  }

  void _notifyAuthChanged() {
    AuthEpoch.advance();
    notifyListeners();
  }

  @override
  void dispose() {
    _disposed = true;
    _liveInstances.removeWhere(
      (reference) => reference.target == null || identical(reference.target, this),
    );
    _httpClient.close();
    super.dispose();
  }
}
