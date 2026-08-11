import 'dart:convert';

import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;

const String kAuthBaseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'http://localhost:8000',
);

class AuthService extends ChangeNotifier {
  static const _tokenKey = 'iamina_native_access_token';

  final FirebaseAuth? _firebaseAuth;
  final FlutterSecureStorage _storage;
  final http.Client _httpClient;
  String? _nativeToken;
  bool _initialized = false;
  bool _auditSession = false;

  AuthService({
    FirebaseAuth? auth,
    FlutterSecureStorage? storage,
    http.Client? httpClient,
  })  : _firebaseAuth = _getAuthInstance(auth),
        _storage = storage ?? const FlutterSecureStorage(),
        _httpClient = httpClient ?? http.Client();

  static FirebaseAuth? _getAuthInstance(FirebaseAuth? provided) {
    try {
      return provided ?? FirebaseAuth.instance;
    } catch (_) {
      return null;
    }
  }

  bool get isInitialized => _initialized;
  bool get isAuthenticated =>
      _auditSession ||
      (_nativeToken?.isNotEmpty ?? false) ||
      _firebaseAuth?.currentUser != null;
  bool get isAnonymous =>
      _auditSession ||
      (_nativeToken == null && (_firebaseAuth?.currentUser?.isAnonymous ?? false));
  bool get isAuditSession => _auditSession;
  User? get firebaseUser => _firebaseAuth?.currentUser;

  Future<void> initialize() async {
    try {
      final stored = await _storage.read(key: _tokenKey);
      if (stored != null &&
          stored.isNotEmpty &&
          await _validateNativeToken(stored)) {
        _nativeToken = stored;
      } else if (stored != null) {
        await _storage.delete(key: _tokenKey);
      }
    } catch (_) {
      _nativeToken = null;
    } finally {
      _initialized = true;
      notifyListeners();
    }
  }

  void enterAuditSession() {
    if (!_initialized) {
      throw StateError('Audit session requires initialized authentication');
    }
    _auditSession = true;
    notifyListeners();
  }

  Future<String?> getIdToken() async {
    if (_auditSession) return null;
    final native = _nativeToken;
    if (native != null && native.isNotEmpty) return native;
    return _firebaseAuth?.currentUser?.getIdToken();
  }

  Future<String?> refreshToken() async {
    if (_auditSession) return null;
    final native = _nativeToken;
    if (native != null && native.isNotEmpty) return native;
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
    if (token != null) {
      try {
        await _httpClient.post(
          Uri.parse('$kAuthBaseUrl/api/v1/auth/logout'),
          headers: {'Authorization': 'Bearer $token'},
        );
      } catch (_) {}
    }
    _nativeToken = null;
    await _storage.delete(key: _tokenKey);
    await _firebaseAuth?.signOut();
    notifyListeners();
  }

  Future<void> signInAnonymously() async {
    if (_firebaseAuth == null) throw StateError('Firebase non initialisé');
    await _firebaseAuth.signInAnonymously();
    notifyListeners();
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
      {
        'uid': uid,
        'token': token,
        'new_password': newPassword,
      },
    );
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw StateError('Password recovery confirmation failed');
    }
  }

  Future<bool> _validateNativeToken(String token) async {
    try {
      final response = await _httpClient.get(
        Uri.parse('$kAuthBaseUrl/api/v1/auth/me'),
        headers: {'Authorization': 'Bearer $token'},
      );
      return response.statusCode >= 200 && response.statusCode < 300;
    } catch (_) {
      return false;
    }
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
    if (token is! String || !token.startsWith('iamina.')) {
      throw StateError('Missing IAMINA access token');
    }
    _nativeToken = token;
    await _storage.write(key: _tokenKey, value: token);
    notifyListeners();
  }

  @override
  void dispose() {
    _httpClient.close();
    super.dispose();
  }
}
