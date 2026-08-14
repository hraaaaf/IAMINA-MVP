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
