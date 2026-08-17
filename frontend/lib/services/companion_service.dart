import 'dart:convert';

import 'package:http/http.dart' as http;

import '../data/models/companion_models.dart';
import '../data/models/proactive_preview_models.dart';
import 'auth_service.dart';

const String companionApiBaseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'http://localhost:8000',
);

class CompanionService {
  final AuthService _authService;
  final http.Client _http;
  final String baseUrl;

  CompanionService({
    AuthService? authService,
    http.Client? httpClient,
    this.baseUrl = companionApiBaseUrl,
  }) : _authService = authService ?? AuthService(),
       _http = httpClient ?? http.Client();

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
    } catch (_) {
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
    } catch (_) {
      return null;
    }
  }

  void dispose() => _http.close();
}
