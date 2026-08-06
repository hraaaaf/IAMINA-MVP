import 'package:flutter/widgets.dart';

import 'app_localizations.dart';

/// Transitional API used by the five audited pages.
///
/// All user-visible copy is sourced from Flutter ARB files through
/// [AppLocalizations]. This adapter preserves existing call sites while
/// P0-UX-6 migrates them incrementally; it must not contain translations.
class AuditedPageCopy {
  final AppLocalizations l10n;
  final bool isArabic;

  const AuditedPageCopy._(this.l10n, this.isArabic);

  factory AuditedPageCopy.of(BuildContext context) {
    final localizations = AppLocalizations.of(context)!;
    return AuditedPageCopy._(
      localizations,
      Localizations.localeOf(context).languageCode == 'ar',
    );
  }

  String get overview => l10n.overview;
  String get breadcrumb => l10n.breadcrumb;
  String get talk => l10n.talk;
  String get dayShort => l10n.dayShort;

  String sync(String key) => switch (key) {
    'checking' => l10n.syncChecking,
    'upToDate' => l10n.syncUpToDate,
    'pending' => l10n.syncPending,
    'syncing' => l10n.syncing,
    'offline' => l10n.syncOffline,
    _ => l10n.syncFailed,
  };

  String greeting(int hour, String firstName) {
    final base = hour < 12
        ? l10n.goodMorning
        : hour < 18
        ? l10n.goodAfternoon
        : l10n.goodEvening;
    return firstName.isEmpty
        ? l10n.greetingWithoutName(base)
        : l10n.greetingWithName(base, firstName);
  }

  String observation(int range) => l10n.observation(range);
  String get emptyAnalysis => l10n.emptyAnalysis;
  String get latestReading => l10n.latestReading;
  String get justNow => l10n.justNow;
  String minutesAgo(int value) => l10n.minutesAgo(value);

  String meal(String? value) {
    if (value == null || value.isEmpty) return '';
    final normalized = value.toLowerCase();
    if (normalized.contains('après') || normalized.contains('post')) {
      return l10n.afterMeal;
    }
    if (normalized.contains('jeun')) return l10n.fasting;
    return value;
  }

  String targetTitle(int range) => l10n.targetTitle(range);
  String targetCoverage(int count, int days) =>
      l10n.targetCoverage(count, days);
  String get targetReference => l10n.targetReference;
  String get viewJournal => l10n.viewJournal;
  String get readingsInRange => l10n.readingsInRange;
  String get rangeReference => l10n.rangeReference;
  String get inRange => l10n.inRange;
  String get high => l10n.high;
  String get low => l10n.low;
  String get veryHigh => l10n.veryHigh;
  String get targetExplanation => l10n.targetExplanation;

  String get importTitle => l10n.importTitle;
  String get importSubtitle => l10n.importSubtitle;
  String get directConnections => l10n.directConnections;
  String get pulperDescription => l10n.pulperDescription;
  String get labReport => l10n.labReport;
  String get cgmExport => l10n.cgmExport;
  String get prescription => l10n.prescription;
  String get photo => l10n.photo;
  String get soon => l10n.soon;
  String get unavailable => l10n.unavailable;
  String get dexcomDescription => l10n.dexcomDescription;
  String get libreDescription => l10n.libreDescription;
  String get openDocumentImport => l10n.openDocumentImport;
  String get documentTitle => l10n.documentTitle;
  String get documentIntro => l10n.documentIntro;
  String get chooseDocument => l10n.chooseDocument;

  String get profileComplete => l10n.profileComplete;
  String profileCompletionLabel(int percentage) => percentage >= 100
      ? l10n.profileCompleteChecked
      : l10n.profileCompletionPercent(percentage);
  String get profileCompletionPrompt => l10n.profileCompletionPrompt;
  String get minimum => l10n.minimum;
  String get maximum => l10n.maximum;
}
