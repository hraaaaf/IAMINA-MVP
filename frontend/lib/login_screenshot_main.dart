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
      home: const _LogoReadyLoginScreen(),
    );
  }
}

class _LogoReadyLoginScreen extends StatefulWidget {
  const _LogoReadyLoginScreen();

  @override
  State<_LogoReadyLoginScreen> createState() => _LogoReadyLoginScreenState();
}

class _LogoReadyLoginScreenState extends State<_LogoReadyLoginScreen> {
  bool _preloadStarted = false;
  bool _ready = false;
  Object? _preloadError;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (_preloadStarted) return;
    _preloadStarted = true;

    precacheImage(
      const AssetImage('assets/images/logo_amina.png'),
      context,
      onError: (Object error, StackTrace? stackTrace) {
        if (!mounted) return;
        setState(() => _preloadError = error);
      },
    ).then((_) {
      if (!mounted || _preloadError != null) return;
      setState(() => _ready = true);
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_preloadError != null) {
      return Scaffold(
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: SelectableText(
              'Logo preload failed:\n${_preloadError.runtimeType}\n${_preloadError.toString()}',
              textAlign: TextAlign.center,
              style: const TextStyle(fontSize: 12),
            ),
          ),
        ),
      );
    }

    if (!_ready) {
      return const Scaffold(body: SizedBox.expand());
    }

    return const LoginScreen();
  }
}
