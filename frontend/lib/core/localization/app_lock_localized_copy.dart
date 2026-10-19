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
        en: 'Use this device’s secure unlock before opening your health space.',
        fr: 'Utilisez le déverrouillage sécurisé de cet appareil avant d’ouvrir votre espace santé.',
        ar: 'استخدم قفل هذا الجهاز الآمن قبل فتح مساحتك الصحية.',
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
        en: 'Strong local unlock is not available in this browser or device. Use a supported secure browser/device before patient use.',
        fr: 'Le déverrouillage local fort n’est pas disponible sur ce navigateur ou cet appareil. Utilisez un navigateur/appareil sécurisé compatible avant tout usage patient.',
        ar: 'فتح القفل المحلي القوي غير متاح على هذا المتصفح أو الجهاز. استخدم متصفحاً أو جهازاً آمناً ومتوافقاً قبل استعماله مع المريض.',
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

  String get w01DisableLockTitle => _appLockPick(
        en: 'Turn off device lock',
        fr: 'Désactiver le verrou',
        ar: 'إيقاف قفل الجهاز',
      );

  String get w01DisableLockConfirm => _appLockPick(
        en: 'Keep account open',
        fr: 'Garder mon compte ouvert',
        ar: 'إبقاء حسابي مفتوحاً',
      );

  String get w01Cancel => _appLockPick(
        en: 'Cancel',
        fr: 'Annuler',
        ar: 'إلغاء',
      );

  String get w01OpenMedicalSpace => _appLockPick(
        en: 'Continue without device lock',
        fr: 'Continuer sans verrou',
        ar: 'المتابعة دون قفل الجهاز',
      );

  String get w01OpenMedicalSpaceWarning => _appLockPick(
        en: 'Your medical information can be opened on this device without Face ID or fingerprint. You can activate the lock later.',
        fr: 'Vos données médicales seront accessibles sur cet appareil sans Face ID ni empreinte. Vous pourrez activer le verrou plus tard.',
        ar: 'ستكون بياناتك الطبية متاحة على هذا الجهاز دون بصمة الوجه أو الإصبع. يمكنك تفعيل القفل لاحقاً.',
      );

  String get w01PreviewSkipLock => _appLockPick(
        en: 'Later · Explore without patient data',
        fr: 'Plus tard · Explorer sans données médicales',
        ar: 'لاحقاً · استكشاف دون بيانات طبية',
      );

  String get w01PreviewReadOnlyNotice => _appLockPick(
        en: 'Preview mode only. Clinical records remain inaccessible until the device is unlocked.',
        fr: 'Aperçu uniquement. Les dossiers médicaux restent inaccessibles sans déverrouillage.',
        ar: 'وضع المعاينة فقط. تبقى السجلات الطبية غير متاحة دون فتح القفل.',
      );

  String get w01PreviewTitle => _appLockPick(
        en: 'Explore IAmina',
        fr: 'Explorer IAmina',
        ar: 'استكشاف IAmina',
      );

  String get w01PreviewDescription => _appLockPick(
        en: 'Safe read-only preview. No patient record is displayed, sent or edited.',
        fr: 'Aperçu sécurisé en lecture seule. Aucun dossier patient n’est affiché, envoyé ou modifié.',
        ar: 'معاينة آمنة للقراءة فقط. لا يتم عرض أو إرسال أو تعديل أي ملف مريض.',
      );

  String get w01PreviewConsentTitle => _appLockPick(
        en: 'External AI consent',
        fr: 'Consentement IA',
        ar: 'الموافقة على الذكاء الاصطناعي',
      );

  String get w01PreviewAccept => _appLockPick(
        en: 'Accept',
        fr: 'Accepter',
        ar: 'قبول',
      );

  String get w01PreviewSkip => _appLockPick(
        en: 'Skip',
        fr: 'Passer',
        ar: 'تخطي',
      );

  String get w01PreviewConsentUnavailable => _appLockPick(
        en: 'A verified server account and unlocked device are required to record AI consent. Nothing was granted.',
        fr: 'Un compte serveur vérifié et un appareil déverrouillé sont nécessaires pour accepter. Aucun consentement n’a été accordé.',
        ar: 'يلزم حساب خادم موثق وجهاز مفتوح لتسجيل الموافقة. لم يتم منح أي موافقة.',
      );

  String get w01PreviewProtect => _appLockPick(
        en: 'Set up secure lock',
        fr: 'Configurer le verrou sécurisé',
        ar: 'إعداد القفل الآمن',
      );

  String get w01PreviewReturnUnlock => _appLockPick(
        en: 'Unlock medical space',
        fr: 'Déverrouiller l’espace médical',
        ar: 'فتح المساحة الطبية',
      );

  String get appLockRetry => _appLockPick(
        en: 'Try again',
        fr: 'Réessayer',
        ar: 'إعادة المحاولة',
      );
}
