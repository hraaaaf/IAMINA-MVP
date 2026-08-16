import 'package:amina/l10n/app_localizations.dart';

extension DashboardKpiLocalizedCopy on AppLocalizations {
  String get _kpiLanguageCode => localeName.split(RegExp('[-_]')).first;

  String _kpiPick({required String en, required String fr, required String ar}) {
    return switch (_kpiLanguageCode) {
      'ar' => ar,
      'fr' => fr,
      _ => en,
    };
  }

  String get dashboardKpiHeading => _kpiPick(
        en: 'Your indicators',
        fr: 'Vos indicateurs',
        ar: 'مؤشراتك',
      );

  String get dashboardKpiRecordedMode => _kpiPick(
        en: 'Recorded-measurement mode',
        fr: 'Mode mesures enregistrées',
        ar: 'وضع القياسات المسجلة',
      );

  String get dashboardKpiRecordedModeNote => _kpiPick(
        en: 'These indicators describe only the measurements actually recorded. They do not estimate missing time.',
        fr: 'Ces indicateurs décrivent uniquement les mesures réellement enregistrées. Ils n’estiment pas le temps manquant.',
        ar: 'تصف هذه المؤشرات القياسات المسجلة فعلياً فقط، ولا تقدّر الفترات التي لا تتوفر فيها بيانات.',
      );

  String get dashboardKpiAdvancedCgmLocked => _kpiPick(
        en: 'Advanced CGM metrics stay hidden until sensor coverage is proven by an eligible governed data source.',
        fr: 'Les métriques CGM avancées restent masquées tant que la couverture capteur n’est pas prouvée par une source gouvernée éligible.',
        ar: 'تبقى مؤشرات المراقبة المستمرة المتقدمة مخفية إلى أن يتم إثبات تغطية المستشعر من مصدر بيانات موثوق ومؤهل.',
      );

  String get dashboardKpiCgmMarkedUnverified => _kpiPick(
        en: 'CGM-labelled measurements are present, but active sensor coverage cannot be proven from the current local record.',
        fr: 'Des mesures marquées CGM sont présentes, mais la couverture active du capteur ne peut pas être prouvée avec le registre local actuel.',
        ar: 'توجد قياسات موسومة كمراقبة مستمرة، لكن لا يمكن إثبات تغطية المستشعر النشطة من السجل المحلي الحالي.',
      );

  String get dashboardKpiRecordedCount => _kpiPick(
        en: 'Recorded',
        fr: 'Enregistrées',
        ar: 'المسجلة',
      );

  String get dashboardKpiDaysWithData => _kpiPick(
        en: 'Days with data',
        fr: 'Jours renseignés',
        ar: 'أيام ببيانات',
      );

  String get dashboardKpiRecordedAverage => _kpiPick(
        en: 'Recorded average',
        fr: 'Moyenne enregistrée',
        ar: 'متوسط القياسات المسجلة',
      );

  String get dashboardKpiReadingsInTarget => _kpiPick(
        en: 'Readings in target',
        fr: 'Mesures dans la cible',
        ar: 'القياسات ضمن النطاق',
      );

  String get dashboardKpiNotTimeInRange => _kpiPick(
        en: 'Count of recorded readings, not time in range.',
        fr: 'Compte des mesures enregistrées, pas du temps dans la cible.',
        ar: 'هذا عدد القياسات المسجلة، وليس الوقت ضمن النطاق.',
      );

  String get dashboardKpiTargetMissing => _kpiPick(
        en: 'Personal target not configured',
        fr: 'Cible personnelle non configurée',
        ar: 'النطاق الشخصي غير مضبوط',
      );

  String get dashboardKpiEmpty => _kpiPick(
        en: 'No recorded measurement in the last 7 days.',
        fr: 'Aucune mesure enregistrée sur les 7 derniers jours.',
        ar: 'لا يوجد قياس مسجل خلال الأيام السبعة الأخيرة.',
      );

  String get dashboardKpiUnavailable => _kpiPick(
        en: 'Indicators are unavailable from local data right now.',
        fr: 'Les indicateurs locaux sont indisponibles pour le moment.',
        ar: 'المؤشرات المحلية غير متاحة حالياً.',
      );

  String get dashboardKpiPeriod7Days => _kpiPick(
        en: 'Last 7 days',
        fr: '7 derniers jours',
        ar: 'آخر 7 أيام',
      );
}
