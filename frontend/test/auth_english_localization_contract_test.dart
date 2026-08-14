import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('active auth surfaces do not embed French user-visible copy', () {
    final login = File('lib/features/auth/login_screen.dart').readAsStringSync();
    final reset = File('lib/features/auth/reset_password_screen.dart').readAsStringSync();
    final source = '$login\n$reset';

    const forbidden = <String>[
      'Créer un compte',
      'Pas encore de compte ?',
      'Confirmer le mot de passe',
      'Les mots de passe ne correspondent pas',
      'Échec de la création du compte',
      'Lien de réinitialisation invalide ou incomplet',
      'Le mot de passe doit contenir au moins 8 caractères',
      'Mot de passe réinitialisé',
      'Nouveau mot de passe',
      'Retour à la connexion',
    ];

    for (final literal in forbidden) {
      expect(source, isNot(contains(literal)), reason: 'Hardcoded locale copy: $literal');
    }
  });

  test('auth supplemental copy keeps explicit EN FR AR parity', () {
    final copy = File('lib/core/localization/auth_localized_copy.dart').readAsStringSync();

    expect(copy, contains('extension AuthLocalizedCopy on AppLocalizations'));
    expect(copy, contains("'ar' => ar"));
    expect(copy, contains("'fr' => fr"));
    expect(copy, contains('_ => en'));

    const requiredGetters = <String>[
      'signupPasswordHint',
      'confirmPassword',
      'passwordsDoNotMatch',
      'accountCreationFailed',
      'createAction',
      'noAccountYet',
      'invalidResetLink',
      'passwordMinimumEight',
      'passwordResetSucceeded',
      'resetLinkExpired',
      'newPassword',
      'newPasswordIntro',
      'resetPasswordAction',
      'backToLogin',
    ];

    for (final getter in requiredGetters) {
      expect(copy, contains('String get $getter'));
    }
  });
}
