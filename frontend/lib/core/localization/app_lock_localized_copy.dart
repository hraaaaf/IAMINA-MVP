import 'package:amina/l10n/app_localizations.dart';

extension AppLockLocalizedCopy on AppLocalizations {
  String get _appLockLanguageCode => localeName.split(RegExp('[-_]')).first;

  String _appLockPick({
    required String en,
    required String fr,
    required String ar,
  }) {
    return switch (_appLockLanguageCode) {
      'ar' => ar,
      'fr' => fr,
      _ => en,
    };
  }

  String get appLockEyebrow => _appLockPick(
        en: 'LOCAL SECURITY',
        fr: 'SÉCURITÉ LOCALE',
        ar: 'أمان محلي',
      );

  String get appLockSetupTitle => _appLockPick(
        en: 'Protect IAmina',
        fr: 'Protéger IAmina',
        ar: 'حماية IAmina',
      );

  String get appLockSetupSubtitle => _appLockPick(
        en: 'Choose whether to protect your health space with this device’s secure unlock, or continue without an app lock after reviewing the risks.',
        fr: 'Choisissez de protéger votre espace santé avec le verrou sécurisé de cet appareil, ou de continuer sans après avoir pris connaissance des risques.',
        ar: 'اختر حماية مساحتك الصحية بقفل الجهاز الآمن أو المتابعة بدونه بعد مراجعة المخاطر.',
      );

  String get appLockOffline => _appLockPick(
        en: 'Unlock works locally, including when IAmina is offline.',
        fr: 'Le déverrouillage fonctionne localement, même lorsque IAmina est hors connexion.',
        ar: 'يعمل فتح القفل محلياً حتى عندما يكون IAmina دون اتصال.',
      );

  String get appLockDeviceSecurity => _appLockPick(
        en: 'Your device can use Face ID, fingerprint, Windows Hello or its screen-lock PIN. IAmina never receives biometric data.',
        fr: 'Votre appareil peut utiliser Face ID, une empreinte, Windows Hello ou son code de verrouillage. IAmina ne reçoit jamais vos données biométriques.',
        ar: 'يمكن لجهازك استخدام بصمة الوجه أو الإصبع أو Windows Hello أو رمز قفل الشاشة. لا يتلقى IAmina بياناتك البيومترية أبداً.',
      );

  String get appLockActivate => _appLockPick(
        en: 'Enable secure lock',
        fr: 'Activer le verrou sécurisé',
        ar: 'تفعيل القفل الآمن',
      );

  String get appLockChecking => _appLockPick(
        en: 'Checking this device…',
        fr: 'Vérification de cet appareil…',
        ar: 'جارٍ التحقق من هذا الجهاز…',
      );

  String get appLockUnavailable => _appLockPick(
        en: 'Secure app locking is unavailable on this browser or device. You may continue without it after acknowledging the privacy risks.',
        fr: 'Le verrouillage local sécurisé n’est pas disponible sur ce navigateur ou cet appareil. Vous pouvez continuer sans verrouillage après avoir accepté les risques de confidentialité.',
        ar: 'القفل المحلي الآمن غير متاح على هذا المتصفح أو الجهاز. يمكنك المتابعة بدونه بعد الإقرار بمخاطر الخصوصية.',
      );

  String get appLockInsecureContext => _appLockPick(
        en: 'Secure unlock requires HTTPS (or localhost during development).',
        fr: 'Le déverrouillage sécurisé exige HTTPS (ou localhost pendant le développement).',
        ar: 'يتطلب فتح القفل الآمن اتصال HTTPS (أو localhost أثناء التطوير).',
      );

  String get appLockSetupFailed => _appLockPick(
        en: 'Secure lock could not be activated. Nothing was unlocked.',
        fr: 'Le verrou sécurisé n’a pas pu être activé. Aucun accès n’a été ouvert.',
        ar: 'تعذر تفعيل القفل الآمن. لم يتم فتح أي وصول.',
      );

  String get appLockLockedTitle => _appLockPick(
        en: 'IAmina is locked',
        fr: 'IAmina est verrouillée',
        ar: 'IAmina مقفل',
      );

  String get appLockLockedSubtitle => _appLockPick(
        en: 'Verify with this device to reopen your local health space.',
        fr: 'Vérifiez avec cet appareil pour rouvrir votre espace santé local.',
        ar: 'تحقق باستخدام هذا الجهاز لإعادة فتح مساحتك الصحية المحلية.',
      );

  String get appLockUnlock => _appLockPick(
        en: 'Unlock IAmina',
        fr: 'Déverrouiller IAmina',
        ar: 'فتح IAmina',
      );

  String get appLockUnlockFailed => _appLockPick(
        en: 'Verification failed or was cancelled. IAmina remains locked.',
        fr: 'La vérification a échoué ou a été annulée. IAmina reste verrouillée.',
        ar: 'فشل التحقق أو تم إلغاؤه. يبقى IAmina مقفلاً.',
      );

  String get appLockRecoveryTitle => _appLockPick(
        en: 'Security recovery required',
        fr: 'Récupération de sécurité requise',
        ar: 'استعادة الأمان مطلوبة',
      );

  String get appLockRecoveryBody => _appLockPick(
        en: 'The previously configured local lock can no longer be verified. IAmina will not bypass it or expose the clinical space.',
        fr: 'Le verrou local déjà configuré ne peut plus être vérifié. IAmina ne le contournera pas et n’ouvrira pas l’espace clinique.',
        ar: 'لم يعد من الممكن التحقق من القفل المحلي الذي تم إعداده سابقاً. لن يتجاوزه IAmina ولن يفتح المساحة السريرية.',
      );

  String get appLockRecoveryReauthenticate => _appLockPick(
        en: 'Sign in again to recover',
        fr: 'Se reconnecter pour récupérer',
        ar: 'تسجيل الدخول مجدداً للاستعادة',
      );

  String get appLockRecoveryReenroll => _appLockPick(
        en: 'Create a new secure lock',
        fr: 'Créer un nouveau verrou sécurisé',
        ar: 'إنشاء قفل آمن جديد',
      );

  String get appLockRecoveryFailed => _appLockPick(
        en: 'Security recovery failed. The clinical space remains locked.',
        fr: 'La récupération de sécurité a échoué. L’espace clinique reste verrouillé.',
        ar: 'فشلت استعادة الأمان. تبقى المساحة السريرية مقفلة.',
      );

  String get appLockRetry => _appLockPick(
        en: 'Try again',
        fr: 'Réessayer',
        ar: 'إعادة المحاولة',
      );
}
