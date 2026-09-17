import 'package:amina/l10n/app_localizations.dart';

extension AuthLocalizedCopy on AppLocalizations {
  String get _languageCode => localeName.split(RegExp('[-_]')).first;

  String _pick({required String en, required String fr, required String ar}) {
    return switch (_languageCode) {
      'ar' => ar,
      'fr' => fr,
      _ => en,
    };
  }

  String get signupPasswordHint => _pick(
        en: '••••••••  (min. 6 characters)',
        fr: '••••••••  (min. 6 caractères)',
        ar: '••••••••  (6 أحرف على الأقل)',
      );

  String get confirmPassword => _pick(
        en: 'Confirm password',
        fr: 'Confirmer le mot de passe',
        ar: 'تأكيد كلمة المرور',
      );

  String get passwordsDoNotMatch => _pick(
        en: 'Passwords do not match.',
        fr: 'Les mots de passe ne correspondent pas.',
        ar: 'كلمتا المرور غير متطابقتين.',
      );

  String get accountCreationFailed => _pick(
        en: 'Account creation failed — check the email and password.',
        fr: 'Échec de la création du compte — vérifiez l’e-mail et le mot de passe.',
        ar: 'تعذر إنشاء الحساب — تحقق من البريد الإلكتروني وكلمة المرور.',
      );

  String get createAction => _pick(en: 'Create', fr: 'Créer', ar: 'إنشاء');

  String get noAccountYet => _pick(
        en: 'No account yet?',
        fr: 'Pas encore de compte ?',
        ar: 'ليس لديك حساب بعد؟',
      );

  String get localEnrollmentEyebrow => _pick(
        en: 'ON THIS DEVICE',
        fr: 'SUR CET APPAREIL',
        ar: 'على هذا الجهاز',
      );

  String get localEnrollmentTitle => _pick(
        en: 'Set up IAmina here',
        fr: 'Configurer IAmina ici',
        ar: 'إعداد IAmina هنا',
      );

  String get localEnrollmentSubtitle => _pick(
        en: 'Create your IAmina space on this device. No online account is required.',
        fr: 'Créez votre espace IAmina sur cet appareil. Aucun compte en ligne n’est nécessaire.',
        ar: 'أنشئ مساحة IAmina على هذا الجهاز. لا يلزم حساب عبر الإنترنت.',
      );

  String get localEnrollmentOffline => _pick(
        en: 'No Internet connection is required to set up or reopen IAmina on this device.',
        fr: 'Aucune connexion Internet n’est nécessaire pour configurer ou rouvrir IAmina sur cet appareil.',
        ar: 'لا يلزم اتصال بالإنترنت لإعداد IAmina أو إعادة فتحه على هذا الجهاز.',
      );

  String get localEnrollmentSecurity => _pick(
        en: 'Next, IAmina will ask this device to protect access with its secure unlock.',
        fr: 'Ensuite, IAmina demandera à cet appareil de protéger l’accès avec son déverrouillage sécurisé.',
        ar: 'بعد ذلك سيطلب IAmina من هذا الجهاز حماية الوصول باستخدام فتح القفل الآمن.',
      );

  String get localEnrollmentAction => _pick(
        en: 'Set up this device',
        fr: 'Configurer cet appareil',
        ar: 'إعداد هذا الجهاز',
      );

  String get localEnrollmentFooter => _pick(
        en: 'You can keep using local features even when you are offline.',
        fr: 'Vous pourrez continuer à utiliser les fonctions locales même hors connexion.',
        ar: 'يمكنك الاستمرار في استخدام الوظائف المحلية حتى دون اتصال.',
      );

  String get localEnrollmentFailed => _pick(
        en: 'Local setup failed. Check that secure storage is available on this device.',
        fr: 'La configuration locale a échoué. Vérifiez que le stockage sécurisé est disponible sur cet appareil.',
        ar: 'فشل الإعداد المحلي. تحقق من توفر التخزين الآمن على هذا الجهاز.',
      );

  String get invalidResetLink => _pick(
        en: 'The reset link is invalid or incomplete.',
        fr: 'Lien de réinitialisation invalide ou incomplet.',
        ar: 'رابط إعادة التعيين غير صالح أو غير مكتمل.',
      );

  String get passwordMinimumEight => _pick(
        en: 'The password must contain at least 8 characters.',
        fr: 'Le mot de passe doit contenir au moins 8 caractères.',
        ar: 'يجب أن تحتوي كلمة المرور على 8 أحرف على الأقل.',
      );

  String get passwordResetSucceeded => _pick(
        en: 'Password reset. You can now sign in.',
        fr: 'Mot de passe réinitialisé. Vous pouvez vous connecter.',
        ar: 'تمت إعادة تعيين كلمة المرور. يمكنك تسجيل الدخول الآن.',
      );

  String get resetLinkExpired => _pick(
        en: 'This link is invalid, expired, or has already been used.',
        fr: 'Ce lien est invalide, expiré ou déjà utilisé.',
        ar: 'هذا الرابط غير صالح أو منتهي الصلاحية أو تم استخدامه بالفعل.',
      );

  String get newPassword => _pick(
        en: 'New password',
        fr: 'Nouveau mot de passe',
        ar: 'كلمة مرور جديدة',
      );

  String get newPasswordIntro => _pick(
        en: 'Choose a new password for your IAmina account.',
        fr: 'Choisissez un nouveau mot de passe pour votre compte IAmina.',
        ar: 'اختر كلمة مرور جديدة لحساب IAmina الخاص بك.',
      );

  String get resetPasswordAction => _pick(
        en: 'Reset password',
        fr: 'Réinitialiser le mot de passe',
        ar: 'إعادة تعيين كلمة المرور',
      );

  String get backToLogin => _pick(
        en: 'Back to sign in',
        fr: 'Retour à la connexion',
        ar: 'العودة إلى تسجيل الدخول',
      );
}
