import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import 'api_client.dart';
import 'auth_service.dart';
import 'country_choices.dart';

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

enum LocaleResolutionSource {
  audit,
  explicitLocal,
  account,
  storedLocal,
  system,
  baseline,
}

class ResolvedLocalePreference {
  final Locale locale;
  final LocaleResolutionSource source;

  const ResolvedLocalePreference(this.locale, this.source);
}

class LocalePreferenceService extends ChangeNotifier {
  static const _languageKey = 'iamina.ui_language';
  static const _countryKey = 'iamina.country';
  static const _toneKey = 'iamina.local_tone';
  static const _explicitKey = 'iamina.locale_explicitly_selected';
  static const _supportedLanguages = {'ar', 'en', 'fr'};
  static const _supportedTones = {'neutral', 'friendly'};

  final ApiClient _apiClient;
  final Locale? _auditLocale;
  final FlutterSecureStorage _storage;
  final Locale _systemLocale;

  Locale _locale = const Locale('fr');
  LocaleResolutionSource _resolutionSource = LocaleResolutionSource.baseline;
  String? _country;
  String _tone = 'neutral';
  bool _loaded = false;

  LocalePreferenceService(
    this._apiClient, {
    Locale? auditLocale,
    FlutterSecureStorage storage = const FlutterSecureStorage(),
    Locale? systemLocale,
  }) : _auditLocale = auditLocale,
       _storage = storage,
       _systemLocale = systemLocale ??
           WidgetsBinding.instance.platformDispatcher.locale;

  Locale get locale => _locale;
  LocaleResolutionSource get resolutionSource => _resolutionSource;
  String? get country => _country;
  String get tone => _tone;
  bool get loaded => _loaded;
  bool get isAuditLocale => _auditLocale != null;

  static String? normalizedLanguage(Object? value) {
    if (value is Locale) {
      return normalizedLanguage(value.languageCode);
    }
    if (value is! String) return null;
    final normalized = value.trim().toLowerCase().replaceAll('_', '-');
    if (normalized.isEmpty) return null;
    final language = normalized.split('-').first;
    return _supportedLanguages.contains(language) ? language : null;
  }

  static Locale? supportedLocale(Object? value) {
    final language = normalizedLanguage(value);
    return language == null ? null : Locale(language);
  }

  static ResolvedLocalePreference resolveLocale({
    Locale? auditLocale,
    Object? explicitLocalLanguage,
    Object? accountLanguage,
    Object? storedLocalLanguage,
    Object? systemLocale,
  }) {
    final candidates = <(Object?, LocaleResolutionSource)>[
      (auditLocale, LocaleResolutionSource.audit),
      (explicitLocalLanguage, LocaleResolutionSource.explicitLocal),
      (accountLanguage, LocaleResolutionSource.account),
      (storedLocalLanguage, LocaleResolutionSource.storedLocal),
      (systemLocale, LocaleResolutionSource.system),
    ];
    for (final candidate in candidates) {
      final locale = supportedLocale(candidate.$1);
      if (locale != null) {
        return ResolvedLocalePreference(locale, candidate.$2);
      }
    }
    return const ResolvedLocalePreference(
      Locale('fr'),
      LocaleResolutionSource.baseline,
    );
  }

  Future<void> refresh() async {
    final localLanguage = await _storage.read(key: _languageKey);
    final localCountry = await _storage.read(key: _countryKey);
    final localTone = await _storage.read(key: _toneKey);
    final isExplicit = await _storage.read(key: _explicitKey) == 'true';

    // An unset country remains unknown, never silently Morocco.
    _country = countryByCode(localCountry)?.code;
    if (localTone != null && _supportedTones.contains(localTone)) {
      _tone = localTone;
    }

    Object? accountLanguage;
    if (_auditLocale == null) {
      if (!kOfflineDemo) {
        try {
          final response = await _apiClient.client.get(
            Uri.parse('/api/v1/profile/locale'),
          );
          if (response.isSuccessful && response.body is Map<String, dynamic>) {
            final resolved = (response.body as Map<String, dynamic>)['resolved'];
            if (resolved is Map<String, dynamic>) {
              accountLanguage = resolved['ui_language'];
            }
          }
        } catch (_) {
          // Resolution continues with local and system inputs.
        }
      }
    }

    final resolved = resolveLocale(
      auditLocale: _auditLocale,
      explicitLocalLanguage: isExplicit ? localLanguage : null,
      accountLanguage: accountLanguage,
      storedLocalLanguage: isExplicit ? null : localLanguage,
      systemLocale: _systemLocale,
    );
    _locale = resolved.locale;
    _resolutionSource = resolved.source;
    _loaded = true;
    notifyListeners();
  }

  /// Persist only an explicitly chosen UI language during onboarding.
  ///
  /// A language selection must not silently persist Morocco or any other
  /// country before the person completes the separate country question.
  Future<void> setLanguageOnly(String language) async {
    final locale = supportedLocale(language);
    if (locale == null) {
      throw ArgumentError.value(language, 'language', 'Unsupported language');
    }
    await Future.wait([
      _storage.write(key: _languageKey, value: locale.languageCode),
      _storage.write(key: _explicitKey, value: 'true'),
    ]);
    _locale = locale;
    _resolutionSource = LocaleResolutionSource.explicitLocal;
    _loaded = true;
    notifyListeners();
  }

  /// Optional, fallible country-by-IP estimate from IAMINA's existing API.
  /// This never persists or changes the user's chosen country.
  Future<String?> suggestCountryFromIp() async {
    try {
      final response = await _apiClient.client
          .get(Uri.parse('/api/v1/country/suggestion'))
          .timeout(const Duration(seconds: 4));
      if (!response.isSuccessful || response.body is! Map) return null;
      return countryByCode((response.body as Map)['country_code'])?.code;
    } catch (_) {
      return null; // Offline / unknown geo: explicit manual choice.
    }
  }

  Future<void> setExperience({
    required String language,
    required String country,
    required String tone,
  }) async {
    final locale = supportedLocale(language);
    if (locale == null) {
      throw ArgumentError.value(language, 'language', 'Unsupported language');
    }
    if (!_supportedTones.contains(tone)) {
      throw ArgumentError.value(tone, 'tone', 'Unsupported tone');
    }
    final normalizedCountry = countryByCode(country)?.code;
    if (normalizedCountry == null) {
      throw ArgumentError.value(country, 'country', 'Unsupported country');
    }

    _locale = locale;
    _resolutionSource = LocaleResolutionSource.explicitLocal;
    _country = normalizedCountry;
    _tone = tone;
    await Future.wait([
      _storage.write(key: _languageKey, value: locale.languageCode),
      _storage.write(key: _countryKey, value: normalizedCountry),
      _storage.write(key: _toneKey, value: tone),
      _storage.write(key: _explicitKey, value: 'true'),
    ]);
    _loaded = true;
    notifyListeners();
  }
}
