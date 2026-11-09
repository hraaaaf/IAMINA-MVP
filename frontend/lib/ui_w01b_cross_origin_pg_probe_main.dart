// CI-only probe: browser Flutter Web -> Django API -> real PostgreSQL.
// Not imported from the patient app. Only public synthetic health data.
// ignore: avoid_web_libraries_in_flutter
import 'dart:html' as html;
import 'dart:convert';

import 'package:http/http.dart' as http;

const _baseUrl = String.fromEnvironment('API_BASE_URL', defaultValue: '');

Future<void> main() async {
  html.document.title = 'IAMINA_W01B_PENDING';
  try {
    // Reject accidental production or non-loopback API targets in this probe.
    if (_baseUrl != 'http://127.0.0.1:8000') {
      throw StateError('Only local synthetic Django is allowed');
    }
    final response = await http
        .get(Uri.parse('$_baseUrl/api/v1/health'))
        .timeout(const Duration(seconds: 15));
    if (response.statusCode != 200) {
      throw StateError('API status was not 200');
    }
    final payload = jsonDecode(response.body);
    if (payload is! Map<String, dynamic> ||
        payload['status'] != 'ok' ||
        payload['db'] != 'ok') {
      throw StateError('API/PG health proof was not confirmed');
    }
    html.document.title = 'IAMINA_W01B_WEB_API_POSTGRES_PASS';
  } catch (error) {
    html.document.title = 'IAMINA_W01B_WEB_API_POSTGRES_FAIL:${error.runtimeType}';
  }
}
