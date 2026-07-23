import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';
import 'package:chopper/chopper.dart';
import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';
import 'auth_service.dart';
import '../data/models/ai_models.dart';
import '../data/models/document_models.dart';

class AuthInterceptor implements Interceptor {
  final AuthService authService;
  AuthInterceptor(this.authService);

  @override
  FutureOr<Response<BodyType>> intercept<BodyType>(Chain<BodyType> chain) async {
    final token = await authService.getIdToken();
    Request request = chain.request;
    if (token != null && token.isNotEmpty) {
      request = applyHeader(request, 'Authorization', 'Bearer $token', override: true);
    }
    return chain.proceed(request);
  }
}

/// Applies a hard 30-second timeout to every Chopper request.
/// TimeoutException is silently caught by each ApiClient method's catch(_) block,
/// which returns null / false to the caller — safe degraded behaviour.
class TimeoutInterceptor implements Interceptor {
  static const _kTimeout = Duration(seconds: 30);

  @override
  Future<Response<BodyType>> intercept<BodyType>(Chain<BodyType> chain) {
    return Future.value(chain.proceed(chain.request)).timeout(_kTimeout);
  }
}

class RetryInterceptor implements Interceptor {
  final AuthService authService;
  static const int _maxRetries = 3;

  RetryInterceptor(this.authService);

  @override
  FutureOr<Response<BodyType>> intercept<BodyType>(Chain<BodyType> chain) async {
    Response<BodyType> response = await chain.proceed(chain.request);

    if (response.statusCode == 401) {
      final newToken = await authService.refreshToken();
      if (newToken != null && newToken.isNotEmpty) {
        final retryRequest = applyHeader(
          chain.request, 'Authorization', 'Bearer $newToken', override: true,
        );
        response = await chain.proceed(retryRequest);
      }
      return response;
    }

    int attempt = 0;
    while (_isServerError(response.statusCode) && attempt < _maxRetries) {
      await Future.delayed(Duration(seconds: 1 << attempt));
      response = await chain.proceed(chain.request);
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

class ApiClient {
  final String baseUrl;
  final AuthService _authService;
  
  ApiClient({
    this.baseUrl = kBaseUrl,
    AuthService? authService,
  }) : _authService = authService ?? AuthService();

  late final ChopperClient _client = ChopperClient(
    baseUrl: Uri.parse(baseUrl),
    interceptors: [
      TimeoutInterceptor(),
      AuthInterceptor(_authService),
      RetryInterceptor(_authService),
      CurlInterceptor(),
    ],
    converter: const JsonConverter(),
  );

  ChopperClient get client => _client;

  /// Persist explicit patient-declared profile fields on the authoritative backend.
  /// Returns false on validation/network failure; callers must not claim onboarding
  /// is complete until this returns true.
  Future<bool> updatePatientProfile(Map<String, dynamic> updates) async {
    try {
      final response = await _client.patch(
        Uri.parse('/api/v1/profile'),
        body: updates,
      );
      return response.isSuccessful;
    } catch (_) {
      return false;
    }
  }

  /// Envoie un log unique au backend.
  Future<bool> syncLogEntry(Map<String, dynamic> log) async {
    try {
      final response = await _client.post(
        Uri.parse('/api/v1/logs'),
        body: log,
      );
      return response.isSuccessful;
    } catch (_) {
      return false;
    }
  }

  /// Envoie une liste de logs en une seule requête (Batch).
  Future<List<String>> batchSyncLogs(List<Map<String, dynamic>> logs) async {
    try {
      final response = await _client.post(
        Uri.parse('/api/v1/logs/batch'),
        body: logs,
      );
      
      if (response.isSuccessful && response.body != null) {
        final data = response.body as Map<String, dynamic>;
        final syncedIds = List<String>.from(data['synced_ids'] ?? []);
        return syncedIds;
      }
      return [];
    } catch (_) {
      return [];
    }
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
  Future<KpisResponse?> getKpis({int days = 21, double targetLow = 70.0, double targetHigh = 180.0}) async {
    try {
      final response = await _client.get(
        Uri.parse('/api/v1/kpis/?days=$days&target_low=$targetLow&target_high=$targetHigh'),
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
    final token = await _authService.getIdToken();
    final uri = Uri.parse('$baseUrl/api/v1/ai/chat/stream')
        .replace(queryParameters: {'message': message});

    final request = http.Request('GET', uri);
    if (token != null && token.isNotEmpty) {
      request.headers['Authorization'] = 'Bearer $token';
    }

    try {
      final client = http.Client();
      final streamed = await client.send(request);

      String buffer = '';
      await for (final chunk in streamed.stream.transform(utf8.decoder)) {
        buffer += chunk;
        final lines = buffer.split('\n');
        buffer = lines.removeLast();
        for (final line in lines) {
          if (line.startsWith('data: ')) {
            final payload = line.substring(6).trim();
            if (payload == '[DONE]') {
              client.close();
              return;
            }
            try {
              final json = jsonDecode(payload) as Map<String, dynamic>;
              final tok = json['token'] as String?;
              if (tok != null) yield tok;
            } catch (_) {}
          }
        }
      }
      client.close();
    } catch (_) {
      yield 'Une erreur est survenue.';
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
  Future<ChatResponse?> chatWithAmina(String message, {String contextType = 'general'}) async {
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
  Future<VoiceResponse?> sendVoiceMessage(
    Uint8List audioBytes,
    String mimeType, {
    int contextDays = 14,
  }) async {
    try {
      final token = await _authService.getIdToken();
      final uri = Uri.parse('$baseUrl/api/v1/ai/voice?context_days=$contextDays');

      final request = http.MultipartRequest('POST', uri);
      if (token != null && token.isNotEmpty) {
        request.headers['Authorization'] = 'Bearer $token';
      }

      request.files.add(
        http.MultipartFile.fromBytes(
          'audio',
          audioBytes,
          filename: 'voice.${_extFromMime(mimeType)}',
          contentType: MediaType.parse(mimeType),
        ),
      );

      final streamed = await request.send();
      final body = await streamed.stream.bytesToString();

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
  Future<GlucometerOcrResponse?> analyzeGlucometerImage(
    String base64Image,
    String mimeType,
  ) async {
    try {
      final token = await _authService.getIdToken();
      final uri = Uri.parse('$baseUrl/api/v1/ai/analyze-glucometer-image');
      final req = http.Request('POST', uri)
        ..headers['Content-Type'] = 'application/json'
        ..body = jsonEncode({'image_base64': base64Image, 'mime_type': mimeType});
      if (token != null && token.isNotEmpty) {
        req.headers['Authorization'] = 'Bearer $token';
      }
      final streamed = await req.send();
      final body = await streamed.stream.bytesToString();
      if (streamed.statusCode >= 200 && streamed.statusCode < 300) {
        return GlucometerOcrResponse.fromJson(jsonDecode(body) as Map<String, dynamic>);
      }
      return null;
    } catch (_) {
      return null;
    }
  }

  /// Transcribe audio to text (STT only — no IAmina pipeline).
  Future<String?> transcribeAudio(Uint8List audioBytes, String mimeType) async {
    try {
      final token = await _authService.getIdToken();
      final uri = Uri.parse('$baseUrl/api/v1/ai/transcribe');
      final request = http.MultipartRequest('POST', uri);
      if (token != null && token.isNotEmpty) {
        request.headers['Authorization'] = 'Bearer $token';
      }
      request.files.add(http.MultipartFile.fromBytes(
        'audio', audioBytes,
        filename: 'note.${_extFromMime(mimeType)}',
        contentType: MediaType.parse(mimeType),
      ));
      final streamed = await request.send();
      final body = await streamed.stream.bytesToString();
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

  Future<bool> withdrawConsent() async {
    try {
      final response = await _client.delete(Uri.parse('/api/v1/account/consent'));
      return response.isSuccessful;
    } catch (_) {
      return false;
    }
  }

  // ── Modules (chassis) ──────────────────────────────────────────────────────

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
        return MealAnalysisResult.fromJson(response.body as Map<String, dynamic>);
      }
      return null;
    } catch (_) {
      return null;
    }
  }

  // ── Phase 12: Document Pulper ─────────────────────────────────────────────

  Future<PulperPreview?> ingestDocument(
    Uint8List fileBytes,
    String filename,
    String mimeType,
  ) async {
    try {
      final token = await _authService.getIdToken();
      final uri = Uri.parse('$baseUrl/api/v1/documents/ingest?confirm=false');

      final request = http.MultipartRequest('POST', uri);
      if (token != null && token.isNotEmpty) {
        request.headers['Authorization'] = 'Bearer $token';
      }
      request.files.add(
        http.MultipartFile.fromBytes(
          'file',
          fileBytes,
          filename: filename,
          contentType: MediaType.parse(mimeType),
        ),
      );

      final streamed = await request.send()
          .timeout(const Duration(seconds: 60));
      final body = await streamed.stream.bytesToString();

      if (streamed.statusCode >= 200 && streamed.statusCode < 300) {
        final json = jsonDecode(body) as Map<String, dynamic>;
        return PulperPreview.fromJson(json);
      }
      return null;
    } catch (_) {
      return null;
    }
  }

  Future<PulperConfirmResult?> confirmDocumentImport(String batchId) async {
    try {
      final response = await _client.post(
        Uri.parse('/api/v1/documents/confirm/$batchId'),
        body: <String, dynamic>{},
      );
      if (response.isSuccessful && response.body != null) {
        return PulperConfirmResult.fromJson(response.body as Map<String, dynamic>);
      }
      return null;
    } catch (_) {
      return null;
    }
  }

  String _extFromMime(String mime) {
    if (mime.contains('webm')) return 'webm';
    if (mime.contains('mp4') || mime.contains('m4a')) return 'm4a';
    if (mime.contains('wav')) return 'wav';
    if (mime.contains('ogg')) return 'ogg';
    return 'audio';
  }
}
