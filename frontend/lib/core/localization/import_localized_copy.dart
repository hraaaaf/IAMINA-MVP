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

  String get cgmViaNightscout => _pick(
        en: 'VIA NIGHTSCOUT',
        fr: 'VIA NIGHTSCOUT',
        ar: 'عبر NIGHTSCOUT',
      );
  String get cgmConnected => _pick(en: 'CONNECTED', fr: 'CONNECTÉ', ar: 'متصل');
  String get cgmConfigure => _pick(en: 'Configure', fr: 'Configurer', ar: 'إعداد');
  String get cgmSync => _pick(en: 'Sync', fr: 'Synchroniser', ar: 'مزامنة');
  String get cgmDisconnect => _pick(en: 'Disconnect', fr: 'Déconnecter', ar: 'قطع الاتصال');
  String get cgmCompatibleBridge => _pick(
        en: 'Compatible through a Nightscout bridge.',
        fr: 'Compatible via un bridge Nightscout.',
        ar: 'متوافق عبر جسر Nightscout.',
      );
  String get cgmLinxBridge => _pick(
        en: 'LinX / AiDEX X through Juggluco → Nightscout.',
        fr: 'LinX / AiDEX X via Juggluco → Nightscout.',
        ar: 'LinX / AiDEX X عبر Juggluco ← Nightscout.',
      );
  String get cgmNoConnection => _pick(
        en: 'No connection configured',
        fr: 'Aucune connexion configurée',
        ar: 'لم يتم إعداد أي اتصال',
      );
  String get cgmOneConnectionNote => _pick(
        en: 'One CGM bridge can be active at a time.',
        fr: 'Un seul bridge CGM peut être actif à la fois.',
        ar: 'يمكن تفعيل جسر CGM واحد فقط في كل مرة.',
      );
  String get cgmConfigTitle => _pick(
        en: 'Configure CGM',
        fr: 'Configurer le CGM',
        ar: 'إعداد جهاز CGM',
      );
  String get cgmNightscoutUrl => _pick(
        en: 'Nightscout URL',
        fr: 'URL Nightscout',
        ar: 'رابط Nightscout',
      );
  String get cgmAuthentication => _pick(
        en: 'Authentication',
        fr: 'Authentification',
        ar: 'المصادقة',
      );
  String get cgmBearerToken => _pick(en: 'Bearer token', fr: 'Token Bearer', ar: 'رمز Bearer');
  String get cgmApiSecret => _pick(en: 'API secret', fr: 'Secret API', ar: 'سر API');
  String get cgmSecret => _pick(en: 'Secret', fr: 'Secret', ar: 'السر');
  String get cgmBridgeDisclosure => _pick(
        en: 'IAMINA reads your compatible Nightscout bridge; it does not log in directly to the sensor manufacturer.',
        fr: 'IAMINA lit votre bridge Nightscout compatible ; elle ne se connecte pas directement au fabricant du capteur.',
        ar: 'تقرأ IAMINA جسر Nightscout المتوافق ولا تسجل الدخول مباشرة لدى الشركة المصنعة للمستشعر.',
      );
  String get cgmSave => _pick(en: 'Save', fr: 'Enregistrer', ar: 'حفظ');
  String get cgmCancel => _pick(en: 'Cancel', fr: 'Annuler', ar: 'إلغاء');
  String get cgmLatestReading => _pick(en: 'Latest reading', fr: 'Dernière mesure', ar: 'آخر قراءة');
  String get cgmLastSync => _pick(en: 'Last sync', fr: 'Dernière synchro', ar: 'آخر مزامنة');
  String get cgmNeverSynced => _pick(en: 'Never synced', fr: 'Jamais synchronisé', ar: 'لم تتم المزامنة بعد');
  String get cgmNoReading => _pick(
        en: 'No CGM reading stored yet.',
        fr: 'Aucune mesure CGM enregistrée pour le moment.',
        ar: 'لا توجد قراءة CGM محفوظة حتى الآن.',
      );
  String get cgmLoading => _pick(en: 'Loading connection…', fr: 'Chargement de la connexion…', ar: 'جارٍ تحميل الاتصال…');
  String get cgmUnavailable => _pick(
        en: 'CGM connection is temporarily unavailable.',
        fr: 'La connexion CGM est temporairement indisponible.',
        ar: 'اتصال CGM غير متاح مؤقتًا.',
      );
  String get cgmSaved => _pick(en: 'Connection saved.', fr: 'Connexion enregistrée.', ar: 'تم حفظ الاتصال.');
  String get cgmSyncComplete => _pick(en: 'Sync complete.', fr: 'Synchronisation terminée.', ar: 'اكتملت المزامنة.');
  String get cgmDisconnectConfirm => _pick(
        en: 'Disconnect this CGM bridge? Stored readings remain in IAMINA.',
        fr: 'Déconnecter ce bridge CGM ? Les mesures déjà enregistrées restent dans IAMINA.',
        ar: 'هل تريد قطع اتصال جسر CGM؟ ستبقى القراءات المحفوظة في IAMINA.',
      );
}
