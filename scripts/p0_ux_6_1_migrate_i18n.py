#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
L10N = ROOT / 'frontend' / 'lib' / 'l10n'

DATA = {
'en': '''overview\tOverview
breadcrumb\tHome · Overview
talk\tTalk to IAmina
dayShort\td
syncChecking\tChecking synchronization
syncUpToDate\tData up to date
syncPending\tData waiting to sync
syncing\tSynchronizing
syncOffline\tOffline · data kept on this device
syncFailed\tSynchronization failed · tap to retry
goodMorning\tGood morning
goodAfternoon\tGood afternoon
goodEvening\tGood evening
greetingWithName\t{greeting}, {firstName}.
greetingWithoutName\t{greeting}!
observation\tHere is what IAmina observed over your last {range} days.
emptyAnalysis\tAdd data to view your IAmina analysis.
latestReading\tLATEST READING
justNow\tjust now
minutesAgo\t{value} min ago
afterMeal\tAfter meal
fasting\tFasting
targetTitle\tREADINGS IN RANGE · {range} DAYS
targetCoverage\t{count} readings over {days} days · share of readings, not CGM duration
targetReference\tGeneral reference ≥ 70% · your personal target may differ.
viewJournal\tView journal
readingsInRange\tReadings in range
rangeReference\tReference 70–180
inRange\tIn range
high\tHigh
low\tLow
veryHigh\tVery high
targetExplanation\tGeneral reference: more than 70% of readings within 70–180 mg/dL. Your personal target may differ.
importTitle\tImport
importSubtitle\tConnect your data sources
directConnections\tDirect connections
pulperDescription\tPDF · Photo · Excel · Word — IAmina extracts data for your review.
labReport\tLab report
cgmExport\tCGM export
prescription\tPrescription
photo\tPhoto
soon\tSOON
unavailable\tUnavailable
dexcomDescription\tDexcom CLARITY connection planned. Frequency and availability must be confirmed before activation.
libreDescription\tLibreView import planned. Formats and availability must be confirmed before activation.
openDocumentImport\tOpen document import
documentTitle\tImport a document
documentIntro\tImport a medical document. IAmina extracts the data, then you must review and confirm it.
chooseDocument\tChoose a document
profileComplete\tProfile complete
profileCompleteChecked\tProfile complete ✓
profileCompletionPercent\tProfile {percentage}% complete
profileCompletionPrompt\tComplete your profile for more precise analyses.
minimum\tMin
maximum\tMax''',
'fr': '''overview\tVue d'ensemble
breadcrumb\tAccueil · Vue d'ensemble
talk\tParler à IAmina
dayShort\tj
syncChecking\tVérification de la synchronisation
syncUpToDate\tDonnées à jour
syncPending\tDonnées en attente de synchronisation
syncing\tSynchronisation en cours
syncOffline\tHors ligne · données conservées sur cet appareil
syncFailed\tÉchec de synchronisation · appuyer pour réessayer
goodMorning\tBonjour
goodAfternoon\tBon après-midi
goodEvening\tBonsoir
greetingWithName\t{greeting}, {firstName}.
greetingWithoutName\t{greeting} !
observation\tVoici ce qu'IAmina a observé sur vos {range} derniers jours.
emptyAnalysis\tChargez des données pour voir votre analyse IAmina.
latestReading\tDERNIÈRE MESURE
justNow\tà l'instant
minutesAgo\til y a {value} min
afterMeal\tAprès repas
fasting\tÀ jeun
targetTitle\tMESURES DANS LA CIBLE · {range} JOURS
targetCoverage\t{count} mesures sur {days} jours · proportion de mesures, pas durée CGM
targetReference\tRepère général ≥ 70 % · votre cible personnelle peut être différente.
viewJournal\tVoir le journal
readingsInRange\tMesures dans la cible
rangeReference\tRepère 70–180
inRange\tDans la cible
high\tÉlevé
low\tBas
veryHigh\tTrès élevé
targetExplanation\tRepère général : plus de 70 % des mesures dans 70–180 mg/dL. Votre cible personnelle peut être différente.
importTitle\tImporter
importSubtitle\tConnectez vos sources de données
directConnections\tConnexions directes
pulperDescription\tPDF · Photo · Excel · Word — IAmina extrait les données pour votre relecture.
labReport\tBilan labo
cgmExport\tExport CGM
prescription\tOrdonnance
photo\tPhoto
soon\tBIENTÔT
unavailable\tNon disponible
dexcomDescription\tConnexion Dexcom CLARITY prévue. Fréquence et disponibilité à confirmer avant activation.
libreDescription\tImport LibreView prévu. Formats et disponibilité à confirmer avant activation.
openDocumentImport\tOuvrir l'import de document
documentTitle\tImporter un document
documentIntro\tImportez un document médical. IAmina extrait les données, puis vous devez les relire et les confirmer.
chooseDocument\tChoisir un document
profileComplete\tProfil complet
profileCompleteChecked\tProfil complet ✓
profileCompletionPercent\tProfil complété à {percentage}%
profileCompletionPrompt\tComplétez votre profil pour des analyses plus précises.
minimum\tMin
maximum\tMax''',
'ar': '''overview\tنظرة عامة
breadcrumb\tالرئيسية · نظرة عامة
talk\tتحدث مع IAmina
dayShort\tي
syncChecking\tجارٍ التحقق من المزامنة
syncUpToDate\tالبيانات محدّثة
syncPending\tبيانات في انتظار المزامنة
syncing\tجارٍ المزامنة
syncOffline\tغير متصل · البيانات محفوظة على هذا الجهاز
syncFailed\tفشلت المزامنة · اضغط لإعادة المحاولة
goodMorning\tصباح الخير
goodAfternoon\tمساء الخير
goodEvening\tمساء الخير
greetingWithName\t{greeting}، {firstName}
greetingWithoutName\t{greeting}!
observation\tإليك ما لاحظته IAmina خلال آخر {range} يومًا.
emptyAnalysis\tأضف بيانات لعرض تحليل IAmina.
latestReading\tآخر قياس
justNow\tالآن
minutesAgo\tمنذ {value} دقيقة
afterMeal\tبعد الوجبة
fasting\tصائم
targetTitle\tالقياسات ضمن النطاق · {range} يومًا
targetCoverage\t{count} قياسًا خلال {days} يومًا · نسبة قياسات وليست مدة قياس مستمر
targetReference\tمرجع عام ≥ 70٪ · قد يختلف هدفك الشخصي.
viewJournal\tعرض اليومية
readingsInRange\tالقياسات ضمن النطاق
rangeReference\tمرجع 70–180
inRange\tضمن النطاق
high\tمرتفع
low\tمنخفض
veryHigh\tمرتفع جدًا
targetExplanation\tمرجع عام: أكثر من 70٪ من القياسات بين 70 و180 mg/dL. قد يختلف هدفك الشخصي.
importTitle\tاستيراد
importSubtitle\tاربط مصادر بياناتك
directConnections\tاتصالات مباشرة
pulperDescription\tPDF · صورة · Excel · Word — تستخرج IAmina البيانات لمراجعتك.
labReport\tتحاليل مخبرية
cgmExport\tتصدير CGM
prescription\tوصفة طبية
photo\tصورة
soon\tقريبًا
unavailable\tغير متاح
dexcomDescription\tربط Dexcom CLARITY مخطط له. يجب تأكيد التواتر والتوفر قبل التفعيل.
libreDescription\tاستيراد LibreView مخطط له. يجب تأكيد الصيغ والتوفر قبل التفعيل.
openDocumentImport\tفتح استيراد المستند
documentTitle\tاستيراد مستند
documentIntro\tاستورد مستندًا طبيًا. تستخرج IAmina البيانات ثم يجب عليك مراجعتها وتأكيدها.
chooseDocument\tاختيار مستند
profileComplete\tالملف مكتمل
profileCompleteChecked\tالملف مكتمل ✓
profileCompletionPercent\tاكتمل الملف بنسبة {percentage}٪
profileCompletionPrompt\tأكمل ملفك للحصول على تحليلات أدق.
minimum\tالحد الأدنى
maximum\tالحد الأقصى''',
}

META = {
    'greetingWithName': {'placeholders': {'greeting': {'type': 'String'}, 'firstName': {'type': 'String'}}},
    'greetingWithoutName': {'placeholders': {'greeting': {'type': 'String'}}},
    'observation': {'placeholders': {'range': {'type': 'int'}}},
    'minutesAgo': {'placeholders': {'value': {'type': 'int'}}},
    'targetTitle': {'placeholders': {'range': {'type': 'int'}}},
    'targetCoverage': {'placeholders': {'count': {'type': 'int'}, 'days': {'type': 'int'}}},
    'profileCompletionPercent': {'placeholders': {'percentage': {'type': 'int'}}},
}

ADAPTER = r'''import 'package:flutter/widgets.dart';

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
  String targetCoverage(int count, int days) => l10n.targetCoverage(count, days);
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
'''

for locale, rows in DATA.items():
    path = L10N / f'app_{locale}.arb'
    payload = json.loads(path.read_text(encoding='utf-8'))
    for row in rows.splitlines():
        key, value = row.split('\t', 1)
        payload[key] = value
        if key in META:
            payload[f'@{key}'] = META[key]
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

(L10N / 'audited_page_copy.dart').write_text(ADAPTER, encoding='utf-8')

TEST = r'''import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('audited page copy contains no embedded translations', () {
    final source = File('lib/l10n/audited_page_copy.dart').readAsStringSync();
    expect(source, contains('AppLocalizations'));
    expect(source, isNot(contains('String pick(')));
    expect(source, isNot(contains("fr:")));
    expect(source, isNot(contains("en:")));
    expect(source, isNot(contains("ar:")));
  });
}
'''

test_path = ROOT / 'frontend' / 'test' / 'l10n' / 'audited_page_copy_source_test.dart'
test_path.parent.mkdir(parents=True, exist_ok=True)
test_path.write_text(TEST, encoding='utf-8')
