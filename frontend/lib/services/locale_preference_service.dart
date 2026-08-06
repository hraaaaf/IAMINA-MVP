import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import 'api_client.dart';

class LocalExperiencePreference {
  final String language;
  final String country;
  final String tone;

  const LocalExperiencePreference({
    required this.language,
    required this.country,
    required this.tone,
  });
}

class LocalePreferenceService extends ChangeNotifier {
  static const _languageKey = 'iamina.ui_language';
  static const _countryKey = 'iamina.country';
  static const _toneKey = 'iamina.local_tone';

  final ApiClient _apiClient;
  final Locale? _auditLocale;
  final FlutterSecureStorage _storage;

  Locale _locale = const Locale('fr');
  String _country = 'MA';
  String _tone = 'neutral';
  bool _loaded = false;

  LocalePreferenceService(
    this._apiClient, {
    Locale? auditLocale,
    FlutterSecureStorage storage = const FlutterSecureStorage(),
  }) : _auditLocale = auditLocale,
       _storage = storage;

  Locale get locale => _locale;
  String get country => _country;
  String get tone => _tone;
  bool get loaded => _loaded;
  bool get isAuditLocale => _auditLocale != null;

  static Locale localeFromResolvedLanguage(Object? value) => switch (value) {
    'ar' => const Locale('ar'),
    'en' => const Locale('en'),
    _ => const Locale('fr'),
  };

  Future<void> refresh() async {
    final auditLocale = _auditLocale;
    if (auditLocale != null) {
      _locale = auditLocale;
      _loaded = true;
      notifyListeners();
      return;
    }

    final localLanguage = await _storage.read(key: _languageKey);
    final localCountry = await _storage.read(key: _countryKey);
    final localTone = await _storage.read(key: _toneKey);
    if (localLanguage != null)
      _locale = localeFromResolvedLanguage(localLanguage);
    if (localCountry != null && localCountry.isNotEmpty)
      _country = localCountry;
    if (localTone != null && localTone.isNotEmpty) _tone = localTone;

    try {
      final response = await _apiClient.client.get(
        Uri.parse('/api/v1/profile/locale'),
      );
      if (response.isSuccessful && response.body is Map<String, dynamic>) {
        final resolved = (response.body as Map<String, dynamic>)['resolved'];
        if (resolved is Map<String, dynamic> && localLanguage == null) {
          _locale = localeFromResolvedLanguage(resolved['ui_language']);
        }
      }
    } catch (_) {
      // The local choice remains authoritative while offline or signed out.
    } finally {
      _loaded = true;
      notifyListeners();
    }
  }

  Future<void> setExperience({
    required String language,
    required String country,
    required String tone,
  }) async {
    _locale = localeFromResolvedLanguage(language);
    _country = country;
    _tone = tone;
    await Future.wait([
      _storage.write(key: _languageKey, value: language),
      _storage.write(key: _countryKey, value: country),
      _storage.write(key: _toneKey, value: tone),
    ]);
    _loaded = true;
    notifyListeners();
  }
}
