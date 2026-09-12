class ConsentNoticeClaim {
  final String version;
  final String noticeHash;
  final String locale;

  const ConsentNoticeClaim({
    required this.version,
    required this.noticeHash,
    required this.locale,
  });

  bool matches(ConsentNoticeClaim other) =>
      version == other.version &&
      noticeHash == other.noticeHash &&
      locale == other.locale;
}

class ConsentNoticeContract {
  static const String version = '2026-09-12.1';

  static const Map<String, String> _hashes = {
    'fr': '2fc950fc5dadb4add4dc8ad344c48126f2b81bbfa18654762d3bc879f15459cb',
    'en': '2673ef01615fff6fde9fb88bbeb33dec87da3a0c417d4bb854c7fa34867bd706',
    'ar': '2351b0e1ea0930ba874d9f2242d3fc22fc38da9c43adc571942a0f94d0a57b0d',
    // Current Darija UI renders the same Arabic consent copy.
    'ar-MA': '2351b0e1ea0930ba874d9f2242d3fc22fc38da9c43adc571942a0f94d0a57b0d',
  };

  static String normalizeLocale(String locale) {
    final trimmed = locale.trim();
    if (_hashes.containsKey(trimmed)) return trimmed;
    final language = trimmed.split('-').first.toLowerCase();
    if (_hashes.containsKey(language)) return language;
    throw ArgumentError.value(locale, 'locale', 'Unsupported consent locale');
  }

  static ConsentNoticeClaim forLocale(String locale) {
    final normalized = normalizeLocale(locale);
    return ConsentNoticeClaim(
      version: version,
      noticeHash: _hashes[normalized]!,
      locale: normalized,
    );
  }

  static bool isCurrent({
    required String? versionValue,
    required String? noticeHash,
    required String? locale,
  }) {
    if (versionValue == null || noticeHash == null || locale == null) {
      return false;
    }
    try {
      return forLocale(locale).matches(
        ConsentNoticeClaim(
          version: versionValue,
          noticeHash: noticeHash,
          locale: normalizeLocale(locale),
        ),
      );
    } on ArgumentError {
      return false;
    }
  }
}
