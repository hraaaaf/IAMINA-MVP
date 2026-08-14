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

  String get debugNoPatientData => _pick(
        en: 'Dev mode — no patient data.',
        fr: 'Mode dev — aucune donnée patient.',
        ar: 'وضع التطوير — لا توجد بيانات للمريض.',
      );

  String get loadDemo => _pick(en: 'Load demo', fr: 'Charger démo', ar: 'تحميل البيانات التجريبية');
}
