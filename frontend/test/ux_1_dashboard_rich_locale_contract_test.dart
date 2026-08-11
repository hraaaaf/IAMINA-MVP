import 'dart:io';

import 'package:amina/l10n/app_localizations.dart';
import 'package:amina/l10n/audited_page_copy.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';

Widget _localizedProbe(Locale locale, String rawMeal) {
  return MaterialApp(
    locale: locale,
    localizationsDelegates: const [
      AppLocalizations.delegate,
      GlobalMaterialLocalizations.delegate,
      GlobalWidgetsLocalizations.delegate,
      GlobalCupertinoLocalizations.delegate,
    ],
    supportedLocales: AppLocalizations.supportedLocales,
    home: Builder(
      builder: (context) => Text(AuditedPageCopy.of(context).meal(rawMeal)),
    ),
  );
}

void main() {
  testWidgets('canonical meal IDs are localized in French and Arabic', (
    tester,
  ) async {
    await tester.pumpWidget(_localizedProbe(const Locale('fr'), 'dinner'));
    await tester.pumpAndSettle();
    expect(find.text('Dîner'), findsOneWidget);

    await tester.pumpWidget(_localizedProbe(const Locale('ar'), 'dinner'));
    await tester.pumpAndSettle();
    expect(find.text('العشاء'), findsOneWidget);

    await tester.pumpWidget(_localizedProbe(const Locale('ar'), 'breakfast'));
    await tester.pumpAndSettle();
    expect(find.text('الفطور'), findsOneWidget);
  });

  test('rich Dashboard widgets do not reintroduce known hard-coded French copy', () {
    const files = [
      'lib/features/dashboard/widgets/hero_live.dart',
      'lib/features/dashboard/widgets/hero_insight.dart',
      'lib/features/dashboard/widgets/kpi_gmi_card.dart',
      'lib/features/dashboard/widgets/kpi_cv_card.dart',
      'lib/features/dashboard/widgets/chart_section.dart',
      'lib/features/dashboard/widgets/glucose_chart_with_events.dart',
      'lib/features/dashboard/widgets/insights_section.dart',
      'lib/features/dashboard/widgets/recent_entries.dart',
    ];
    const forbidden = [
      'GMI estimée',
      'Variabilité (CV)',
      'Événements clés',
      'DÉCOUVERTES IAMINA',
      "Journal · Aujourd'hui",
      'Profil glycémique ambulatoire',
      'Données insuffisantes',
      'Analyse IA temporairement limitée',
      'IAmina analyse tes données',
      'u rapide',
    ];
    for (final file in files) {
      final source = File(file).readAsStringSync();
      for (final literal in forbidden) {
        expect(
          source.contains(literal),
          isFalse,
          reason: '$file contains $literal',
        );
      }
    }
  });
}
