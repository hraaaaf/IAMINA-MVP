import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';

import 'core/theme/amina_visual_language.dart';
import 'core/theme/app_theme.dart';
import 'features/import/cgm_screen.dart';
import 'l10n/app_localizations.dart';
import 'services/cgm_service.dart';

class _BrowserAuditCgmService extends CgmService {
  @override
  Future<CgmConnectionState> getConnection() async =>
      const CgmConnectionState(connected: false);
}

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  final service = _BrowserAuditCgmService();

  runApp(
    MaterialApp(
      debugShowCheckedModeBanner: false,
      theme: AminaVisualLanguage.harmonize(AminaTheme.light),
      themeMode: ThemeMode.light,
      locale: const Locale('fr'),
      localizationsDelegates: const [
        AppLocalizations.delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      supportedLocales: AppLocalizations.supportedLocales,
      home: CgmScreen(service: service),
    ),
  );
}
