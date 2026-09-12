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
    'fr': '6da07cc7cb585b7690e181563984806163ceb667682203afa39575b3221e5cbd',
    'en': '111609419beaef233463bc8d91a691468ab16ffe80b8f817ba51e8d0667cc65c',
    'ar': 'dc7978b3b20548e1327c03110adb9fb092a9af27b0eab35151143f89897b897',
    // Current Darija UI renders the same Arabic consent copy.
    'ar-MA': 'dc7978b3b20548e1327c03110adb9fb092a9af27b0eab35151143f89897b897',
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
