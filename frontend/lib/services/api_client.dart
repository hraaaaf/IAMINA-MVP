import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';
import 'package:chopper/chopper.dart';
import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';
import 'auth_epoch.dart';
import 'auth_service.dart';
import 'preview_api_origin.dart';
import 'document_ingest_minimizer.dart';
import 'sync_api_contract.dart';
import '../data/models/ai_models.dart';
import '../data/models/document_models.dart';
import '../data/models/personal_response_models.dart';

class ProviderApiException implements Exception {
  final String code;
  final String message;
  final bool retryable;
  final int statusCode;

  const ProviderApiException({
    required this.code,
    required this.message,
    required this.retryable,
    required this.statusCode,
  });

  factory ProviderApiException.fromJson(
    Map<String, dynamic> payload, {
    required int statusCode,
  }) {
    final error = payload['error'];
    if (error is! Map<String, dynamic>) {
      return ProviderApiException.unknown(statusCode: statusCode);
    }
    return ProviderApiException(
      code: error['code'] as String? ?? 'provider_unknown_failure',
      message:
          error['message'] as String? ??
          'The AI request could not be completed safely.',
      retryable: error['retryable'] as bool? ?? false,
      statusCode: statusCode,
    );
  }

  factory ProviderApiException.unknown({required int statusCode}) {
    return ProviderApiException(
      code: 'provider_unknown_failure',
      message: 'The AI request could not be completed safely.',
      retryable: false,
      statusCode: statusCode,
    );
  }

  String get userMessage {
    switch (code) {
      case 'provider_timeout':
      case 'provider_unavailable':
        return 'Le service IA est temporairement indisponible. Réessaie dans quelques instants.';
      case 'provider_quota_exceeded':
        return 'Le service IA est temporairement saturé. Réessaie plus tard.';
      case 'provider_malformed_response':
      case 'provider_internal_failure':
        return 'La réponse IA n’a pas pu être traitée en toute sécurité.';
      default:
        return retryable
            ? 'Le service IA est momentanément indisponible. Réessaie dans quelques instants.'
            : 'La demande IA n’a pas pu être traitée en toute sécurité.';
    }
  }

  @override
  String toString() =>
      'ProviderApiException(code: $code, retryable: $retryable)';
}

void requireCurrentAuthEpoch(int originEpoch) {
  if (AuthEpoch.value != originEpoch) {
    throw StateError('Authentication changed before patient request egress');
  }
}

/// Pin the identity while waiting for an asynchronous credential lookup.
/// Without this check, A's prepared clinical payload could get B's bearer.
Future<T> readForStableAuthEpoch<T>(Future<T> Function() read) async {
  final epoch = AuthEpoch.value;
  final value = await read();
  requireCurrentAuthEpoch(epoch);
  return value;
}

/// Public, read-only country estimate used only to prefill onboarding UI.
/// No clinical data is sent or received by this route.
bool isPublicCountrySuggestion(Uri url, String method) =>
    method.toUpperCase() == 'GET' &&
    url.path == '/api/v1/country/suggestion' &&
    !url.hasQuery && url.fragment.isEmpty;

/// Patient-owned sync must not leave the device after the app-lock closes,
/// including while a bearer or retry timer is resolving asynchronously.
/// Public login/enrollment endpoints are deliberately excluded.
void requireUnlockedPatientSyncTransport(
  Uri url,
  bool Function()? canUsePatientSyncTransport, {
  String method = '',
}) {
  // All API v1 routes other than public credential/recovery endpoints can
  // carry or mutate medical state (including AI, documents and consent).
  // The demo route is also protected outside explicit local audit sessions.
  final protected = url.path.startsWith('/api/v1/') &&
      !url.path.startsWith('/api/v1/auth/');
  if (protected && !isPublicCountrySuggestion(url, method) &&
      canUsePatientSyncTransport != null &&
      !canUsePatientSyncTransport()) {
    throw StateError('Patient sync blocked while device is locked');
  }
}

/// Pilot A: deny all clinical API routes except public authentication.
void requirePilotClinicalTransport(Uri url, bool Function()? allowed, {String method = ''}) {
  if (allowed != null && !allowed() &&
      !isPublicCountrySuggestion(url, method) &&
      url.path.startsWith('/api/v1/') &&
      !url.path.startsWith('/api/v1/auth/')) {
    throw StateError('Clinical transport disabled: local-only pilot');
  }
}

class AuthInterceptor implements Interceptor {
  final AuthService authService;
  final bool Function()? canUsePatientSyncTransport;
  final bool Function()? canUseClinicalTransport;
  AuthInterceptor(this.authService, {
    this.canUsePatientSyncTransport,
    this.canUseClinicalTransport,
  });

  @override
  FutureOr<Response<BodyType>> intercept<BodyType>(
    Chain<BodyType> chain,
  ) async {
    requirePilotClinicalTransport(chain.request.url, canUseClinicalTransport, method: chain.request.method);
    // Public, read-only Web geolocation has no patient identity. Do not let
    // a slow or failing browser credential lookup stall its 4-second UI
    // deadline. All other clinical requests still resolve and guard bearer.
    if (isPublicCountrySuggestion(chain.request.url, chain.request.method)) {
      return chain.proceed(chain.request);
    }
    final token = await readForStableAuthEpoch(authService.getIdToken);
    requirePilotClinicalTransport(chain.request.url, canUseClinicalTransport, method: chain.request.method);
    // This executes AFTER any async credential lookup and immediately before
    // the Chopper chain is allowed to dispatch the medical request.
    requireUnlockedPatientSyncTransport(
      chain.request.url, canUsePatientSyncTransport, method: chain.request.method,
    );
    Request request = chain.request;
    if (token != null && token.isNotEmpty) {
      request = applyHeader(
        request,
        'Authorization',
        'Bearer $token',
        override: true,
      );
    }
    return chain.proceed(request);
  }
}

/// Applies a hard 30-second timeout to every Chopper request.
/// Each ApiClient method decides whether a timeout should degrade safely or
/// surface as a typed failure to its caller.
class TimeoutInterceptor implements Interceptor {
  static const _kTimeout = Duration(seconds: 30);

  @override
  Future<Response<BodyType>> intercept<BodyType>(Chain<BodyType> chain) {
    // Future.value() promotes FutureOr → Future so .timeout() is available.
    return Future.value(chain.proceed(chain.request)).timeout(_kTimeout);
  }
}

/// A server 5xx may mean a medical mutation was committed but its response
/// was lost. Only safe reads can be resent without a per-operation receipt.
bool mayRetryAfterServerError(String method) =>
    method.toUpperCase() == 'GET' || method.toUpperCase() == 'HEAD';

class RetryInterceptor implements Interceptor {
  final AuthService authService;
  final bool Function()? canUsePatientSyncTransport;
  static const int _maxRetries = 3;

  final bool Function()? canUseClinicalTransport;
  RetryInterceptor(this.authService, {
    this.canUsePatientSyncTransport,
    this.canUseClinicalTransport,
  });

  @override
  FutureOr<Response<BodyType>> intercept<BodyType>(
    Chain<BodyType> chain,
  ) async {
    final epoch = AuthEpoch.value;
    requirePilotClinicalTransport(chain.request.url, canUseClinicalTransport, method: chain.request.method);
    requireUnlockedPatientSyncTransport(
      chain.request.url, canUsePatientSyncTransport, method: chain.request.method,
    );
    Response<BodyType> response = await chain.proceed(chain.request);
    requireCurrentAuthEpoch(epoch);

    // 401 — refresh token and retry once
    if (response.statusCode == 401) {
      final newToken = await readForStableAuthEpoch(authService.refreshToken);
      requireCurrentAuthEpoch(epoch);
      if (newToken != null && newToken.isNotEmpty) {
        final retryRequest = applyHeader(
          chain.request,
          'Authorization',
          'Bearer $newToken',
          override: true,
        );
        requirePilotClinicalTransport(retryRequest.url, canUseClinicalTransport, method: retryRequest.method);
        requireUnlockedPatientSyncTransport(
          retryRequest.url, canUsePatientSyncTransport, method: retryRequest.method,
        );
        response = await chain.proceed(retryRequest);
        requireCurrentAuthEpoch(epoch);
      }
      return response;
    }

    // 5xx: retry safe reads only. POST/PATCH/PUT/DELETE may have committed
    // before the upstream 502/503, so the caller must reconcile their status.
    if (!mayRetryAfterServerError(chain.request.method)) return response;
    int attempt = 0;
    while (_isServerError(response.statusCode) && attempt < _maxRetries) {
      await Future.delayed(Duration(seconds: 1 << attempt));
      requireCurrentAuthEpoch(epoch);
      requirePilotClinicalTransport(chain.request.url, canUseClinicalTransport, method: chain.request.method);
      requireUnlockedPatientSyncTransport(
        chain.request.url, canUsePatientSyncTransport, method: chain.request.method,
      );
      response = await chain.proceed(chain.request);
      requireCurrentAuthEpoch(epoch);
      attempt++;
    }

    return response;
  }

  bool _isServerError(int statusCode) => statusCode >= 500 && statusCode < 600;
}

const String kBaseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'http://localhost:8000',
);

const int kMaxDocumentUploadBytes = 15 * 1024 * 1024;

bool isDocumentUploadSizeAllowed(int byteLength) =>
    byteLength > 0 && byteLength <= kMaxDocumentUploadBytes;

enum TreatmentMirrorStatus { confirmed, conflict, unavailable }

final class TreatmentMirrorResult {
  final TreatmentMirrorStatus status;
  final DateTime? serverUpdatedAtUtc;
  const TreatmentMirrorResult(this.status, {this.serverUpdatedAtUtc});
}

/// The backend must acknowledge exactly the declared state and codes.
bool treatmentMirrorMatches(
  Map<String, dynamic> profile,
  String state,
  List<String> codes,
) {
  final remoteCodes = profile['treatment_declarations'];
  if (profile['treatment_declaration_source'] != 'patient_declared' ||
      profile['treatment_declaration_version'] != 1 ||
      profile['treatment_declaration_state'] != state ||
      remoteCodes is! List ||
      remoteCodes.length != codes.length) return false;
  for (var i = 0; i < codes.length; i++) {
    if (remoteCodes[i] != codes[i]) return false;
  }
  return true;
}

DateTime? verifiedServerTreatmentRevision(Map<String, dynamic> profile) {
  final raw = profile['treatment_declaration_updated_at'];
  if (raw is! String ||
      !RegExp(r'(Z|[+-][0-9]{2}:[0-9]{2})$').hasMatch(raw)) return null;
  return DateTime.tryParse(raw)?.toUtc();
}

class ApiClient {
  final String baseUrl;
  final AuthService _authService;
  final bool Function()? _canUsePatientSyncTransport;
  final bool Function()? _allowClinicalTransportForSyntheticTests;
  /// Local-only by default, including when a native bearer exists.
  bool get canSyncClinicalData =>
      _allowClinicalTransportForSyntheticTests?.call() ?? false;
  final PendingDocumentDeduplicator<PulperPreview> _documentDeduplicator =
      PendingDocumentDeduplicator<PulperPreview>();

  ApiClient({
    String? baseUrl,
    AuthService? authService,
    bool Function()? canUsePatientSyncTransport,
    bool Function()? allowClinicalTransportForSyntheticTests,
  }) : baseUrl = baseUrl ?? resolveIaminaApiOrigin(kBaseUrl),
       _authService = authService ?? AuthService(),
       _canUsePatientSyncTransport = canUsePatientSyncTransport,
       _allowClinicalTransportForSyntheticTests =
           allowClinicalTransportForSyntheticTests;

  late final ChopperClient _client = ChopperClient(
    baseUrl: Uri.parse(baseUrl),
    interceptors: [
      TimeoutInterceptor(), // 30 s hard cap — before auth so it covers all latency
      AuthInterceptor(
        _authService,
        canUsePatientSyncTransport: _canUsePatientSyncTransport,
        canUseClinicalTransport: () => canSyncClinicalData,
      ),
      RetryInterceptor(
        _authService,
        canUsePatientSyncTransport: _canUsePatientSyncTransport,
        canUseClinicalTransport: () => canSyncClinicalData,
      ),
    ],
    converter: const JsonConverter(),
  );

  ChopperClient get client => _client;

  /// A response from the previous auth epoch is never exposed to its caller.
  Future<Map<String, dynamic>?> getProfile() async {
    if (!canSyncClinicalData) return null;
    final epoch = AuthEpoch.value;
    try {
      final response = await _client.get(Uri.parse('/api/v1/profile'));
      requireCurrentAuthEpoch(epoch);
      final body = response.body;
      return response.isSuccessful && body is Map<String, dynamic>
          ? body
          : null;
    } on StateError {
      rethrow;
    } catch (_) {
      return null;
    }
  }

  /// Strict opt-in CAS mirror. An HTTP 200 without matching server evidence
  /// is NOT acknowledgement. 409 never overwrites a competing declaration.
  Future<TreatmentMirrorResult> mirrorTreatmentDeclaration({
    required String state,
    required List<String> codes,
    required DateTime? expectedUpdatedAtUtc,
  }) async {
    final epoch = AuthEpoch.value;
    if (!canSyncClinicalData) {
      return const TreatmentMirrorResult(TreatmentMirrorStatus.unavailable);
    }
    final payload = <String, dynamic>{
      'treatment_declaration': {
        'version': 1,
        'state': state,
        'codes': codes,
      },
    };
    try {
      final response = await _client.patch(
        Uri.parse('/api/v1/profile'),
        body: payload,
        headers: {
          'X-Iamina-Treatment-Expected-Updated-At':
              expectedUpdatedAtUtc?.toUtc().toIso8601String() ?? 'none',
        },
      );
      requireCurrentAuthEpoch(epoch);
      Map<String, dynamic>? confirmed;
      if (response.statusCode == 409) {
        // A lost 200 followed by a retry can legitimately hit 409.
        // Read back owner-scoped server state before calling it a conflict.
        confirmed = await getProfile();
        requireCurrentAuthEpoch(epoch);
        if (confirmed == null ||
            !treatmentMirrorMatches(confirmed, state, codes)) {
          return const TreatmentMirrorResult(TreatmentMirrorStatus.conflict);
        }
      } else if (response.isSuccessful && response.body is Map) {
        confirmed = Map<String, dynamic>.from(response.body as Map);
      } else {
        return const TreatmentMirrorResult(TreatmentMirrorStatus.unavailable);
      }
      // Both accepted branches guarantee a non-null server snapshot.
      if (!treatmentMirrorMatches(confirmed, state, codes)) {
        return const TreatmentMirrorResult(TreatmentMirrorStatus.unavailable);
      }
      final serverAt = verifiedServerTreatmentRevision(confirmed);
      if (serverAt == null) {
        return const TreatmentMirrorResult(TreatmentMirrorStatus.unavailable);
      }
      return TreatmentMirrorResult(
        TreatmentMirrorStatus.confirmed,
        serverUpdatedAtUtc: serverAt,
      );
    } on StateError {
      rethrow;
    } catch (_) {
      return const TreatmentMirrorResult(TreatmentMirrorStatus.unavailable);
    }
  }

  Future<bool> patchProfile(Map<String, dynamic> patch) async {
    if (!canSyncClinicalData) return false;
    try {
      final response = await _client.patch(
        Uri.parse('/api/v1/profile'),
        body: patch,
      );
      return response.isSuccessful;
    } catch (_) {
      return false;
    }
  }

  Future<PersonalResponseResult?> getPersonalResponse({int days = 90}) async {
    try {
      final response = await _client.get(
        Uri.parse('/api/v1/personal-response/?days=$days'),
      );
      final body = response.body;
      if (response.isSuccessful && body is Map) {
        return PersonalResponseResult.fromJson(Map<String, dynamic>.from(body));
      }
      return null;
    } catch (_) {
      return null;
    }
  }

  /// Envoie un log unique au backend.
  Future<bool> syncLogEntry(Map<String, dynamic> log) {
    if (!canSyncClinicalData) return Future.value(false);
    return guardSyncApiCall<bool>('sync_log_entry', () async {
      final response = await _client.post(Uri.parse('/api/v1/logs'), body: log);
      return response.isSuccessful;
    });
  }

  /// Envoie une liste de logs en une seule requête (Batch).
  Future<List<String>> batchSyncLogs(List<Map<String, dynamic>> logs) {
    if (!canSyncClinicalData) return Future.value(const <String>[]);
    return guardSyncApiCall<List<String>>('batch_sync_logs', () async {
      final response = await _client.post(
        Uri.parse('/api/v1/logs/batch'),
        body: logs,
      );

      if (!response.isSuccessful) return const <String>[];
      return parseBatchSyncIds(response.body);
    });
  }

  /// Récupère le résumé analytique IAmina.
  Future<SummaryResponse?> getAiSummary({int days = 21}) async {
    try {
      final response = await _client.post(
        Uri.parse('/api/v1/ai/summary'),
        body: {'days': days},
      );

      if (response.isSuccessful && response.body != null) {
        return SummaryResponse.fromJson(response.body as Map<String, dynamic>);
      }
      return null;
    } catch (_) {
      return null;
    }
  }

  /// Récupère les KPIs canoniques depuis l'endpoint SQL-first.
  Future<KpisResponse?> getKpis({
    int days = 21,
    double targetLow = 70.0,
    double targetHigh = 180.0,
  }) async {
    try {
      final response = await _client.get(
        Uri.parse(
          '/api/v1/kpis/?days=$days&target_low=$targetLow&target_high=$targetHigh',
        ),
      );

      if (response.isSuccessful && response.body != null) {
        return KpisResponse.fromJson(response.body as Map<String, dynamic>);
      }
      return null;
    } catch (_) {
      return null;
    }
  }

  /// Streaming SSE chat — yields token strings as they arrive.
  Stream<String> chatStream(String message) async* {
    if (!canSyncClinicalData) return;
    final epoch = AuthEpoch.value;
    final token = await readForStableAuthEpoch(_authService.getIdToken);
    final uri = Uri.parse(
      '$baseUrl/api/v1/ai/chat/stream',
    ).replace(queryParameters: {'message': message});

    final request = http.Request('GET', uri);
    if (token != null && token.isNotEmpty) {
      request.headers['Authorization'] = 'Bearer $token';
    }

    final client = http.Client();
    try {
      requireUnlockedPatientSyncTransport(uri, _canUsePatientSyncTransport);
      final streamed = await client
          .send(request)
          .timeout(TimeoutInterceptor._kTimeout);
      requireCurrentAuthEpoch(epoch);
      requireUnlockedPatientSyncTransport(uri, _canUsePatientSyncTransport);

      if (streamed.statusCode < 200 || streamed.statusCode >= 300) {
        final body = await streamed.stream.bytesToString();
      requireCurrentAuthEpoch(epoch);
      requireUnlockedPatientSyncTransport(uri, _canUsePatientSyncTransport);
        try {
          final payload = jsonDecode(body) as Map<String, dynamic>;
          throw ProviderApiException.fromJson(
            payload,
            statusCode: streamed.statusCode,
          );
        } on ProviderApiException {
          rethrow;
        } catch (_) {
          throw ProviderApiException.unknown(statusCode: streamed.statusCode);
        }
      }

      String buffer = '';
      await for (final chunk in streamed.stream.transform(utf8.decoder)) {
        requireCurrentAuthEpoch(epoch);
        requireUnlockedPatientSyncTransport(uri, _canUsePatientSyncTransport);
        buffer += chunk;
        final lines = buffer.split('\n');
        buffer = lines.removeLast(); // last may be incomplete
        for (final line in lines) {
          if (line.startsWith('data: ')) {
            final payload = line.substring(6).trim();
            if (payload == '[DONE]') return;
            try {
              final json = jsonDecode(payload) as Map<String, dynamic>;
              final tok = json['token'] as String?;
              if (tok != null) {
                requireCurrentAuthEpoch(epoch);
                requireUnlockedPatientSyncTransport(
                  uri, _canUsePatientSyncTransport,
                );
                yield tok;
              }
            } catch (_) {}
          }
        }
      }
    } on TimeoutException {
      throw const ProviderApiException(
        code: 'provider_timeout',
        message: 'The AI service did not respond in time.',
        retryable: true,
        statusCode: 503,
      );
    } on ProviderApiException {
      rethrow;
    } catch (_) {
      throw const ProviderApiException(
        code: 'provider_unavailable',
        message: 'The AI service is temporarily unavailable.',
        retryable: true,
        statusCode: 503,
      );
    } finally {
      client.close();
    }
  }

  /// Seed demo data on the backend for the current user (creates PatientProfile + 30 days of logs).
  Future<bool> seedDemoData() async {
    try {
      final response = await _client.post(
        Uri.parse('/api/v1/demo/seed'),
        body: <String, dynamic>{},
      );
      return response.isSuccessful;
    } catch (_) {
      return false;
    }
  }

  /// Discute avec l'assistant IAmina.
  Future<ChatResponse?> chatWithAmina(
    String message, {
    String contextType = 'general',
  }) async {
    try {
      final response = await _client.post(
        Uri.parse('/api/v1/ai/chat'),
        body: {'message': message, 'context_type': contextType},
      );

      if (response.isSuccessful && response.body != null) {
        return ChatResponse.fromJson(response.body as Map<String, dynamic>);
      }
      return null;
    } catch (_) {
      return null;
    }
  }

  /// Envoie un message vocal à IAmina.
  ///
  /// [audioBytes]  : raw audio content (WebM on web, m4a on mobile).
  /// [mimeType]    : e.g. "audio/webm" or "audio/mp4".
  /// [contextDays] : look-back window for clinical context.
  ///
  /// Returns [VoiceResponse] with transcript + IAmina reply.
  /// TTS is handled by the caller (flutter_tts) — no server-side audio.
  Future<VoiceResponse?> sendVoiceMessage(
    Uint8List audioBytes,
    String mimeType, {
    int contextDays = 14,
  }) async {
    if (!canSyncClinicalData) return null;
    try {
      final epoch = AuthEpoch.value;
      final token = await readForStableAuthEpoch(_authService.getIdToken);
      final uri = Uri.parse(
        '$baseUrl/api/v1/ai/voice?context_days=$contextDays',
      );

      final request = http.MultipartRequest('POST', uri);
      if (token != null && token.isNotEmpty) {
        request.headers['Authorization'] = 'Bearer $token';
      }

      // Attach audio as multipart field "audio"
      request.files.add(
        http.MultipartFile.fromBytes(
          'audio',
          audioBytes,
          filename: 'voice.${_extFromMime(mimeType)}',
          contentType: MediaType.parse(mimeType),
        ),
      );

      requireUnlockedPatientSyncTransport(uri, _canUsePatientSyncTransport);
      final streamed = await request.send();
      final body = await streamed.stream.bytesToString();
      requireCurrentAuthEpoch(epoch);
      requireUnlockedPatientSyncTransport(uri, _canUsePatientSyncTransport);

      if (streamed.statusCode >= 200 && streamed.statusCode < 300) {
        final json = jsonDecode(body) as Map<String, dynamic>;
        return VoiceResponse.fromJson(json);
      }
      return null;
    } catch (_) {
      return null;
    }
  }

  /// Web OCR: extract glucose value from a glucometer photo via Gemini Vision.
  /// Mobile uses ML Kit (offline); web uses this endpoint as fallback.
  Future<GlucometerOcrResponse?> analyzeGlucometerImage(
    String base64Image,
    String mimeType,
  ) async {
    if (!canSyncClinicalData) return null;
    try {
      final epoch = AuthEpoch.value;
      final token = await readForStableAuthEpoch(_authService.getIdToken);
      final uri = Uri.parse('$baseUrl/api/v1/ai/analyze-glucometer-image');
      final req = http.Request('POST', uri)
        ..headers['Content-Type'] = 'application/json'
        ..body = jsonEncode({
          'image_base64': base64Image,
          'mime_type': mimeType,
        });
      if (token != null && token.isNotEmpty) {
        req.headers['Authorization'] = 'Bearer $token';
      }
      requireUnlockedPatientSyncTransport(uri, _canUsePatientSyncTransport);
      final streamed = await req.send();
      final body = await streamed.stream.bytesToString();
      requireCurrentAuthEpoch(epoch);
      requireUnlockedPatientSyncTransport(uri, _canUsePatientSyncTransport);
      if (streamed.statusCode >= 200 && streamed.statusCode < 300) {
        return GlucometerOcrResponse.fromJson(
          jsonDecode(body) as Map<String, dynamic>,
        );
      }
      return null;
    } catch (_) {
      return null;
    }
  }

  /// Transcribe audio to text (STT only — no IAmina pipeline).
  /// Used for vocal input in the add-log page meal note field.
  Future<String?> transcribeAudio(Uint8List audioBytes, String mimeType) async {
    if (!canSyncClinicalData) return null;
    try {
      final epoch = AuthEpoch.value;
      final token = await readForStableAuthEpoch(_authService.getIdToken);
      final uri = Uri.parse('$baseUrl/api/v1/ai/transcribe');
      final request = http.MultipartRequest('POST', uri);
      if (token != null && token.isNotEmpty) {
        request.headers['Authorization'] = 'Bearer $token';
      }
      request.files.add(
        http.MultipartFile.fromBytes(
          'audio',
          audioBytes,
          filename: 'note.${_extFromMime(mimeType)}',
          contentType: MediaType.parse(mimeType),
        ),
      );
      requireUnlockedPatientSyncTransport(uri, _canUsePatientSyncTransport);
      final streamed = await request.send();
      final body = await streamed.stream.bytesToString();
      requireCurrentAuthEpoch(epoch);
      requireUnlockedPatientSyncTransport(uri, _canUsePatientSyncTransport);
      if (streamed.statusCode >= 200 && streamed.statusCode < 300) {
        final json = jsonDecode(body) as Map<String, dynamic>;
        return json['transcript'] as String?;
      }
      return null;
    } catch (_) {
      return null;
    }
  }

  // ── RGPD Consent (Art. 7) ────────────────────────────────────────────────

  /// Returns {ai_consent_given: bool, ai_consent_given_at: String|null}.
  Future<Map<String, dynamic>?> getConsentStatus() async {
    try {
      final response = await _client.get(Uri.parse('/api/v1/account/consent'));
      if (response.isSuccessful && response.body != null) {
        return response.body as Map<String, dynamic>;
      }
      return null;
    } catch (_) {
      return null;
    }
  }

  /// Record explicit AI consent (RGPD Art. 7).
  Future<bool> giveConsent() async {
    try {
      final response = await _client.post(
        Uri.parse('/api/v1/account/consent'),
        body: <String, dynamic>{},
      );
      return response.isSuccessful;
    } catch (_) {
      return false;
    }
  }

  /// Withdraw AI consent — AI features disabled until re-consent.
  Future<bool> withdrawConsent() async {
    try {
      final response = await _client.delete(
        Uri.parse('/api/v1/account/consent'),
      );
      return response.isSuccessful;
    } catch (_) {
      return false;
    }
  }

  // ── Modules (chassis) ──────────────────────────────────────────────────────

  /// Returns the patient's active module names, or null on failure/offline.
  Future<List<String>?> getActiveModules() async {
    try {
      final response = await _client.get(Uri.parse('/api/v1/account/modules'));
      if (response.isSuccessful && response.body != null) {
        final body = response.body as Map<String, dynamic>;
        final mods = (body['modules'] as List?) ?? const [];
        return mods.map((m) => (m as Map)['name'] as String).toList();
      }
      return null;
    } catch (_) {
      return null;
    }
  }

  /// Enrol the patient into [moduleName].
  Future<bool> activateModule(String moduleName) async {
    try {
      final response = await _client.post(
        Uri.parse('/api/v1/account/modules/$moduleName/activate'),
        body: <String, dynamic>{},
      );
      return response.isSuccessful;
    } catch (_) {
      return false;
    }
  }

  // ── Phase 11-C: Meal photo recognition ──────────────────────────────────────

  /// POST /api/v1/ai/analyze-meal-image
  ///
  /// [imageBytes] — raw bytes of the picked image (JPEG / PNG / WebP).
  /// [mimeType]   — MIME type of the image (default "image/jpeg").
  ///
  /// Returns [MealAnalysisResult] with identified food names (French).
  /// Returns null on network error; check [MealAnalysisResult.fallback] for
  /// LLM-side failures (server is reachable but couldn't identify the food).
  Future<MealAnalysisResult?> analyzeMealImage(
    Uint8List imageBytes, {
    String mimeType = 'image/jpeg',
  }) async {
    try {
      final b64 = base64Encode(imageBytes);
      final response = await _client.post(
        Uri.parse('/api/v1/ai/analyze-meal-image'),
        body: {'image_base64': b64, 'mime_type': mimeType},
      );
      if (response.isSuccessful && response.body != null) {
        return MealAnalysisResult.fromJson(
          response.body as Map<String, dynamic>,
        );
      }
      return null;
    } catch (_) {
      return null;
    }
  }

  // ── Phase 12: Document Pulper ─────────────────────────────────────────────

  /// Stage 1 compatibility wrapper for callers that already own bytes.
  Future<PulperPreview?> ingestDocument(
    Uint8List fileBytes,
    String filename,
    String mimeType,
  ) => ingestDocumentStream(
    Stream<List<int>>.value(fileBytes),
    fileBytes.lengthInBytes,
    filename,
    mimeType,
  );

  /// Stage 1: stream file bytes into multipart without materializing the full
  /// selected document in Flutter memory. [byteLength] comes from the picker and
  /// is validated before opening the HTTP request.
  Future<PulperPreview?> ingestDocumentStream(
    Stream<List<int>> fileStream,
    int byteLength,
    String filename,
    String mimeType,
  ) async {
    if (!canSyncClinicalData) return null;
    if (!isDocumentUploadSizeAllowed(byteLength)) return null;
    if (!isMinimizableDocumentImage(filename: filename, mimeType: mimeType)) {
      return _ingestDocumentStreamRaw(
        fileStream,
        byteLength,
        filename,
        mimeType,
      );
    }

    try {
      final source = await readDocumentStreamBounded(
        fileStream,
        maxBytes: kMaxDocumentUploadBytes,
      );
      final minimized = minimizeDocumentImage(
        source,
        filename: filename,
        mimeType: mimeType,
      );
      final cached = _documentDeduplicator.lookup(minimized.sha256Digest);
      if (cached != null) return cached;

      final preview = await _ingestDocumentStreamRaw(
        Stream<List<int>>.value(minimized.bytes),
        minimized.bytes.length,
        minimized.filename,
        minimized.mimeType,
      );
      if (preview != null) {
        _documentDeduplicator.remember(
          digest: minimized.sha256Digest,
          batchId: preview.batchId,
          value: preview,
        );
      }
      return preview;
    } on DocumentStreamLimitExceeded {
      return null;
    }
  }

  Future<PulperPreview?> _ingestDocumentStreamRaw(
    Stream<List<int>> fileStream,
    int byteLength,
    String filename,
    String mimeType,
  ) async {
    if (!canSyncClinicalData) return null;
    if (!isDocumentUploadSizeAllowed(byteLength)) {
      return null;
    }

    try {
      final epoch = AuthEpoch.value;
      final token = await readForStableAuthEpoch(_authService.getIdToken);
      final uri = Uri.parse('$baseUrl/api/v1/documents/ingest?confirm=false');

      final request = http.MultipartRequest('POST', uri);
      if (token != null && token.isNotEmpty) {
        request.headers['Authorization'] = 'Bearer $token';
      }
      request.files.add(
        http.MultipartFile(
          'file',
          fileStream,
          byteLength,
          filename: filename,
          contentType: MediaType.parse(mimeType),
        ),
      );

      requireUnlockedPatientSyncTransport(uri, _canUsePatientSyncTransport);
      final streamed = await request.send().timeout(
        const Duration(seconds: 60),
      ); // extraction can take time
      final body = await streamed.stream.bytesToString();
      requireCurrentAuthEpoch(epoch);
      requireUnlockedPatientSyncTransport(uri, _canUsePatientSyncTransport);

      if (streamed.statusCode >= 200 && streamed.statusCode < 300) {
        final json = jsonDecode(body) as Map<String, dynamic>;
        return PulperPreview.fromJson(json);
      }
      return null;
    } catch (_) {
      return null;
    }
  }

  /// Stage 2: confirm extraction → persists to DB.
  Future<PulperConfirmResult?> confirmDocumentImport(String batchId) async {
    try {
      final response = await _client.post(
        Uri.parse('/api/v1/documents/confirm/$batchId'),
        body: <String, dynamic>{},
      );
      if (response.isSuccessful && response.body != null) {
        final result = PulperConfirmResult.fromJson(
          response.body as Map<String, dynamic>,
        );
        _documentDeduplicator.clearBatch(batchId);
        return result;
      }
      return null;
    } catch (_) {
      return null;
    }
  }

  /// List previously imported lab reports.
  Future<List<LabReportSummary>> listLabReports({int limit = 20}) async {
    try {
      final response = await _client.get(
        Uri.parse('/api/v1/documents/?limit=$limit'),
      );
      if (response.isSuccessful && response.body != null) {
        return (response.body as List)
            .map((e) => LabReportSummary.fromJson(e as Map<String, dynamic>))
            .toList();
      }
      return [];
    } catch (_) {
      return [];
    }
  }

  /// Map MIME type to file extension for the multipart filename.
  String _extFromMime(String mime) {
    const map = {
      'audio/webm': 'webm',
      'audio/mp4': 'm4a',
      'audio/mpeg': 'mp3',
      'audio/wav': 'wav',
      'audio/ogg': 'ogg',
    };
    return map[mime] ?? 'bin';
  }
}
