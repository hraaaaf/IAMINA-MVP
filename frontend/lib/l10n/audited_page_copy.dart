import 'package:flutter/widgets.dart';

/// Product UI copy for the pages covered by the post-P0 visual audit.
/// This does not replace the restricted native/clinical corpus approval gate.
class AuditedPageCopy {
  final String languageCode;

  const AuditedPageCopy._(this.languageCode);

  factory AuditedPageCopy.of(BuildContext context) =>
      AuditedPageCopy._(Localizations.localeOf(context).languageCode);

  String pick({required String fr, required String en, required String ar}) =>
      switch (languageCode) {
        'ar' => ar,
        'en' => en,
        _ => fr,
      };

  bool get isArabic => languageCode == 'ar';
  String get overview =>
      pick(fr: "Vue d'ensemble", en: 'Overview', ar: 'نظرة عامة');
  String get breadcrumb => pick(
    fr: "Accueil · Vue d'ensemble",
    en: 'Home · Overview',
    ar: 'الرئيسية · نظرة عامة',
  );
  String get talk =>
      pick(fr: 'Parler à IAmina', en: 'Talk to IAmina', ar: 'تحدث مع IAmina');
  String get dayShort => pick(fr: 'j', en: 'd', ar: 'ي');

  String sync(String key) => switch (key) {
    'checking' => pick(
      fr: 'Vérification de la synchronisation',
      en: 'Checking synchronization',
      ar: 'جارٍ التحقق من المزامنة',
    ),
    'upToDate' => pick(
      fr: 'Données à jour',
      en: 'Data up to date',
      ar: 'البيانات محدّثة',
    ),
    'pending' => pick(
      fr: 'Données en attente de synchronisation',
      en: 'Data waiting to sync',
      ar: 'بيانات في انتظار المزامنة',
    ),
    'syncing' => pick(
      fr: 'Synchronisation en cours',
      en: 'Synchronizing',
      ar: 'جارٍ المزامنة',
    ),
    'offline' => pick(
      fr: 'Hors ligne · données conservées sur cet appareil',
      en: 'Offline · data kept on this device',
      ar: 'غير متصل · البيانات محفوظة على هذا الجهاز',
    ),
    _ => pick(
      fr: 'Échec de synchronisation · appuyer pour réessayer',
      en: 'Synchronization failed · tap to retry',
      ar: 'فشلت المزامنة · اضغط لإعادة المحاولة',
    ),
  };

  String greeting(int hour, String firstName) {
    final base = hour < 12
        ? pick(fr: 'Bonjour', en: 'Good morning', ar: 'صباح الخير')
        : hour < 18
        ? pick(fr: 'Bon après-midi', en: 'Good afternoon', ar: 'مساء الخير')
        : pick(fr: 'Bonsoir', en: 'Good evening', ar: 'مساء الخير');
    if (firstName.isEmpty) return isArabic ? '$base!' : '$base !';
    return isArabic ? '$base، $firstName' : '$base, $firstName.';
  }

  String observation(int range) => pick(
    fr: "Voici ce qu'IAmina a observé sur vos $range derniers jours.",
    en: 'Here is what IAmina observed over your last $range days.',
    ar: 'إليك ما لاحظته IAmina خلال آخر $range يومًا.',
  );
  String get emptyAnalysis => pick(
    fr: 'Chargez des données pour voir votre analyse IAmina.',
    en: 'Add data to view your IAmina analysis.',
    ar: 'أضف بيانات لعرض تحليل IAmina.',
  );
  String get latestReading =>
      pick(fr: 'DERNIÈRE MESURE', en: 'LATEST READING', ar: 'آخر قياس');
  String get justNow => pick(fr: "à l'instant", en: 'just now', ar: 'الآن');
  String minutesAgo(int value) => pick(
    fr: 'il y a $value min',
    en: '$value min ago',
    ar: 'منذ $value دقيقة',
  );
  String meal(String? value) {
    if (value == null || value.isEmpty) return '';
    final v = value.toLowerCase();
    if (v.contains('après') || v.contains('post'))
      return pick(fr: 'Après repas', en: 'After meal', ar: 'بعد الوجبة');
    if (v.contains('jeun'))
      return pick(fr: 'À jeun', en: 'Fasting', ar: 'صائم');
    return value;
  }

  String targetTitle(int range) => pick(
    fr: 'MESURES DANS LA CIBLE · $range JOURS',
    en: 'READINGS IN RANGE · $range DAYS',
    ar: 'القياسات ضمن النطاق · $range يومًا',
  );
  String targetCoverage(int count, int days) => pick(
    fr: '$count mesures sur $days jour${days > 1 ? 's' : ''} · proportion de mesures, pas durée CGM',
    en: '$count readings over $days day${days == 1 ? '' : 's'} · share of readings, not CGM duration',
    ar: '$count قياسًا خلال $days يومًا · نسبة قياسات وليست مدة قياس مستمر',
  );
  String get targetReference => pick(
    fr: 'Repère général ≥ 70 % · votre cible personnelle peut être différente.',
    en: 'General reference ≥ 70% · your personal target may differ.',
    ar: 'مرجع عام ≥ 70٪ · قد يختلف هدفك الشخصي.',
  );
  String get viewJournal =>
      pick(fr: 'Voir le journal', en: 'View journal', ar: 'عرض اليومية');
  String get readingsInRange => pick(
    fr: 'Mesures dans la cible',
    en: 'Readings in range',
    ar: 'القياسات ضمن النطاق',
  );
  String get rangeReference =>
      pick(fr: 'Repère 70–180', en: 'Reference 70–180', ar: 'مرجع 70–180');
  String get inRange =>
      pick(fr: 'Dans la cible', en: 'In range', ar: 'ضمن النطاق');
  String get high => pick(fr: 'Élevé', en: 'High', ar: 'مرتفع');
  String get low => pick(fr: 'Bas', en: 'Low', ar: 'منخفض');
  String get veryHigh =>
      pick(fr: 'Très élevé', en: 'Very high', ar: 'مرتفع جدًا');
  String get targetExplanation => pick(
    fr: 'Repère général : plus de 70 % des mesures dans 70–180 mg/dL. Votre cible personnelle peut être différente.',
    en: 'General reference: more than 70% of readings within 70–180 mg/dL. Your personal target may differ.',
    ar: 'مرجع عام: أكثر من 70٪ من القياسات بين 70 و180 mg/dL. قد يختلف هدفك الشخصي.',
  );

  String get importTitle => pick(fr: 'Importer', en: 'Import', ar: 'استيراد');
  String get importSubtitle => pick(
    fr: 'Connectez vos sources de données',
    en: 'Connect your data sources',
    ar: 'اربط مصادر بياناتك',
  );
  String get directConnections => pick(
    fr: 'Connexions directes',
    en: 'Direct connections',
    ar: 'اتصالات مباشرة',
  );
  String get pulperDescription => pick(
    fr: 'PDF · Photo · Excel · Word — IAmina extrait les données pour votre relecture.',
    en: 'PDF · Photo · Excel · Word — IAmina extracts data for your review.',
    ar: 'PDF · صورة · Excel · Word — تستخرج IAmina البيانات لمراجعتك.',
  );
  String get labReport =>
      pick(fr: 'Bilan labo', en: 'Lab report', ar: 'تحاليل مخبرية');
  String get cgmExport =>
      pick(fr: 'Export CGM', en: 'CGM export', ar: 'تصدير CGM');
  String get prescription =>
      pick(fr: 'Ordonnance', en: 'Prescription', ar: 'وصفة طبية');
  String get photo => pick(fr: 'Photo', en: 'Photo', ar: 'صورة');
  String get soon => pick(fr: 'BIENTÔT', en: 'SOON', ar: 'قريبًا');
  String get unavailable =>
      pick(fr: 'Non disponible', en: 'Unavailable', ar: 'غير متاح');
  String get dexcomDescription => pick(
    fr: 'Connexion Dexcom CLARITY prévue. Fréquence et disponibilité à confirmer avant activation.',
    en: 'Dexcom CLARITY connection planned. Frequency and availability must be confirmed before activation.',
    ar: 'ربط Dexcom CLARITY مخطط له. يجب تأكيد التواتر والتوفر قبل التفعيل.',
  );
  String get libreDescription => pick(
    fr: 'Import LibreView prévu. Formats et disponibilité à confirmer avant activation.',
    en: 'LibreView import planned. Formats and availability must be confirmed before activation.',
    ar: 'استيراد LibreView مخطط له. يجب تأكيد الصيغ والتوفر قبل التفعيل.',
  );
  String get openDocumentImport => pick(
    fr: "Ouvrir l'import de document",
    en: 'Open document import',
    ar: 'فتح استيراد المستند',
  );
  String get documentTitle => pick(
    fr: 'Importer un document',
    en: 'Import a document',
    ar: 'استيراد مستند',
  );
  String get documentIntro => pick(
    fr: "Importez un document médical. IAmina extrait les données, puis vous devez les relire et les confirmer.",
    en: 'Import a medical document. IAmina extracts the data, then you must review and confirm it.',
    ar: 'استورد مستندًا طبيًا. تستخرج IAmina البيانات ثم يجب عليك مراجعتها وتأكيدها.',
  );
  String get chooseDocument => pick(
    fr: 'Choisir un document',
    en: 'Choose a document',
    ar: 'اختيار مستند',
  );
  String get profileComplete =>
      pick(fr: 'Profil complet', en: 'Profile complete', ar: 'الملف مكتمل');

  String profileCompletionLabel(int percentage) => percentage >= 100
      ? pick(
          fr: 'Profil complet ✓',
          en: 'Profile complete ✓',
          ar: 'الملف مكتمل ✓',
        )
      : pick(
          fr: 'Profil complété à $percentage%',
          en: 'Profile $percentage% complete',
          ar: 'اكتمل الملف بنسبة $percentage٪',
        );

  String get profileCompletionPrompt => pick(
    fr: 'Complétez votre profil pour des analyses plus précises.',
    en: 'Complete your profile for more precise analyses.',
    ar: 'أكمل ملفك للحصول على تحليلات أدق.',
  );

  String get minimum => pick(fr: 'Min', en: 'Min', ar: 'الحد الأدنى');
  String get maximum => pick(fr: 'Max', en: 'Max', ar: 'الحد الأقصى');
}
