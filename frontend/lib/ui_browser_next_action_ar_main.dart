import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';

import 'core/theme/amina_visual_language.dart';
import 'core/theme/app_theme.dart';
import 'features/dashboard/widgets/dashboard_next_action_section.dart';
import 'l10n/app_localizations.dart';
import 'services/companion_service.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  final service = CompanionService();

  runApp(_ArabicNextActionAuditApp(service: service));
}

class _ArabicNextActionAuditApp extends StatelessWidget {
  final CompanionService service;

  const _ArabicNextActionAuditApp({required this.service});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      theme: AminaVisualLanguage.harmonize(AminaTheme.light),
      themeMode: ThemeMode.light,
      locale: const Locale('ar'),
      localizationsDelegates: const [
        AppLocalizations.delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      supportedLocales: AppLocalizations.supportedLocales,
      home: Scaffold(
        backgroundColor: const Color(0xFFF4FBF9),
        body: SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: DashboardNextActionSection(service: service),
          ),
        ),
      ),
    );
  }
}
