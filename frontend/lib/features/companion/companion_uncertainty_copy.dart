import 'package:flutter/widgets.dart';

String? companionPatternLimitationLabel(BuildContext context, String code) {
  final language = Localizations.localeOf(context).languageCode;

  String pick({required String fr, required String en, required String ar}) =>
      language == 'ar' ? ar : language == 'en' ? en : fr;

  return switch (code) {
    'numeric_pattern_values_describe_last_eligible_active_evidence' => pick(
        fr: 'Les valeurs décrivent les dernières données actives admissibles avant la résolution.',
        en: 'Values describe the last eligible active evidence before resolution.',
        ar: 'تصف القيم آخر بيانات نشطة مؤهلة قبل زوال النمط.',
      ),
    'improving_descriptively_does_not_mean_treatment_response_or_outcome' => pick(
        fr: 'Ce rapprochement descriptif ne prouve ni une réponse au traitement ni un résultat clinique.',
        en: 'This descriptive movement does not prove treatment response or a clinical outcome.',
        ar: 'هذا التحسن الوصفي لا يثبت الاستجابة للعلاج ولا نتيجة سريرية.',
      ),
    _ => null,
  };
}

String? companionMissingDataLabel(BuildContext context, String code) {
  final language = Localizations.localeOf(context).languageCode;

  String pick({required String fr, required String en, required String ar}) =>
      language == 'ar' ? ar : language == 'en' ? en : fr;

  return switch (code) {
    'anchor_missing_state_that_predates_review' => pick(
        fr: 'L’état antérieur à la revue n’est pas disponible dans le point de comparaison.',
        en: 'The state that predates the review is missing from the comparison anchor.',
        ar: 'الحالة السابقة للمراجعة غير متوفرة في نقطة المقارنة.',
      ),
    'post_review_transition_not_provable' => pick(
        fr: 'Les données disponibles ne permettent pas de prouver la transition après la revue.',
        en: 'Available data cannot prove the transition after the review.',
        ar: 'البيانات المتاحة لا تكفي لإثبات الانتقال بعد المراجعة.',
      ),
    'current_governed_state_missing_cannot_infer_resolution' => pick(
        fr: 'L’état actuel manque : une résolution ne peut pas être déduite.',
        en: 'Current governed state is missing, so resolution cannot be inferred.',
        ar: 'الحالة الحالية غير متوفرة، لذلك لا يمكن استنتاج زوال النمط.',
      ),
    'reactivation_after_review_not_provable' => pick(
        fr: 'Une réapparition après la revue ne peut pas être démontrée avec ces données.',
        en: 'Reactivation after the review cannot be proven from these data.',
        ar: 'لا يمكن إثبات عودة النمط بعد المراجعة من هذه البيانات.',
      ),
    'resolution_after_review_not_provable' => pick(
        fr: 'Une résolution après la revue ne peut pas être démontrée avec ces données.',
        en: 'Resolution after the review cannot be proven from these data.',
        ar: 'لا يمكن إثبات زوال النمط بعد المراجعة من هذه البيانات.',
      ),
    'no_eligible_post_review_evidence' => pick(
        fr: 'Aucune donnée admissible après la revue ne permet cette comparaison.',
        en: 'No eligible post-review evidence supports this comparison.',
        ar: 'لا توجد بيانات مؤهلة بعد المراجعة تدعم هذه المقارنة.',
      ),
    _ => null,
  };
}
