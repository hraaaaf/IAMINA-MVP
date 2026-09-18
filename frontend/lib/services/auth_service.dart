import 'dart:convert';
import 'dart:developer' as developer;

import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import 'package:uuid/uuid.dart';

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

const bool kRemoteBackendAuthRequired = bool.fromEnvironment(
  'IAMINA_REQUIRE_REMOTE_BACKEND_AUTH',
  defaultValue: false,
);

typedef AuthFailureLogger = void Function(
  String operation,
  String errorType,
  StackTrace stackTrace,
);

class AuthService extends ChangeNotifier {
  static const _tokenKey = 'iamina_native_access_token';
  static const _nativeUserIdKey = 'iamina_native_user_id';
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
  int? _nativeUserId;
  bool _localSessionEnrolled = false;
  bool _initialized = false;
  bool _auditSession = false;
  bool _remoteCredentialVerified = false;

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
  bool get hasRemoteCredential =>
      _nativeToken != null || (_firebaseAuth?.currentUser != null);
  int? get nativeUserId => _nativeUserId;
  int get localProfileUserId => _nativeUserId ?? 1;
  bool get isAnonymous =>
      _auditSession ||
      (!_localSessionEnrolled &&
          _nativeToken == null &&
          (_firebaseAuth?.currentUser?.isAnonymous ?? false));
  bool get isAuditSession => _auditSession;
  User? get firebaseUser => _firebaseAuth?.currentUser;

  Future<void> initialize() async {
    try {
      _localSessionEnrolled =
          await _storage.read(key: _localSessionKey) == _localSessionValue;
      final storedToken = await _storage.read(key: _tokenKey);
      final storedUserIdRaw = await _storage.read(key: _nativeUserIdKey);
      final storedUserId = int.tryParse(storedUserIdRaw ?? '');
      if (_isExpectedNativeBearerShape(storedToken)) {
        _nativeToken = storedToken;
        _nativeUserId = storedUserId;
        _remoteCredentialVerified = false;
        await _ensureLocalEnrollment();
      } else {
        if (storedToken != null) {
          await _storage.delete(key: _tokenKey);
        }
        if (storedUserIdRaw != null) {
          await _storage.delete(key: _nativeUserIdKey);
        }
        _nativeToken = null;
        _nativeUserId = null;
        _remoteCredentialVerified = false;
      }
    } catch (error, stackTrace) {
      _failureLogger(
        'initialize',
        error.runtimeType.toString(),
        stackTrace,
      );
      _nativeToken = null;
      _nativeUserId = null;
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
      _nativeUserId = null;
      _remoteCredentialVerified = false;
      await _storage.delete(key: _tokenKey);
      await _storage.delete(key: _nativeUserIdKey);
      _notifyAuthChanged();
      return null;
    }
    return _firebaseAuth?.currentUser?.getIdToken(true);
  }

  Future<void> signInWithEmail(String email, String password) async {
    final normalized = email.trim().toLowerCase();
    final nativeResponse = await _postJson(
      '/api/v1/auth/login',
      {'email': normalized, 'password': password},
    );
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
      if (firebaseToken == null || firebaseToken.isEmpty) {
        throw StateError('Firebase migration credential unavailable');
      }
      final exchange = await _postJson(
        '/api/v1/auth/firebase',
        {'id_token': firebaseToken},
      );
      if (exchange.statusCode >= 200 && exchange.statusCode < 300) {
        await _acceptAuthResponse(exchange);
        return;
      }
    }
    throw StateError('Authentication failed');
  }

  Future<void> registerWithEmail(String email, String password) async {
    if (!kRemoteAccountEnrollmentEnabled) {
      throw StateError('Remote account enrollment is disabled');
    }
    final response = await _postJson(
      '/api/v1/auth/register',
      {'email': email.trim().toLowerCase(), 'password': password},
    );
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw StateError('Registration failed');
    }
    await _acceptAuthResponse(response);
  }

  Future<void> signOut() async {
    _auditSession = false;
    final token = _nativeToken;

    // Local sign-out is authoritative. Never let optional remote revocation keep
    // an enrolled device authenticated while the network is slow or unavailable.
    _nativeToken = null;
    _nativeUserId = null;
    _localSessionEnrolled = false;
    _remoteCredentialVerified = false;
    try {
      await _storage.delete(key: _tokenKey);
      await _storage.delete(key: _nativeUserIdKey);
      await _storage.delete(key: _localSessionKey);
      await _storage.delete(key: _localDeviceIdKey);
      await _firebaseAuth?.signOut();
    } finally {
      _notifyAuthChanged();
    }

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
    if (kOfflineDemo) {
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
    final userId = user is Map ? user['id'] : null;
    if (token is! String || !_isExpectedNativeBearerShape(token)) {
      throw StateError('Missing IAMINA access token');
    }
    if (userId is! int || userId <= 0) {
      throw StateError('Missing IAMINA user id');
    }
    await _storage.write(key: _tokenKey, value: token);
    await _storage.write(key: _nativeUserIdKey, value: userId.toString());
    await _storage.write(key: _localSessionKey, value: _localSessionValue);
    _nativeToken = token;
    _nativeUserId = userId;
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
