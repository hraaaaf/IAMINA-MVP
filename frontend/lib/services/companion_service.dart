import 'dart:async';
import 'dart:convert';
import 'dart:developer' as developer;
import 'dart:typed_data';

import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';

import '../data/models/ai_models.dart';
import '../data/models/companion_models.dart';
import '../data/models/companion_next_action_models.dart';
import '../data/models/proactive_preview_models.dart';
import 'api_client.dart';
import 'auth_service.dart';

const String companionApiBaseUrl = kBaseUrl;

typedef CompanionFailureLogger = void Function(
  String operation,
  String errorType,
  StackTrace stackTrace,
);

class CompanionChatReply {
  final String reply;
  final String conversationId;
  final String replyLanguage;
  final bool isEmergency;

  const CompanionChatReply({
    required this.reply,
    required this.conversationId,
    required this.replyLanguage,
    this.isEmergency = false,
  });

  factory CompanionChatReply.fromJson(Map<String, dynamic> json) {
    return CompanionChatReply(
      reply: json['reply'] as String? ?? '',
      conversationId: json['conversation_id'] as String? ?? '',
      replyLanguage: json['reply_language'] as String? ?? 'fr',
      isEmergency: json['is_emergency'] as bool? ?? false,
    );
  }
}

class _DemoHistoryTurn {
  final String role;
  final String content;

  const _DemoHistoryTurn(this.role, this.content);

  Map<String, String> toJson() => {'role': role, 'content': content};
}

class CompanionService {
  final AuthService _authService;
  final http.Client _http;
  final String baseUrl;
  final String demoLanguage;
  final CompanionFailureLogger _failureLogger;
  final List<_DemoHistoryTurn> _demoHistory = <_DemoHistoryTurn>[];

  static const int _demoMaxHistoryItems = 20;
  static const int _demoMaxHistoryChars = 6000;

  CompanionService({
    AuthService? authService,
    http.Client? httpClient,
    this.baseUrl = companionApiBaseUrl,
    this.demoLanguage = 'fr',
    CompanionFailureLogger? failureLogger,
  }) : _authService = authService ?? AuthService(),
       _http = httpClient ?? http.Client(),
       _failureLogger = failureLogger ?? _defaultFailureLogger;

  static void _defaultFailureLogger(
    String operation,
    String errorType,
    StackTrace stackTrace,
  ) {
    developer.log(
      'Safe companion fallback invoked for $errorType.',
      name: 'iamina.companion.$operation',
      stackTrace: stackTrace,
    );
  }

  Future<CompanionOverview?> fetchOverview() async {
    try {
      final token = await _authService.getIdToken();
      if (token == null || token.isEmpty) return null;
      final response = await _http
          .get(
            Uri.parse('$baseUrl/api/v1/companion/overview'),
            headers: {'Authorization': 'Bearer $token'},
          )
          .timeout(const Duration(seconds: 30));
      if (response.statusCode != 200) return null;
      final decoded = jsonDecode(response.body);
      if (decoded is! Map) return null;
      return CompanionOverview.fromJson(Map<String, dynamic>.from(decoded));
    } catch (error, stackTrace) {
      _failureLogger(
        'fetch_overview',
        error.runtimeType.toString(),
        stackTrace,
      );
      return null;
    }
  }

  Future<ProactivePreview?> fetchProactivePreview() async {
    try {
      final token = await _authService.getIdToken();
      if (token == null || token.isEmpty) return null;
      final response = await _http
          .get(
            Uri.parse('$baseUrl/api/v1/proactive-insights/preview/'),
            headers: {'Authorization': 'Bearer $token'},
          )
          .timeout(const Duration(seconds: 30));
      if (response.statusCode != 200) return null;
      final decoded = jsonDecode(response.body);
      if (decoded is! Map) return null;
      return ProactivePreview.fromJson(Map<String, dynamic>.from(decoded));
    } catch (error, stackTrace) {
      _failureLogger(
        'fetch_proactive_preview',
        error.runtimeType.toString(),
        stackTrace,
      );
      return null;
    }
  }

  Future<CompanionNextAction?> evaluateNextAction() async {
    try {
      final token = await _authService.getIdToken();
      if (token == null || token.isEmpty) return null;
      final response = await _http
          .post(
            Uri.parse('$baseUrl/api/v1/companion/next-action/evaluate/'),
            headers: {'Authorization': 'Bearer $token'},
          )
          .timeout(const Duration(seconds: 30));
      if (response.statusCode != 200) return null;
      final decoded = jsonDecode(response.body);
      if (decoded is! Map) return null;
      return CompanionNextAction.fromJson(Map<String, dynamic>.from(decoded));
    } catch (error, stackTrace) {
      _failureLogger(
        'evaluate_next_action',
        error.runtimeType.toString(),
        stackTrace,
      );
      return null;
    }
  }

  Future<CompanionChatReply?> sendChatMessage(
    String message, {
    int contextDays = 14,
  }) async {
    final trimmed = message.trim();
    if (trimmed.isEmpty) return null;

    if (_authService.isAuditSession) {
      return _sendDemoChat(trimmed);
    }

    final token = await _authService.getIdToken();
    if (token == null || token.isEmpty) {
      throw const ProviderApiException(
        code: 'authentication_required',
        message: 'Authentication is required.',
        retryable: false,
        statusCode: 401,
      );
    }

    try {
      final response = await _http
          .post(
            Uri.parse('$baseUrl/api/v1/ai/chat'),
            headers: {
              'Authorization': 'Bearer $token',
              'Content-Type': 'application/json',
            },
            body: jsonEncode({
              'message': trimmed,
              'context_days': contextDays,
            }),
          )
          .timeout(const Duration(seconds: 45));

      if (response.statusCode != 200) {
        try {
          final decoded = jsonDecode(response.body);
          if (decoded is Map) {
            throw ProviderApiException.fromJson(
              Map<String, dynamic>.from(decoded),
              statusCode: response.statusCode,
            );
          }
        } on ProviderApiException {
          rethrow;
        } catch (_) {}
        throw ProviderApiException.unknown(statusCode: response.statusCode);
      }

      final decoded = jsonDecode(response.body);
      if (decoded is! Map) {
        throw const ProviderApiException(
          code: 'provider_malformed_response',
          message: 'The AI service returned an invalid response.',
          retryable: true,
          statusCode: 502,
        );
      }
      final reply = CompanionChatReply.fromJson(
        Map<String, dynamic>.from(decoded),
      );
      if (reply.reply.trim().isEmpty) {
        throw const ProviderApiException(
          code: 'provider_malformed_response',
          message: 'The AI service returned an invalid response.',
          retryable: true,
          statusCode: 502,
        );
      }
      return reply;
    } on ProviderApiException {
      rethrow;
    } on TimeoutException {
      throw const ProviderApiException(
        code: 'provider_timeout',
        message: 'The AI service did not respond in time.',
        retryable: true,
        statusCode: 503,
      );
    } on http.ClientException {
      throw const ProviderApiException(
        code: 'provider_unavailable',
        message: 'The AI service is temporarily unavailable.',
        retryable: true,
        statusCode: 503,
      );
    } catch (_) {
      throw const ProviderApiException(
        code: 'provider_internal_failure',
        message: 'The AI request could not be completed safely.',
        retryable: false,
        statusCode: 500,
      );
    }
  }

  Future<VoiceResponse?> sendVoiceMessage(
    Uint8List audioBytes,
    String mimeType, {
    int contextDays = 14,
  }) async {
    if (audioBytes.isEmpty) return null;

    final token = await _authService.getIdToken();
    if (token == null || token.isEmpty) {
      throw const ProviderApiException(
        code: 'authentication_required',
        message: 'Authentication is required.',
        retryable: false,
        statusCode: 401,
      );
    }

    final uri = Uri.parse(
      '$baseUrl/api/v1/ai/voice?context_days=$contextDays',
    );
    final request = http.MultipartRequest('POST', uri)
      ..headers['Authorization'] = 'Bearer $token'
      ..files.add(
        http.MultipartFile.fromBytes(
          'audio',
          audioBytes,
          filename: 'voice.${_voiceExtensionFromMime(mimeType)}',
          contentType: MediaType.parse(mimeType),
        ),
      );

    try {
      final streamed = await _http
          .send(request)
          .timeout(const Duration(seconds: 45));
      final body = await streamed.stream.bytesToString();

      if (streamed.statusCode < 200 || streamed.statusCode >= 300) {
        try {
          final decoded = jsonDecode(body);
          if (decoded is Map) {
            throw ProviderApiException.fromJson(
              Map<String, dynamic>.from(decoded),
              statusCode: streamed.statusCode,
            );
          }
        } on ProviderApiException {
          rethrow;
        } catch (_) {}
        throw ProviderApiException.unknown(statusCode: streamed.statusCode);
      }

      final decoded = jsonDecode(body);
      if (decoded is! Map) {
        throw const ProviderApiException(
          code: 'provider_malformed_response',
          message: 'The AI service returned an invalid response.',
          retryable: true,
          statusCode: 502,
        );
      }
      final reply = VoiceResponse.fromJson(Map<String, dynamic>.from(decoded));
      if (reply.reply.trim().isEmpty) {
        throw const ProviderApiException(
          code: 'provider_malformed_response',
          message: 'The AI service returned an invalid response.',
          retryable: true,
          statusCode: 502,
        );
      }
      return reply;
    } on ProviderApiException {
      rethrow;
    } on TimeoutException {
      throw const ProviderApiException(
        code: 'provider_timeout',
        message: 'The AI service did not respond in time.',
        retryable: true,
        statusCode: 503,
      );
    } on http.ClientException {
      throw const ProviderApiException(
        code: 'provider_unavailable',
        message: 'The AI service is temporarily unavailable.',
        retryable: true,
        statusCode: 503,
      );
    } catch (_) {
      throw const ProviderApiException(
        code: 'provider_internal_failure',
        message: 'The AI request could not be completed safely.',
        retryable: false,
        statusCode: 500,
      );
    }
  }

  Future<CompanionChatReply> _sendDemoChat(String message) async {
    try {
      final response = await _http
          .post(
            Uri.parse('$baseUrl/api/v1/demo/chat'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({
              'message': message,
              'language': demoLanguage,
              'history': _demoHistory.map((turn) => turn.toJson()).toList(),
            }),
          )
          .timeout(const Duration(seconds: 15));

      if (response.statusCode != 200) {
        return _demoReply(message);
      }

      final decoded = jsonDecode(response.body);
      if (decoded is! Map) return _demoReply(message);
      final reply = CompanionChatReply.fromJson(
        Map<String, dynamic>.from(decoded),
      );
      if (reply.reply.trim().isEmpty) return _demoReply(message);
      if (!reply.isEmergency) {
        _rememberDemoExchange(message, reply.reply);
      }
      return reply;
    } catch (error, stackTrace) {
      _failureLogger(
        'demo_chat',
        error.runtimeType.toString(),
        stackTrace,
      );
      return _demoReply(message);
    }
  }

  void _rememberDemoExchange(String userMessage, String assistantReply) {
    _demoHistory
      ..add(_DemoHistoryTurn('user', userMessage))
      ..add(_DemoHistoryTurn('assistant', assistantReply));

    int totalChars() =>
        _demoHistory.fold(0, (sum, turn) => sum + turn.content.length);

    while (_demoHistory.length > _demoMaxHistoryItems ||
        totalChars() > _demoMaxHistoryChars) {
      if (_demoHistory.length >= 2) {
        _demoHistory.removeRange(0, 2);
      } else {
        _demoHistory.clear();
      }
    }
  }

  CompanionChatReply _demoReply(String message) {
    final normalized = message.toLowerCase();
    final isArabic = RegExp(r'[\u0600-\u06FF]').hasMatch(message);
    final isEnglishGreeting = normalized == 'hello' || normalized == 'hi';
    final isFrenchGreeting = normalized == 'bonjour' || normalized == 'salut';
    final isArabicGreeting =
        normalized == 'مرحبا' || normalized == 'السلام عليكم';

    final language = isArabic
        ? 'ar'
        : isEnglishGreeting
            ? 'en'
            : 'fr';

    final reply = switch (language) {
      'ar' => isArabicGreeting
          ? 'مرحبًا 👋 أنا IAmina في وضع العرض المحلي. محادثة الخادم غير متاحة الآن، لكن يمكنني متابعة عرض الواجهة هنا.'
          : 'وضع العرض المحلي: محادثة الخادم غير متاحة الآن. يمكنني متابعة عرض الواجهة، ثم حاول مجددًا لاحقًا.',
      'en' => 'Hello 👋 I’m IAmina in local demo fallback. The server conversation is unavailable right now, but the demo interface still works.',
      _ => isFrenchGreeting
          ? 'Bonjour 👋 Je suis IAmina en mode démo local. La conversation serveur est indisponible pour le moment, mais l’interface reste utilisable.'
          : 'Mode démo local : la conversation serveur est indisponible pour le moment. Je peux continuer à montrer l’interface, puis réessaie plus tard.',
    };

    return CompanionChatReply(
      reply: reply,
      conversationId: 'demo-local',
      replyLanguage: language,
    );
  }

  static String _voiceExtensionFromMime(String mimeType) {
    return switch (mimeType.split(';').first.trim().toLowerCase()) {
      'audio/webm' => 'webm',
      'audio/mp4' || 'audio/m4a' || 'audio/x-m4a' => 'm4a',
      'audio/wav' || 'audio/x-wav' => 'wav',
      'audio/ogg' || 'audio/x-ogg' => 'ogg',
      'audio/mpeg' || 'audio/mp3' => 'mp3',
      _ => 'audio',
    };
  }

  void dispose() => _http.close();
}
