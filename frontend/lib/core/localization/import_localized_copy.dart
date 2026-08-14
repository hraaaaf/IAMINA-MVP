import 'package:amina/l10n/app_localizations.dart';

extension ImportLocalizedCopy on AppLocalizations {
  String get _languageCode => localeName.split(RegExp('[-_]')).first;

  String _pick({required String en, required String fr, required String ar}) {
    return switch (_languageCode) {
      'ar' => ar,
      'fr' => fr,
      _ => en,
    };
  }

  String get demoDataTitle => _pick(
        en: 'Demo data — 21 days',
        fr: 'Données démo — 21 jours',
        ar: 'بيانات تجريبية — 21 يومًا',
      );
  String get demoDataSubtitle => _pick(
        en: 'Load realistic clinical demo data to explore all features.',
        fr: 'Charger un jeu de données cliniques réalistes pour explorer toutes les fonctionnalités.',
        ar: 'حمّل بيانات سريرية تجريبية واقعية لاستكشاف جميع الميزات.',
      );
  String get loaded => _pick(en: 'Loaded', fr: 'Chargé', ar: 'تم التحميل');
  String get load => _pick(en: 'Load', fr: 'Charger', ar: 'تحميل');
  String get justNowRelative => _pick(en: 'just now', fr: 'à l’instant', ar: 'الآن');
  String minutesAgoRelative(int value) => _pick(
        en: '$value min ago', fr: 'il y a $value min', ar: 'منذ $value دقيقة');
  String hoursAgoRelative(int value) => _pick(
        en: '$value h ago', fr: 'il y a $value h', ar: 'منذ $value ساعة');
  String daysAgoRelative(int value) => _pick(
        en: '$value d ago', fr: 'il y a $value j', ar: 'منذ $value يوم');
  String weeksAgoRelative(int value) => _pick(
        en: '$value wk ago', fr: 'il y a $value sem.', ar: 'منذ $value أسبوع');
  String monthsAgoRelative(int value) => _pick(
        en: '$value mo ago', fr: 'il y a $value mois', ar: 'منذ $value شهر');
  String get staleDataTitle => _pick(
        en: 'Data is stale', fr: 'Données expirées', ar: 'البيانات قديمة');
  String staleDataBody(String relative) => _pick(
        en: 'Last reading $relative · Reload the demo for current analyses.',
        fr: 'Dernière mesure $relative · Rechargez la démo pour des analyses correctes.',
        ar: 'آخر قراءة $relative · أعد تحميل البيانات التجريبية لتحليلات محدثة.',
      );
  String readingsRecorded(int count) => _pick(
        en: '$count reading${count == 1 ? '' : 's'} recorded',
        fr: '$count mesure${count == 1 ? '' : 's'} enregistrée${count == 1 ? '' : 's'}',
        ar: 'تم تسجيل $count قراءة',
      );
  String latestReadingStoredLocally(String relative) => _pick(
        en: 'Last reading $relative · Local storage',
        fr: 'Dernière mesure $relative · Stockage local',
        ar: 'آخر قراءة $relative · تخزين محلي',
      );
  String get storedOnDevice => _pick(
        en: 'Data stored on this device',
        fr: 'Données stockées sur cet appareil',
        ar: 'البيانات مخزنة على هذا الجهاز',
      );
}
