import 'package:flutter/material.dart';

import 'api_client.dart';

class LocalePreferenceService extends ChangeNotifier {
  final ApiClient _apiClient;
  final Locale? _auditLocale;

  Locale _locale = const Locale('fr');
  bool _loaded = false;

  LocalePreferenceService(this._apiClient, {Locale? auditLocale})
      : _auditLocale = auditLocale;

  Locale get locale => _locale;
  bool get loaded => _loaded;
  bool get isAuditLocale => _auditLocale != null;

  static Locale localeFromResolvedLanguage(Object? value) {
    switch (value) {
      case 'ar':
        return const Locale('ar');
      case 'en':
        return const Locale('en');
      case 'fr':
      default:
        return const Locale('fr');
    }
  }

  Future<void> refresh() async {
    final auditLocale = _auditLocale;
    if (auditLocale != null) {
      _locale = auditLocale;
      _loaded = true;
      notifyListeners();
      return;
    }

    try {
      final response = await _apiClient.client.get(
        Uri.parse('/api/v1/profile/locale'),
      );
      if (response.isSuccessful && response.body is Map<String, dynamic>) {
        final body = response.body as Map<String, dynamic>;
        final resolved = body['resolved'];
        if (resolved is Map<String, dynamic>) {
          _locale = localeFromResolvedLanguage(resolved['ui_language']);
        }
      }
    } catch (_) {
      // Fail closed to the deterministic French baseline.
      _locale = const Locale('fr');
    } finally {
      _loaded = true;
      notifyListeners();
    }
  }
}
