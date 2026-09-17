import 'dart:async';
import 'dart:convert';
import 'dart:developer' as developer;

import 'package:http/http.dart' as http;

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

  const CompanionChatReply({
    required this.reply,
    required this.conversationId,
    required this.replyLanguage,
  });

  factory CompanionChatReply.fromJson(Map<String, dynamic> json) {
    return CompanionChatReply(
      reply: json['reply'] as String? ?? '',
      conversationId: json['conversation_id'] as String? ?? '',
      replyLanguage: json['reply_language'] as String? ?? 'fr',
    );
  }
}

class CompanionService {
  final AuthService _authService;
  final http.Client _http;
  final String baseUrl;
  final CompanionFailureLogger _failureLogger;

  CompanionService({
    AuthService? authService,
    http.Client? httpClient,
    this.baseUrl = companionApiBaseUrl,
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

  void dispose() => _http.close();
}
