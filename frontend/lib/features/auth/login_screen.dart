import 'package:flutter/material.dart';

import '../../services/auth_service.dart';
import 'local_device_enrollment_screen.dart' as local;
import 'login_screen_fr_certified.dart' as certified_fr;
import 'login_screen_mena.dart' as mena;

/// Both journeys remain available when remote accounts are enabled.
/// Selecting a local vault must never create a synthetic remote identity.
class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  bool _accountMode = false;

  @override
  Widget build(BuildContext context) {
    if (!_accountMode || !kRemoteAccountEnrollmentEnabled) {
      return local.LocalDeviceEnrollmentScreen(
        onChooseAccount: kRemoteAccountEnrollmentEnabled
            ? () => setState(() => _accountMode = true)
            : null,
      );
    }

    final locale = Localizations.localeOf(context).languageCode;
    final backText = switch (locale) {
      'fr' => 'Continuer sans compte',
      'ar' => 'المتابعة بدون حساب',
      _ => 'Continue without an account',
    };
    return Column(
      children: [
        Material(
          color: Theme.of(context).scaffoldBackgroundColor,
          child: SafeArea(
            bottom: false,
            child: Align(
              alignment: AlignmentDirectional.centerStart,
              child: TextButton.icon(
                key: const Key('d30-return-local'),
                onPressed: () => setState(() => _accountMode = false),
                icon: const Icon(Icons.arrow_back_rounded),
                label: Text(backText),
              ),
            ),
          ),
        ),
        Expanded(
          child: locale == 'fr'
              ? const certified_fr.LoginScreen()
              : const mena.LoginScreen(),
        ),
      ],
    );
  }
}
