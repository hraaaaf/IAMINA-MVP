import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';

import 'core/theme/app_theme.dart';
import 'features/auth/login_screen.dart';
import 'l10n/app_localizations.dart';

/// CI-only entrypoint used to render the real login screen without backend setup.
void main() {
  runApp(const _LoginScreenshotApp());
}

class _LoginScreenshotApp extends StatelessWidget {
  const _LoginScreenshotApp();

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      theme: AminaTheme.light,
      locale: const Locale('fr'),
      localizationsDelegates: const [
        AppLocalizations.delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      supportedLocales: AppLocalizations.supportedLocales,
      home: const LoginScreen(),
    );
  }
}
