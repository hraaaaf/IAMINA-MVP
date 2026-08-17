import 'dart:convert';

import 'package:http/http.dart' as http;

import 'auth_service.dart';

const String cgmApiBaseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'http://localhost:8000',
);

class CgmConnectionState {
  final bool connected;
  final String? source;
  final String? baseUrl;
  final String? authType;
  final bool credentialSet;
  final bool enabled;
  final DateTime? lastSyncAt;
  final DateTime? lastSuccessAt;
  final String lastErrorCode;

  const CgmConnectionState({
    required this.connected,
    this.source,
    this.baseUrl,
    this.authType,
    this.credentialSet = false,
    this.enabled = false,
    this.lastSyncAt,
    this.lastSuccessAt,
    this.lastErrorCode = '',
  });

  factory CgmConnectionState.fromJson(Map<String, dynamic> json) {
    DateTime? parseDate(Object? value) {
      if (value is! String || value.isEmpty) return null;
      return DateTime.tryParse(value)?.toLocal();
    }

    return CgmConnectionState(
      connected: json['connected'] == true,
      source: json['source'] as String?,
      baseUrl: json['base_url'] as String?,
      authType: json['auth_type'] as String?,
      credentialSet: json['credential_set'] == true,
      enabled: json['enabled'] == true,
      lastSyncAt: parseDate(json['last_sync_at']),
      lastSuccessAt: parseDate(json['last_success_at']),
      lastErrorCode: json['last_error_code'] as String? ?? '',
    );
  }
}

class CgmReadingView {
  final DateTime recordedAt;
  final int glucoseMgDl;
  final String trend;
  final String device;
  final String source;

  const CgmReadingView({
    required this.recordedAt,
    required this.glucoseMgDl,
    required this.trend,
    required this.device,
    required this.source,
  });

  factory CgmReadingView.fromJson(Map<String, dynamic> json) {
    final recordedAt = DateTime.tryParse(json['recorded_at'] as String? ?? '');
    final glucose = json['glucose_mg_dl'];
    if (recordedAt == null || glucose is! int || glucose <= 0) {
      throw const FormatException('Invalid CGM reading payload');
    }
    return CgmReadingView(
      recordedAt: recordedAt.toLocal(),
      glucoseMgDl: glucose,
      trend: json['trend'] as String? ?? '',
      device: json['device'] as String? ?? '',
      source: json['source'] as String? ?? '',
    );
  }
}

class CgmSyncResult {
  final int received;
  final int inserted;
  final DateTime? lastRecordedAt;

  const CgmSyncResult({
    required this.received,
    required this.inserted,
    this.lastRecordedAt,
  });

  factory CgmSyncResult.fromJson(Map<String, dynamic> json) {
    return CgmSyncResult(
      received: json['received'] as int? ?? 0,
      inserted: json['inserted'] as int? ?? 0,
      lastRecordedAt: DateTime.tryParse(json['last_recorded_at'] as String? ?? '')?.toLocal(),
    );
  }
}

class CgmServiceException implements Exception {
  final String code;
  final int statusCode;
  const CgmServiceException(this.code, this.statusCode);

  @override
  String toString() => 'CgmServiceException($code, $statusCode)';
}

class CgmService {
  final AuthService _authService;
  final http.Client _http;
  final String baseUrl;

  CgmService({
    AuthService? authService,
    http.Client? httpClient,
    this.baseUrl = cgmApiBaseUrl,
  }) : _authService = authService ?? AuthService(),
       _http = httpClient ?? http.Client();

  Future<Map<String, String>> _headers({bool json = false}) async {
    final token = await _authService.getIdToken();
    if (token == null || token.isEmpty) {
      throw const CgmServiceException('authentication_required', 401);
    }
    return {
      'Authorization': 'Bearer $token',
      if (json) 'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
  }

  Never _throwResponse(http.Response response) {
    var code = 'cgm_request_failed';
    try {
      final decoded = jsonDecode(response.body);
      if (decoded is Map<String, dynamic>) {
        final detail = decoded['detail'];
        if (detail is String && detail.isNotEmpty) code = detail;
      }
    } catch (_) {
      // Preserve one stable non-sensitive client failure code.
    }
    throw CgmServiceException(code, response.statusCode);
  }

  Future<CgmConnectionState> getConnection() async {
    final response = await _http
        .get(
          Uri.parse('$baseUrl/api/v1/cgm/connection'),
          headers: await _headers(),
        )
        .timeout(const Duration(seconds: 30));
    if (response.statusCode != 200) _throwResponse(response);
    final decoded = jsonDecode(response.body);
    if (decoded is! Map) throw const FormatException('Invalid CGM connection payload');
    return CgmConnectionState.fromJson(Map<String, dynamic>.from(decoded));
  }

  Future<CgmConnectionState> configure({
    required String source,
    required String nightscoutUrl,
    required String authType,
    required String credential,
  }) async {
    final response = await _http
        .put(
          Uri.parse('$baseUrl/api/v1/cgm/connection'),
          headers: await _headers(json: true),
          body: jsonEncode({
            'source': source,
            'base_url': nightscoutUrl,
            'auth_type': authType,
            'credential': credential,
          }),
        )
        .timeout(const Duration(seconds: 30));
    if (response.statusCode != 200) _throwResponse(response);
    final decoded = jsonDecode(response.body);
    if (decoded is! Map) throw const FormatException('Invalid CGM connection payload');
    return CgmConnectionState.fromJson(Map<String, dynamic>.from(decoded));
  }

  Future<CgmSyncResult> sync() async {
    final response = await _http
        .post(
          Uri.parse('$baseUrl/api/v1/cgm/sync'),
          headers: await _headers(),
        )
        .timeout(const Duration(seconds: 30));
    if (response.statusCode != 200) _throwResponse(response);
    final decoded = jsonDecode(response.body);
    if (decoded is! Map) throw const FormatException('Invalid CGM sync payload');
    return CgmSyncResult.fromJson(Map<String, dynamic>.from(decoded));
  }

  Future<List<CgmReadingView>> getReadings({int hours = 24}) async {
    final response = await _http
        .get(
          Uri.parse('$baseUrl/api/v1/cgm/readings?hours=$hours'),
          headers: await _headers(),
        )
        .timeout(const Duration(seconds: 30));
    if (response.statusCode != 200) _throwResponse(response);
    final decoded = jsonDecode(response.body);
    if (decoded is! List) throw const FormatException('Invalid CGM readings payload');
    return decoded
        .whereType<Map>()
        .map((item) => CgmReadingView.fromJson(Map<String, dynamic>.from(item)))
        .toList(growable: false);
  }

  Future<void> disconnect() async {
    final response = await _http
        .delete(
          Uri.parse('$baseUrl/api/v1/cgm/connection'),
          headers: await _headers(),
        )
        .timeout(const Duration(seconds: 30));
    if (response.statusCode != 204) _throwResponse(response);
  }

  void dispose() => _http.close();
}
