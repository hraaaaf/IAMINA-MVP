import 'package:amina/l10n/app_localizations.dart';

extension DashboardNextActionLocalizedCopy on AppLocalizations {
  String get _nextActionLanguageCode => localeName.split(RegExp('[-_]')).first;

  String _nextActionPick({required String en, required String fr, required String ar}) {
    return switch (_nextActionLanguageCode) {
      'ar' => ar,
      'fr' => fr,
      _ => en,
    };
  }

  String get dashboardNextActionHeading => _nextActionPick(
        en: 'Your next step',
        fr: 'Votre prochaine étape',
        ar: 'خطوتك التالية',
      );

  String get dashboardNextActionIntro => _nextActionPick(
        en: 'IAmina can prepare one bounded non-urgent step from your governed signals. Nothing is consumed until you ask for it.',
        fr: 'IAmina peut préparer une étape non urgente et bornée à partir de vos signaux gouvernés. Rien n’est consommé avant votre demande.',
        ar: 'يمكن لـ IAmina إعداد خطوة واحدة غير عاجلة ومحدودة اعتماداً على إشاراتك الموثوقة. لا يتم استهلاك أي شيء قبل طلبك.',
      );

  String get dashboardNextActionPrepare => _nextActionPick(
        en: 'Prepare my next step',
        fr: 'Préparer ma prochaine étape',
        ar: 'إعداد خطوتي التالية',
      );

  String get dashboardNextActionLoading => _nextActionPick(
        en: 'Preparing a governed step…',
        fr: 'Préparation d’une étape gouvernée…',
        ar: 'جارٍ إعداد خطوة موثوقة…',
      );

  String get dashboardNextActionUnavailable => _nextActionPick(
        en: 'The next step is unavailable right now. No action is invented.',
        fr: 'La prochaine étape est indisponible pour le moment. Aucune action n’est inventée.',
        ar: 'الخطوة التالية غير متاحة حالياً. لا يتم اختراع أي إجراء.',
      );

  String get dashboardNextActionRetry =>
      _nextActionPick(en: 'Retry', fr: 'Réessayer', ar: 'إعادة المحاولة');

  String get dashboardNextActionCooldown => _nextActionPick(
        en: 'No new non-urgent step is highlighted right now.',
        fr: 'Aucune nouvelle étape non urgente n’est mise en avant pour le moment.',
        ar: 'لا توجد خطوة جديدة غير عاجلة بارزة حالياً.',
      );

  String get dashboardNextActionNoChange => _nextActionPick(
        en: 'No material change currently needs a new step.',
        fr: 'Aucun changement matériel ne nécessite une nouvelle étape pour le moment.',
        ar: 'لا يوجد تغير جوهري يحتاج إلى خطوة جديدة حالياً.',
      );

  String get dashboardNextActionInsufficient => _nextActionPick(
        en: 'There is not enough governed information yet to prepare a step.',
        fr: 'Il n’y a pas encore assez d’informations gouvernées pour préparer une étape.',
        ar: 'لا تتوفر بعد معلومات موثوقة كافية لإعداد خطوة.',
      );

  String dashboardNextActionTitle(String suggestionClass) => switch (suggestionClass) {
        'UNDERSTAND_DATA' => _nextActionPick(
            en: 'Understand this signal',
            fr: 'Comprendre ce signal',
            ar: 'فهم هذه الإشارة',
          ),
        'PREPARE_CLINICIAN_DISCUSSION' => _nextActionPick(
            en: 'Prepare a clinician discussion',
            fr: 'Préparer une discussion avec votre soignant',
            ar: 'الاستعداد لمناقشة الأمر مع طبيبك',
          ),
        'MONITOR' => _nextActionPick(
            en: 'Continue observing',
            fr: 'Continuer à observer',
            ar: 'مواصلة المراقبة',
          ),
        _ => _nextActionPick(
            en: 'No action available',
            fr: 'Aucune action disponible',
            ar: 'لا يوجد إجراء متاح',
          ),
      };

  String dashboardNextActionBody(String suggestionClass) => switch (suggestionClass) {
        'UNDERSTAND_DATA' => _nextActionPick(
            en: 'Review the evidence already recorded around this signal.',
            fr: 'Revoir les preuves déjà enregistrées autour de ce signal.',
            ar: 'راجع الأدلة المسجلة بالفعل حول هذه الإشارة.',
          ),
        'PREPARE_CLINICIAN_DISCUSSION' => _nextActionPick(
            en: 'Bring the governed observation and its evidence into your next clinical discussion.',
            fr: 'Apporter l’observation gouvernée et ses preuves à votre prochaine discussion clinique.',
            ar: 'خذ الملاحظة الموثوقة وأدلتها إلى مناقشتك الطبية القادمة.',
          ),
        'MONITOR' => _nextActionPick(
            en: 'Review your recorded measurements without assuming permanent resolution.',
            fr: 'Revoir vos mesures enregistrées sans supposer une résolution définitive.',
            ar: 'راجع قياساتك المسجلة دون افتراض أن الحالة حُلّت نهائياً.',
          ),
        _ => '',
      };

  String dashboardNextActionOpenLabel(String suggestionClass) => switch (suggestionClass) {
        'MONITOR' => _nextActionPick(
            en: 'See my measurements',
            fr: 'Voir mes mesures',
            ar: 'عرض قياساتي',
          ),
        'PREPARE_CLINICIAN_DISCUSSION' => _nextActionPick(
            en: 'Prepare in Companion',
            fr: 'Préparer dans Compagnon',
            ar: 'التحضير في الرفيق',
          ),
        _ => _nextActionPick(
            en: 'Open Companion',
            fr: 'Ouvrir Compagnon',
            ar: 'فتح الرفيق',
          ),
      };

  String get dashboardNextActionSafety => _nextActionPick(
        en: 'Bounded companion step only. It is not a diagnosis, prescription, dose or treatment change.',
        fr: 'Étape bornée du compagnon uniquement. Ce n’est ni un diagnostic, ni une prescription, ni une dose, ni un changement de traitement.',
        ar: 'هذه خطوة محدودة من الرفيق فقط، وليست تشخيصاً أو وصفة أو جرعة أو تغييراً للعلاج.',
      );
}
