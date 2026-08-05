import 'package:flutter/widgets.dart';

/// Reviewed UI copy used by the pages covered by the post-P0 visual audit.
///
/// This file provides product localization coverage only. It does not replace
/// the restricted native/clinical safety-corpus approval tracked in ROADMAP.md.
class AuditedPageCopy {
  final String languageCode;

  const AuditedPageCopy._(this.languageCode);

  factory AuditedPageCopy.of(BuildContext context) {
    return AuditedPageCopy._(Localizations.localeOf(context).languageCode);
  }

  String _pick({required String fr, required String en, required String ar}) {
    return switch (languageCode) {
      'ar' => ar,
      'en' => en,
      _ => fr,
    };
  }

  bool get isArabic => languageCode == 'ar';

  String get dashboardOverview => _pick(
    fr: "Vue d'ensemble",
    en: 'Overview',
    ar: 'نظرة عامة',
  );

  String get dashboardBreadcrumb => _pick(
    fr: "Accueil · Vue d'ensemble",
    en: 'Home · Overview',
    ar: 'الرئيسية · نظرة عامة',
  );

  String get talkToIamina => _pick(
    fr: 'Parler à IAmina',
    en: 'Talk to IAmina',
    ar: 'تحدث مع IAmina',
  );

  String get dayShort => _pick(fr: 'j', en: 'd', ar: 'ي');

  String syncLabel(String state) {
    return switch (state) {
      'checking' => _pick(
          fr: 'Vérification de la synchronisation',
          en: 'Checking synchronization',
          ar: 'جارٍ التحقق من المزامنة',
        ),
      'upToDate' => _pick(
          fr: 'Données à jour',
          en: 'Data up to date',
          ar: 'البيانات محدّثة',
        ),
      'pending' => _pick(
          fr: 'Données en attente de synchronisation',
          en: 'Data waiting to sync',
          ar: 'بيانات في انتظار المزامنة',
        ),
      'syncing' => _pick(
          fr: 'Synchronisation en cours',
          en: 'Synchronizing',
          ar: 'جارٍ المزامنة',
        ),
      'offline' => _pick(
          fr: 'Hors ligne · données conservées sur cet appareil',
          en: 'Offline · data kept on this device',
          ar: 'غير متصل · البيانات محفوظة على هذا الجهاز',
        ),
      _ => _pick(
          fr: 'Échec de synchronisation · appuyer pour réessayer',
          en: 'Synchronization failed · tap to retry',
          ar: 'فشلت المزامنة · اضغط لإعادة المحاولة',
        ),
    };
  }

  String greeting(int hour, {String firstName = ''}) {
    final base = hour < 12
        ? _pick(fr: 'Bonjour', en: 'Good morning', ar: 'صباح الخير')
        : hour < 18
            ? _pick(fr: 'Bon après-midi', en: 'Good afternoon', ar: 'مساء الخير')
            : _pick(fr: 'Bonsoir', en: 'Good evening', ar: 'مساء الخير');
    if (firstName.isEmpty) return isArabic ? '$base!' : '$base !';
    return isArabic ? '$base، $firstName' : '$base, $firstName.';
  }

  String dashboardObservation(int range) => _pick(
    fr: "Voici ce qu'IAmina a observé sur vos $range derniers jours.",
    en: 'Here is what IAmina observed over your last $range days.',
    ar: 'إليك ما لاحظته IAmina خلال آخر $range يومًا.',
  );

  String get dashboardEmpty => _pick(
    fr: 'Chargez des données pour voir votre analyse IAmina.',
    en: 'Add data to view your IAmina analysis.',
    ar: 'أضف بيانات لعرض تحليل IAmina.',
  );

  String get latestMeasurement => _pick(
    fr: 'DERNIÈRE MESURE',
    en: 'LATEST READING',
    ar: 'آخر قياس',
  );

  String get justNow => _pick(fr: "à l'instant", en: 'just now', ar: 'الآن');

  String minutesAgo(int minutes) => _pick(
    fr: 'il y a $minutes min',
    en: '$minutes min ago',
    ar: 'منذ $minutes دقيقة',
  );

  String localizeMeal(String? value) {
    if (value == null || value.isEmpty) return '';
    final normalized = value.toLowerCase();
    if (normalized.contains('après') || normalized.contains('post')) {
      return _pick(fr: 'Après repas', en: 'After meal', ar: 'بعد الوجبة');
    }
    if (normalized.contains('jeun')) {
      return _pick(fr: 'À jeun', en: 'Fasting', ar: 'صائم');
    }
    if (normalized.contains('coucher')) {
      return _pick(fr: 'Avant le coucher', en: 'Before bed', ar: 'قبل النوم');
    }
    return value;
  }

  String measurementsInRangeTitle(int range) => _pick(
    fr: 'MESURES DANS LA CIBLE · $range JOURS',
    en: 'READINGS IN RANGE · $range DAYS',
    ar: 'القياسات ضمن النطاق · $range يومًا',
  );

  String targetCoverage(int count, int days) => _pick(
    fr: '$count mesures sur $days jour${days > 1 ? 's' : ''} · proportion de mesures, pas durée CGM',
    en: '$count readings over $days day${days == 1 ? '' : 's'} · share of readings, not CGM duration',
    ar: '$count قياسًا خلال $days يومًا · نسبة قياسات وليست مدة قياس مستمر',
  );

  String get targetGeneralReference => _pick(
    fr: 'Repère général ≥ 70 % · votre cible personnelle peut être différente.',
    en: 'General reference ≥ 70% · your personal target may differ.',
    ar: 'مرجع عام ≥ 70٪ · قد يختلف هدفك الشخصي.',
  );

  String get viewJournal => _pick(
    fr: 'Voir le journal',
    en: 'View journal',
    ar: 'عرض اليومية',
  );

  String get importTitle => _pick(fr: 'Importer', en: 'Import', ar: 'استيراد');

  String get importSubtitle => _pick(
    fr: 'Connectez vos sources de données',
    en: 'Connect your data sources',
    ar: 'اربط مصادر بياناتك',
  );

  String measuresRecorded(int count) => _pick(
    fr: '$count mesure${count > 1 ? 's' : ''} enregistrée${count > 1 ? 's' : ''}',
    en: '$count reading${count == 1 ? '' : 's'} recorded',
    ar: 'تم تسجيل $count قياسًا',
  );

  String lastMeasurement(String relative) => _pick(
    fr: 'Dernière mesure $relative · Stockage local',
    en: 'Latest reading $relative · Local storage',
    ar: 'آخر قياس $relative · تخزين محلي',
  );

  String relativeNow() => _pick(fr: "à l'instant", en: 'just now', ar: 'الآن');

  String relativeMinutes(int value) => _pick(
    fr: 'il y a $value min',
    en: '$value min ago',
    ar: 'منذ $value دقيقة',
  );

  String relativeHours(int value) => _pick(
    fr: 'il y a $value h',
    en: '$value h ago',
    ar: 'منذ $value ساعة',
  );

  String relativeDays(int value) => _pick(
    fr: 'il y a $value j',
    en: '$value d ago',
    ar: 'منذ $value يوم',
  );

  String get directConnections => _pick(
    fr: 'Connexions directes',
    en: 'Direct connections',
    ar: 'اتصالات مباشرة',
  );

  String get pulperDescription => _pick(
    fr: 'PDF · Photo · Excel · Word — IAmina extrait les données pour votre relecture.',
    en: 'PDF · Photo · Excel · Word — IAmina extracts data for your review.',
    ar: 'PDF · صورة · Excel · Word — تستخرج IAmina البيانات لمراجعتك.',
  );

  String get labReport => _pick(fr: 'Bilan labo', en: 'Lab report', ar: 'تحاليل مخبرية');
  String get cgmExport => _pick(fr: 'Export CGM', en: 'CGM export', ar: 'تصدير CGM');
  String get prescriptionDocument => _pick(fr: 'Ordonnance', en: 'Prescription', ar: 'وصفة طبية');
  String get photo => _pick(fr: 'Photo', en: 'Photo', ar: 'صورة');

  String get soon => _pick(fr: 'BIENTÔT', en: 'SOON', ar: 'قريبًا');
  String get unavailable => _pick(fr: 'Non disponible', en: 'Unavailable', ar: 'غير متاح');

  String get dexcomDescription => _pick(
    fr: 'Connexion Dexcom CLARITY prévue. Fréquence et disponibilité à confirmer avant activation.',
    en: 'Dexcom CLARITY connection planned. Frequency and availability must be confirmed before activation.',
    ar: 'ربط Dexcom CLARITY مخطط له. يجب تأكيد التواتر والتوفر قبل التفعيل.',
  );

  String get libreDescription => _pick(
    fr: 'Import LibreView prévu. Formats et disponibilité à confirmer avant activation.',
    en: 'LibreView import planned. Formats and availability must be confirmed before activation.',
    ar: 'استيراد LibreView مخطط له. يجب تأكيد الصيغ والتوفر قبل التفعيل.',
  );

  String get openDocumentImport => _pick(
    fr: "Ouvrir l'import de document",
    en: 'Open document import',
    ar: 'فتح استيراد المستند',
  );

  String get documentImportTitle => _pick(
    fr: 'Importer un document',
    en: 'Import a document',
    ar: 'استيراد مستند',
  );

  String get documentImportIntro => _pick(
    fr: "Importez un document médical. IAmina extrait les données, puis vous devez les relire et les confirmer.",
    en: 'Import a medical document. IAmina extracts the data, then you must review and confirm it.',
    ar: 'استورد مستندًا طبيًا. تستخرج IAmina البيانات ثم يجب عليك مراجعتها وتأكيدها.',
  );

  String get chooseDocument => _pick(
    fr: 'Choisir un document',
    en: 'Choose a document',
    ar: 'اختيار مستند',
  );

  String get profileComplete => _pick(
    fr: 'Profil complet',
    en: 'Profile complete',
    ar: 'الملف مكتمل',
  );

  String get minimum => _pick(fr: 'Min', en: 'Min', ar: 'الحد الأدنى');
  String get maximum => _pick(fr: 'Max', en: 'Max', ar: 'الحد الأقصى');
}
