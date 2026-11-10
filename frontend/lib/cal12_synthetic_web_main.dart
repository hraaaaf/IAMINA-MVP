// Standalone CAL-12 real-Chrome-only entrypoint, NOT used by app main.dart.
// Synthetic enums, invented readings, no authentication or network.
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';

import 'features/journal/synthetic_doctor_export_web_flow.dart';
import 'services/synthetic_doctor_export_gate.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  if (SyntheticDoctorExportGate.patientExportEnabled) {
    throw StateError('CAL-12: real patient export must remain disabled');
  }
  final fromQuery = Uri.base.queryParameters['lang'];
  final lang = const ['fr', 'en', 'ar'].contains(fromQuery) ? fromQuery! : 'fr';
  runApp(MaterialApp(
    debugShowCheckedModeBanner: false,
    locale: Locale(lang),
    supportedLocales: const [Locale('fr'), Locale('en'), Locale('ar')],
    localizationsDelegates: const [
      GlobalMaterialLocalizations.delegate,
      GlobalWidgetsLocalizations.delegate,
      GlobalCupertinoLocalizations.delegate,
    ],
    theme: ThemeData(
      useMaterial3: true,
      colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF176655)),
      fontFamily: lang == 'ar' ? 'NotoSansArabic' : 'Inter',
    ),
    home: SyntheticDoctorExportWebFlow(languageCode: lang),
  ));
}
