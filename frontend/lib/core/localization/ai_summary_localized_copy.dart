import 'package:amina/l10n/app_localizations.dart';

extension AiSummaryLocalizedCopy on AppLocalizations {
  String get _languageCode => localeName.split(RegExp('[-_]')).first;

  String _pick({required String en, required String fr, required String ar}) {
    return switch (_languageCode) {
      'ar' => ar,
      'fr' => fr,
      _ => en,
    };
  }

  String get keyEvents => _pick(en: 'KEY EVENTS', fr: 'ÉVÉNEMENTS CLÉS', ar: 'الأحداث الرئيسية');
  String priorities(int count) => _pick(en: '$count ${count == 1 ? 'priority' : 'priorities'}', fr: '$count priorité${count > 1 ? 's' : ''}', ar: '$count أولوية');
  String get noDiscoveryYet => _pick(en: 'No findings yet.', fr: 'Aucune découverte pour le moment.', ar: 'لا توجد ملاحظات بعد.');
  String get mostlyInTarget => _pick(en: 'Most available readings\nare within the 70–180 mg/dL reference range.', fr: 'Une majorité des mesures disponibles\nse situe dans le repère 70–180 mg/dL.', ar: 'تقع غالبية القراءات المتاحة\nضمن النطاق المرجعي 70–180 mg/dL.');
  String get someReadingsNeedReview => _pick(en: 'Some available readings\nmay be worth reviewing.', fr: 'Certaines mesures disponibles\nméritent d’être examinées.', ar: 'قد تستحق بعض القراءات المتاحة\nالمراجعة.');
  String heroObservationSummary(int observations, int discussionPoints, int readings) => _pick(
        en: '$observations priority observations, $discussionPoints points to discuss. Based on $readings available readings.',
        fr: '$observations observations prioritaires, $discussionPoints pistes à discuter. Basé sur $readings mesures disponibles.',
        ar: '$observations ملاحظات ذات أولوية، و$discussionPoints نقاط للنقاش. استنادًا إلى $readings قراءة متاحة.',
      );
  String get seeFindings => _pick(en: 'See my findings', fr: 'Voir mes découvertes', ar: 'عرض ملاحظاتي');
  String get discussWithIamina => _pick(en: 'Talk with IAmina', fr: 'Discuter avec IAmina', ar: 'التحدث مع IAmina');
  String get readingsInRange => _pick(en: 'READINGS IN RANGE', fr: 'MESURES DANS LA CIBLE', ar: 'القراءات ضمن النطاق');
  String get generalRangeReference => _pick(en: 'General reference 70–180 mg/dL', fr: 'Repère général 70–180 mg/dL', ar: 'مرجع عام 70–180 mg/dL');
  String get estimatedGmi => _pick(en: 'ESTIMATED GMI', fr: 'GMI ESTIMÉE', ar: 'GMI تقديري');
  String gmiBasis(String basis) => _pick(en: '$basis · estimate, not a laboratory HbA1c', fr: '$basis · estimation, pas HbA1c laboratoire', ar: '$basis · تقدير وليس HbA1c مخبريًا');
  String get gmiAvailableMean => _pick(en: 'Available mean · estimate, not a laboratory HbA1c', fr: 'Moyenne disponible · estimation, pas HbA1c laboratoire', ar: 'المتوسط المتاح · تقدير وليس HbA1c مخبريًا');
  String get variabilityCv => _pick(en: 'VARIABILITY (CV)', fr: 'VARIABILITÉ (CV)', ar: 'التباين (CV)');
  String get generalCvReference => _pick(en: 'General reference <36%', fr: 'Repère général <36 %', ar: 'مرجع عام <36٪');
  String coverage(int readings, int days) => _pick(en: '$readings readings across $days ${days == 1 ? 'day' : 'days'}', fr: '$readings mesures sur $days jour${days > 1 ? 's' : ''}', ar: '$readings قراءة خلال $days يوم');
  String coverageDisclosure(String coverage) => _pick(en: 'General, non-personalized references · $coverage. Missing data may change interpretation.', fr: 'Repères généraux non personnalisés · $coverage. Les données manquantes peuvent modifier l’interprétation.', ar: 'مراجع عامة غير مخصصة · $coverage. قد تغيّر البيانات الناقصة التفسير.');
  String get ambulatoryGlucoseProfile => _pick(en: 'AMBULATORY GLUCOSE PROFILE', fr: 'PROFIL GLYCÉMIQUE AMBULATOIRE', ar: 'ملف الغلوكوز المتنقل');
  String periodDays(int days) => _pick(en: '${days}d', fr: '${days}j', ar: '$days يوم');
  String get inTarget => _pick(en: 'In range', fr: 'En cible', ar: 'ضمن النطاق');
  String get elevated => _pick(en: 'High', fr: 'Élevé', ar: 'مرتفع');
  String get lowLabel => _pick(en: 'Low', fr: 'Bas', ar: 'منخفض');
  String get adaReference => _pick(en: 'ADA reference >70%', fr: 'Repère ADA > 70%', ar: 'مرجع ADA >70٪');
  String get insufficientData => _pick(en: 'Insufficient data.', fr: 'Données insuffisantes.', ar: 'البيانات غير كافية.');
  String get median => _pick(en: 'Median', fr: 'Médiane', ar: 'الوسيط');
  String get generalRangeShort => _pick(en: 'General reference 70–180', fr: 'Repère général 70–180', ar: 'مرجع عام 70–180');
  String get discussionPoints => _pick(en: 'POINTS TO DISCUSS', fr: 'POINTS À DISCUTER', ar: 'نقاط للنقاش');
  String discussionCount(int count) => _pick(en: '$count ${count == 1 ? 'point' : 'points'} to review over 7 days', fr: '$count point${count > 1 ? 's' : ''} à examiner sur 7 jours', ar: '$count نقطة للمراجعة خلال 7 أيام');
  String get discussWithDoctor => _pick(en: 'Discuss with your doctor', fr: 'À discuter avec le médecin', ar: 'للنقاش مع الطبيب');
  String get documentCarbMeals => _pick(en: 'Document carbohydrate-containing meals', fr: 'Documenter les repas glucidiques', ar: 'توثيق الوجبات المحتوية على الكربوهيدرات');
  String get addMealContextTiming => _pick(en: 'Add meal context and timing', fr: 'Ajouter le contexte et les horaires du repas', ar: 'أضف سياق الوجبة وتوقيتها');
  String get documentNightValues => _pick(en: 'Document nighttime readings', fr: 'Documenter les valeurs nocturnes', ar: 'توثيق القراءات الليلية');
  String get noteActivitySleepSymptoms => _pick(en: 'Note associated activity, sleep and symptoms', fr: 'Noter activité, sommeil et symptômes associés', ar: 'دوّن النشاط والنوم والأعراض المصاحبة');
  String get prepareTirReview => _pick(en: 'Prepare the TIR review', fr: 'Préparer le bilan TIR', ar: 'تحضير مراجعة TIR');
  String get compareWithProfessional => _pick(en: 'Compare periods with your healthcare professional', fr: 'Comparer les périodes avec votre professionnel', ar: 'قارن الفترات مع مقدم الرعاية الصحية');
  String get positive => _pick(en: 'Positive', fr: 'Positif', ar: 'إيجابي');
  String get watch => _pick(en: 'Review', fr: 'À surveiller', ar: 'للمراجعة');
  String get highPriority => _pick(en: 'High priority', fr: 'Priorité haute', ar: 'أولوية عالية');
  String get automaticObservation => _pick(en: 'Automatic observation', fr: 'Observation automatique', ar: 'ملاحظة تلقائية');
  String discussionSuggestion(String action) => _pick(en: 'Point to discuss: $action', fr: 'Piste à discuter : $action', ar: 'نقطة للنقاش: $action');
  String get askWhy => _pick(en: 'Ask why', fr: 'Demander pourquoi', ar: 'اسأل لماذا');
  String get chatCtaBody => _pick(en: 'Ask questions or request an explanation of the available data.', fr: 'Posez vos questions ou demandez une explication des données disponibles.', ar: 'اطرح أسئلتك أو اطلب شرحًا للبيانات المتاحة.');
  String get start => _pick(en: 'Start', fr: 'Démarrer', ar: 'ابدأ');
}
