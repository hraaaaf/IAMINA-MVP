import 'package:amina/l10n/app_localizations.dart';

extension DashboardLocalizedCopy on AppLocalizations {
  String get _languageCode => localeName.split(RegExp('[-_]')).first;

  String _pick({required String en, required String fr, required String ar}) {
    return switch (_languageCode) {
      'ar' => ar,
      'fr' => fr,
      _ => en,
    };
  }

  String dashboardChatContext({required String value, String? meal}) {
    final mealPart = meal == null || meal.trim().isEmpty ? '' : ' — ${meal.trim()}';
    return _pick(
      en: 'My latest reading is $value$mealPart. Can you help me understand my current situation?',
      fr: 'Ma dernière mesure est $value$mealPart. Peux-tu m’aider à comprendre ma situation actuelle ?',
      ar: 'آخر قراءة لدي هي $value$mealPart. هل يمكنك مساعدتي على فهم وضعي الحالي؟',
    );
  }

  String get dashboardLatestKnownReading => _pick(
        en: 'Latest known reading',
        fr: 'Dernière mesure connue',
        ar: 'آخر قياس معروف',
      );

  String get dashboardTargetNotConfigured => _pick(
        en: 'Target not configured',
        fr: 'Cible non configurée',
        ar: 'النطاق المستهدف غير مضبوط',
      );

  String get dashboardTodayHeading => _pick(
        en: 'Today at a glance',
        fr: 'À retenir aujourd’hui',
        ar: 'ملخص اليوم',
      );

  String get dashboardTodayLoading => _pick(
        en: 'Updating your governed summary…',
        fr: 'Mise à jour de votre synthèse gouvernée…',
        ar: 'جارٍ تحديث ملخصك الموثوق…',
      );

  String get dashboardTodayUnavailable => _pick(
        en: 'Governed summary is unavailable right now. Your local data remains available.',
        fr: 'La synthèse gouvernée est indisponible pour le moment. Vos données locales restent disponibles.',
        ar: 'الملخص الموثوق غير متاح حالياً. تبقى بياناتك المحلية متاحة.',
      );

  String get dashboardRetry => _pick(
        en: 'Retry',
        fr: 'Réessayer',
        ar: 'إعادة المحاولة',
      );

  String get dashboardConfigureTargetSignal => _pick(
        en: 'Configure your personal target before IAmina labels a reading against it.',
        fr: 'Configurez votre cible personnelle avant qu’IAmina ne qualifie une mesure par rapport à celle-ci.',
        ar: 'اضبط نطاقك الشخصي قبل أن تصف IAmina أي قياس مقارنةً به.',
      );

  String get dashboardConfigureTargetAction => _pick(
        en: 'Configure',
        fr: 'Configurer',
        ar: 'ضبط',
      );

  String dashboardGovernedChanges(int count) => _pick(
        en: '$count governed change${count == 1 ? '' : 's'} available since your last review.',
        fr: '$count changement${count == 1 ? '' : 's'} gouverné${count == 1 ? '' : 's'} disponible${count == 1 ? '' : 's'} depuis votre dernière revue.',
        ar: 'يتوفر $count تغير موثوق منذ آخر مراجعة لك.',
      );

  String dashboardGovernedPatterns(int count) => _pick(
        en: '$count governed personal pattern${count == 1 ? '' : 's'} available to review.',
        fr: '$count schéma${count == 1 ? '' : 's'} personnel${count == 1 ? '' : 's'} gouverné${count == 1 ? '' : 's'} disponible${count == 1 ? '' : 's'} à consulter.',
        ar: 'يتوفر $count نمط شخصي موثوق للمراجعة.',
      );

  String get dashboardNoGovernedHighlight => _pick(
        en: 'No new governed summary to highlight from the available data.',
        fr: 'Aucun nouveau résumé gouverné à mettre en avant avec les données disponibles.',
        ar: 'لا يوجد ملخص موثوق جديد لإبرازه من البيانات المتاحة.',
      );

  String get dashboardOpenCompanion => _pick(
        en: 'Companion',
        fr: 'Compagnon',
        ar: 'الرفيق',
      );

  String get dashboardImportData => _pick(
        en: 'Import',
        fr: 'Importer',
        ar: 'استيراد',
      );

  String get dashboardGovernedTrustShort => _pick(
        en: 'This summary uses governed observations only · missing data is never invented.',
        fr: 'Cette synthèse utilise uniquement des observations gouvernées · les données manquantes ne sont jamais inventées.',
        ar: 'يستخدم هذا الملخص ملاحظات موثوقة فقط · لا يتم اختراع البيانات المفقودة.',
      );

  String get dashboardFreshNow => _pick(
        en: 'just now',
        fr: 'à l’instant',
        ar: 'الآن',
      );

  String get dashboardTimestampNeedsReview => _pick(
        en: 'timestamp to check',
        fr: 'horodatage à vérifier',
        ar: 'تحقق من وقت القياس',
      );

  String dashboardFreshMinutes(int minutes) => _pick(
        en: '$minutes min ago',
        fr: 'il y a $minutes min',
        ar: 'منذ $minutes د',
      );

  String dashboardFreshHours(int hours) => _pick(
        en: '$hours h ago',
        fr: 'il y a $hours h',
        ar: 'منذ $hours س',
      );

  String dashboardFreshDays(int days) => _pick(
        en: '$days d ago',
        fr: 'il y a $days j',
        ar: 'منذ $days ي',
      );

  String dashboardTodayAt(String time) => _pick(
        en: 'Today · $time',
        fr: 'Aujourd’hui · $time',
        ar: 'اليوم · $time',
      );

  String dashboardYesterdayAt(String time) => _pick(
        en: 'Yesterday · $time',
        fr: 'Hier · $time',
        ar: 'أمس · $time',
      );

  String get debugNoPatientData => _pick(
        en: 'Dev mode — no patient data.',
        fr: 'Mode dev — aucune donnée patient.',
        ar: 'وضع التطوير — لا توجد بيانات للمريض.',
      );

  String get loadDemo => _pick(
        en: 'Load demo',
        fr: 'Charger démo',
        ar: 'تحميل البيانات التجريبية',
      );
}
