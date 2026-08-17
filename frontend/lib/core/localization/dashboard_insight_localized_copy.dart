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
      _insightPick(en: 'IAmina insight', fr: 'Insight IAmina', ar: 'إشارة IAmina');

  String get dashboardInsightEyebrow => _insightPick(
        en: 'GOVERNED SIGNAL',
        fr: 'SIGNAL GOUVERNÉ',
        ar: 'إشارة موثوقة',
      );

  String get dashboardInsightSubheading => _insightPick(
        en: 'One evidence-qualified signal at a time, without inventing a cause.',
        fr: 'Un signal qualifié par les preuves à la fois, sans inventer de cause.',
        ar: 'إشارة واحدة مؤهلة بالأدلة في كل مرة، دون اختراع سبب.',
      );

  String get dashboardInsightLoading => _insightPick(
        en: 'Reading the governed signal…',
        fr: 'Lecture du signal gouverné…',
        ar: 'جارٍ قراءة الإشارة الموثوقة…',
      );

  String get dashboardInsightUnavailable => _insightPick(
        en: 'The governed insight is unavailable right now. No interpretation is invented.',
        fr: 'L’insight gouverné est indisponible pour le moment. Aucune interprétation n’est inventée.',
        ar: 'الإشارة الموثوقة غير متاحة حالياً. لا يتم اختراع أي تفسير.',
      );

  String get dashboardInsightRetry =>
      _insightPick(en: 'Retry', fr: 'Réessayer', ar: 'إعادة المحاولة');

  String get dashboardInsightInsufficient => _insightPick(
        en: 'Not enough governed longitudinal state yet to show a qualified insight.',
        fr: 'Pas encore assez d’état longitudinal gouverné pour afficher un insight qualifié.',
        ar: 'لا تتوفر بعد حالة طولية موثوقة كافية لعرض إشارة مؤهلة.',
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

  String get dashboardInsightSeeEvidence => _insightPick(
        en: 'See the evidence in Companion',
        fr: 'Voir les preuves dans Compagnon',
        ar: 'عرض الأدلة في الرفيق',
      );
}
