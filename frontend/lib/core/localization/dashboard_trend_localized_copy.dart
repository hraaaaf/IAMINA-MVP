import 'package:amina/l10n/app_localizations.dart';

extension DashboardTrendLocalizedCopy on AppLocalizations {
  String get _trendLanguageCode => localeName.split(RegExp('[-_]')).first;

  String _trendPick({required String en, required String fr, required String ar}) {
    return switch (_trendLanguageCode) {
      'ar' => ar,
      'fr' => fr,
      _ => en,
    };
  }

  String get dashboardTrendHeading => _trendPick(
        en: 'Trend',
        fr: 'Tendance',
        ar: 'الاتجاه',
      );

  String get dashboardTrendSubheading => _trendPick(
        en: 'Recorded measurements · no invented continuity',
        fr: 'Mesures enregistrées · aucun continu inventé',
        ar: 'قياسات مسجلة · دون استمرارية مختلقة',
      );

  String dashboardTrendRangeHours(int hours) => _trendPick(
        en: '${hours}h',
        fr: '${hours}h',
        ar: '$hours س',
      );

  String dashboardTrendRangeDays(int days) => _trendPick(
        en: '${days}d',
        fr: '${days}j',
        ar: '$days ي',
      );

  String get dashboardTrendLoading => _trendPick(
        en: 'Loading recorded measurements…',
        fr: 'Chargement des mesures enregistrées…',
        ar: 'جارٍ تحميل القياسات المسجلة…',
      );

  String get dashboardTrendUnavailable => _trendPick(
        en: 'Trend is unavailable from local data right now.',
        fr: 'La tendance locale est indisponible pour le moment.',
        ar: 'الاتجاه المحلي غير متاح حالياً.',
      );

  String get dashboardTrendEmpty => _trendPick(
        en: 'No recorded measurement in this period.',
        fr: 'Aucune mesure enregistrée sur cette période.',
        ar: 'لا يوجد قياس مسجل خلال هذه الفترة.',
      );

  String dashboardTrendPointCount(int count) => _trendPick(
        en: '$count recorded measurement${count == 1 ? '' : 's'}',
        fr: '$count mesure${count == 1 ? '' : 's'} enregistrée${count == 1 ? '' : 's'}',
        ar: '$count قياس مسجل',
      );

  String get dashboardTrendTargetBand => _trendPick(
        en: 'Personal target',
        fr: 'Cible personnelle',
        ar: 'النطاق الشخصي',
      );

  String get dashboardTrendTargetMissing => _trendPick(
        en: 'Target not configured',
        fr: 'Cible non configurée',
        ar: 'النطاق المستهدف غير مضبوط',
      );

  String get dashboardTrendNoInterpolation => _trendPick(
        en: 'Each point is a recorded measurement. Empty spaces remain missing data.',
        fr: 'Chaque point est une mesure enregistrée. Les espaces vides restent des données manquantes.',
        ar: 'كل نقطة تمثل قياساً مسجلاً. تبقى المساحات الفارغة بيانات مفقودة.',
      );

  String get dashboardTrendNoContext => _trendPick(
        en: 'No context was recorded with this measurement.',
        fr: 'Aucun contexte n’a été enregistré avec cette mesure.',
        ar: 'لم يتم تسجيل سياق مع هذا القياس.',
      );

  String dashboardTrendMedicationEvents(int count) => _trendPick(
        en: '$count treatment event${count == 1 ? '' : 's'} recorded in this period',
        fr: '$count événement${count == 1 ? '' : 's'} de traitement enregistré${count == 1 ? '' : 's'} sur cette période',
        ar: '$count حدث علاجي مسجل خلال هذه الفترة',
      );

  String dashboardTrendSourceLabel(String source) {
    final normalized = source.trim().toLowerCase();
    if (normalized == 'manual') {
      return _trendPick(en: 'Manual', fr: 'Manuel', ar: 'يدوي');
    }
    if (normalized.contains('cgm')) {
      return 'CGM';
    }
    if (normalized.contains('import')) {
      return _trendPick(en: 'Imported', fr: 'Importé', ar: 'مستورد');
    }
    return _trendPick(en: 'Recorded', fr: 'Enregistré', ar: 'مسجل');
  }

  String? dashboardTrendContextLabel(String key) {
    return switch (key) {
      'fasting' => _trendPick(en: 'Fasting', fr: 'À jeun', ar: 'صائم'),
      'pre_meal' => _trendPick(en: 'Before meal', fr: 'Avant repas', ar: 'قبل الوجبة'),
      'post_meal' => _trendPick(en: 'After meal', fr: 'Après repas', ar: 'بعد الوجبة'),
      'bedtime' => _trendPick(en: 'Bedtime', fr: 'Coucher', ar: 'وقت النوم'),
      'breakfast' => _trendPick(en: 'Breakfast', fr: 'Petit-déjeuner', ar: 'الفطور'),
      'lunch' => _trendPick(en: 'Lunch', fr: 'Déjeuner', ar: 'الغداء'),
      'dinner' => _trendPick(en: 'Dinner', fr: 'Dîner', ar: 'العشاء'),
      'snack' => _trendPick(en: 'Snack', fr: 'Collation', ar: 'وجبة خفيفة'),
      'suhoor' => _trendPick(en: 'Suhoor', fr: 'Suhoor', ar: 'السحور'),
      'iftar' => _trendPick(en: 'Iftar', fr: 'Iftar', ar: 'الإفطار'),
      'stress' => _trendPick(en: 'Stress recorded', fr: 'Stress enregistré', ar: 'توتر مسجل'),
      'activity' => _trendPick(en: 'Activity recorded', fr: 'Activité enregistrée', ar: 'نشاط مسجل'),
      'illness' => _trendPick(en: 'Illness recorded', fr: 'Maladie enregistrée', ar: 'مرض مسجل'),
      'fatigue' => _trendPick(en: 'Fatigue recorded', fr: 'Fatigue enregistrée', ar: 'تعب مسجل'),
      _ => null,
    };
  }
}
