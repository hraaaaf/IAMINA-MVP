import 'package:amina/l10n/app_localizations.dart';

extension DashboardInsightLocalizedCopy on AppLocalizations {
  String get _insightLanguageCode => localeName.split(RegExp('[-_]')).first;

  String _insightPick({required String en, required String fr, required String ar}) {
    return switch (_insightLanguageCode) {
      'ar' => ar,
      'fr' => fr,
      _ => en,
    };
  }

  String get dashboardInsightHeading =>
      _insightPick(en: 'Automatic IAmina insight', fr: 'Analyse IAmina automatique', ar: 'تحليل IAmina التلقائي');

  String get dashboardInsightEyebrow => _insightPick(
        en: 'GOVERNED SIGNAL',
        fr: 'SIGNAL GOUVERNÉ',
        ar: 'إشارة موثوقة',
      );

  String get dashboardInsightSubheading => _insightPick(
        en: 'IAmina looks for useful trends in your recorded readings. This is separate from the chat.',
        fr: 'IAmina recherche des tendances utiles dans vos mesures enregistrées. Cette analyse est distincte du chat.',
        ar: 'تبحث IAmina عن اتجاهات مفيدة في قياساتك المسجلة. هذا التحليل منفصل عن الدردشة.',
      );

  String get dashboardInsightLoading => _insightPick(
        en: 'Looking for a useful trend…',
        fr: 'Recherche d’une tendance utile…',
        ar: 'جارٍ البحث عن اتجاه مفيد…',
      );

  String get dashboardInsightUnavailable => _insightPick(
        en: 'The automatic analysis is unavailable right now. IAmina will not invent an interpretation.',
        fr: 'L’analyse automatique est indisponible pour le moment. IAmina n’invente aucune interprétation.',
        ar: 'التحليل التلقائي غير متاح حالياً. لن تختلق IAmina أي تفسير.',
      );

  String get dashboardInsightRetry =>
      _insightPick(en: 'Retry', fr: 'Réessayer', ar: 'إعادة المحاولة');

  String get dashboardInsightInsufficient => _insightPick(
        en: 'Not enough readings yet to show a useful trend. Keep recording normally; IAmina will show one only when the data is sufficient.',
        fr: 'Pas encore assez de mesures pour afficher une tendance utile. Continuez simplement à enregistrer vos mesures ; IAmina en affichera une seulement quand les données seront suffisantes.',
        ar: 'لا توجد قياسات كافية بعد لإظهار اتجاه مفيد. واصل تسجيل قياساتك بشكل طبيعي؛ ستعرض IAmina اتجاهاً فقط عندما تصبح البيانات كافية.',
      );

  String get dashboardInsightCooldown => _insightPick(
        en: 'IAmina deliberately limits non-urgent signals. Nothing new is highlighted right now.',
        fr: 'IAmina limite volontairement les signaux non urgents. Rien de nouveau n’est mis en avant pour le moment.',
        ar: 'تحد IAmina عمداً من الإشارات غير العاجلة. لا توجد إشارة جديدة بارزة حالياً.',
      );

  String get dashboardInsightNoChange => _insightPick(
        en: 'No material governed change is waiting to be highlighted.',
        fr: 'Aucun changement gouverné matériel n’attend d’être mis en avant.',
        ar: 'لا يوجد تغير موثوق جوهري بانتظار عرضه.',
      );

  String dashboardInsightObservationLabel(String key) => switch (key) {
        'context:stress' => _insightPick(en: 'Stress', fr: 'Stress', ar: 'التوتر'),
        'context:activity' =>
          _insightPick(en: 'Activity', fr: 'Activité', ar: 'النشاط'),
        'context:illness' => _insightPick(
            en: 'Recorded illness',
            fr: 'Maladie déclarée',
            ar: 'مرض مسجل',
          ),
        'context:poor_sleep' => _insightPick(
            en: 'Poor sleep',
            fr: 'Sommeil difficile',
            ar: 'نوم غير جيد',
          ),
        'context:fatigue' =>
          _insightPick(en: 'Fatigue', fr: 'Fatigue', ar: 'التعب'),
        'meal:breakfast' => _insightPick(
            en: 'Breakfast',
            fr: 'Petit-déjeuner',
            ar: 'الفطور',
          ),
        'meal:lunch' =>
          _insightPick(en: 'Lunch', fr: 'Déjeuner', ar: 'الغداء'),
        'meal:dinner' =>
          _insightPick(en: 'Dinner', fr: 'Dîner', ar: 'العشاء'),
        'meal:snack' => _insightPick(
            en: 'Snack',
            fr: 'Collation',
            ar: 'وجبة خفيفة',
          ),
        'meal:suhoor' =>
          _insightPick(en: 'Suhoor', fr: 'Suhoor', ar: 'السحور'),
        'meal:iftar' =>
          _insightPick(en: 'Iftar', fr: 'Iftar', ar: 'الإفطار'),
        _ => _insightPick(
            en: 'Personal signal',
            fr: 'Signal personnel',
            ar: 'إشارة شخصية',
          ),
      };

  String dashboardInsightChangeLabel(String value) => switch (value) {
        'first_eligible_observation' => _insightPick(
            en: 'A first repeatable observation is now eligible for review.',
            fr: 'Une première observation répétable est maintenant éligible à la revue.',
            ar: 'أصبحت أول ملاحظة قابلة للتكرار مؤهلة للمراجعة.',
          ),
        'new_supporting_evidence' => _insightPick(
            en: 'New supporting evidence changed this observation.',
            fr: 'De nouvelles preuves ont fait évoluer cette observation.',
            ar: 'أدلة داعمة جديدة غيّرت هذه الملاحظة.',
          ),
        'repeated_eligible_evidence' => _insightPick(
            en: 'Eligible evidence has repeated across the governed history.',
            fr: 'Les preuves éligibles se répètent dans l’historique gouverné.',
            ar: 'تكررت الأدلة المؤهلة ضمن السجل الموثوق.',
          ),
        'association_moved_toward_personal_baseline' => _insightPick(
            en: 'The descriptive association moved toward your personal baseline.',
            fr: 'L’association descriptive s’est rapprochée de votre référence personnelle.',
            ar: 'اقترب الارتباط الوصفي من مرجعك الشخصي.',
          ),
        'observation_no_longer_meets_repeatability_rule' => _insightPick(
            en: 'This observation no longer meets the governed repeatability rule.',
            fr: 'Cette observation ne remplit plus la règle gouvernée de répétabilité.',
            ar: 'لم تعد هذه الملاحظة تستوفي قاعدة التكرار الموثوقة.',
          ),
        _ => _insightPick(
            en: 'A governed material change is available for review.',
            fr: 'Un changement gouverné matériel est disponible à la revue.',
            ar: 'يتوفر تغير موثوق جوهري للمراجعة.',
          ),
      };

  String get dashboardInsightEvidenceTitle =>
      _insightPick(en: 'Evidence', fr: 'Preuve', ar: 'الدليل');

  String dashboardInsightObservationCount(int value) => _insightPick(
        en: '$value observations',
        fr: '$value observations',
        ar: '$value ملاحظات',
      );

  String dashboardInsightDayCount(int value) => _insightPick(
        en: '$value days',
        fr: '$value jours',
        ar: '$value أيام',
      );

  String dashboardInsightWindow(int value) => _insightPick(
        en: '$value-day window',
        fr: 'Fenêtre $value j',
        ar: 'نافذة $value يوماً',
      );

  String dashboardInsightEvidenceStrength(String value) => switch (value) {
        'strong' => _insightPick(en: 'Strong', fr: 'Forte', ar: 'قوية'),
        'moderate' => _insightPick(en: 'Moderate', fr: 'Modérée', ar: 'متوسطة'),
        _ => _insightPick(en: 'Limited', fr: 'Limitée', ar: 'محدودة'),
      };

  String get dashboardInsightAllowedAction => _insightPick(
        en: 'Allowed next step',
        fr: 'Étape suivante autorisée',
        ar: 'الخطوة التالية المسموح بها',
      );

  String dashboardInsightAction(String value) => switch (value) {
        'PREPARE_CLINICIAN_DISCUSSION' => _insightPick(
            en: 'Prepare a discussion with your clinician',
            fr: 'Préparer une discussion avec votre professionnel de santé',
            ar: 'الاستعداد لمناقشة الأمر مع طبيبك',
          ),
        _ => _insightPick(
            en: 'Continue observing',
            fr: 'Continuer à observer',
            ar: 'مواصلة المراقبة',
          ),
      };

  String get dashboardInsightLimitation => _insightPick(
        en: 'Descriptive association only. It does not establish a cause, diagnosis, or treatment effect.',
        fr: 'Association descriptive uniquement. Elle n’établit ni cause, ni diagnostic, ni effet du traitement.',
        ar: 'ارتباط وصفي فقط. لا يثبت سبباً أو تشخيصاً أو تأثيراً للعلاج.',
      );

  String get dashboardInsightDemoEyebrow => _insightPick(
        en: 'DEMO · FACTUAL LOCAL SUMMARY',
        fr: 'DÉMO · RÉSUMÉ LOCAL FACTUEL',
        ar: 'عرض · ملخص محلي وصفي',
      );

  String dashboardInsightDemoSummary(
    int readings,
    int days,
    int averageMgDl,
  ) => _insightPick(
        en: '$readings recorded readings across $days days · average $averageMgDl mg/dL.',
        fr: '$readings mesures enregistrées sur $days jours · moyenne $averageMgDl mg/dL.',
        ar: '$readings قراءة مسجلة على مدى $days أيام · متوسط $averageMgDl mg/dL.',
      );

  String get dashboardInsightDemoEmpty => _insightPick(
        en: 'Add a first reading to unlock a factual local summary.',
        fr: 'Ajoutez une première mesure pour afficher un résumé local factuel.',
        ar: 'أضف أول قراءة لعرض ملخص محلي وصفي.',
      );

  String get dashboardInsightDemoLimitation => _insightPick(
        en: 'Demo only: descriptive local statistics. No diagnosis, cause, treatment effect, or patient-record access is inferred.',
        fr: 'Démo uniquement : statistiques locales descriptives. Aucun diagnostic, cause, effet du traitement ou accès à un dossier patient n’est déduit.',
        ar: 'للعرض فقط: إحصاءات محلية وصفية. لا يتم استنتاج تشخيص أو سبب أو تأثير للعلاج أو الوصول إلى ملف المريض.',
      );

  String get dashboardInsightSeeEvidence => _insightPick(
        en: 'See the evidence in Companion',
        fr: 'Voir les preuves dans Compagnon',
        ar: 'عرض الأدلة في الرفيق',
      );
}
