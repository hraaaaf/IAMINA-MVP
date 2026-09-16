import 'package:flutter/material.dart';

import '../../services/auth_service.dart';
import 'local_device_enrollment_screen.dart' as local;
import 'login_screen_fr_certified.dart' as certified_fr;
import 'login_screen_mena.dart' as mena;

class LoginScreen extends StatelessWidget {
  const LoginScreen({super.key});

  @override
  Widget build(BuildContext context) {
    if (!kRemoteAccountEnrollmentEnabled) {
      return const local.LocalDeviceEnrollmentScreen();
    }
    final locale = Localizations.localeOf(context).languageCode;
    return locale == 'fr'
        ? const certified_fr.LoginScreen()
        : const mena.LoginScreen();
  }
}
