import 'dart:io';

import 'package:amina/data/drift/database.dart';
import 'package:amina/features/journal/reports_screen.dart';
import 'package:drift/drift.dart' as drift;
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

/// D22 F05: synthetic, local, descriptive-only REPORT evidence.
/// This is NOT a CGM, PDF/CSV export, clinical target or remote certification.
void main() {
  for (final locale in <Locale>[
    const Locale('fr'),
    const Locale('en'),
    const Locale('ar'),
  ]) {
    testWidgets('D22 F05 legacy targets never classify report in ${locale.languageCode}',
        (tester) async {
      tester.view.physicalSize = const Size(390, 844);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      final db = AppDatabase(NativeDatabase.memory());
      addTearDown(db.close);
      await db.into(db.patientProfiles).insert(
        PatientProfilesCompanion.insert(
          userId: const drift.Value(1),
          updatedAt: DateTime.utc(2026, 11, 3),
          unitPreference: const drift.Value('mmol/L'),
          // Intentionally legacy, unverified/unauthorized numbers.
          targetRangeLow: const drift.Value(70),
          targetRangeHigh: const drift.Value(180),
        ),
      );
      await db.into(db.logEntries).insert(
        LogEntriesCompanion.insert(
          createdAt: DateTime.now().subtract(const Duration(hours: 1)),
          bloodSugar: 103.25,
          clientUuid: 'f05-local-synthetic-${locale.languageCode}',
        ),
      );

      await tester.pumpWidget(
        Provider<AppDatabase>.value(
          value: db,
          child: MaterialApp(
            locale: locale,
            supportedLocales: const [Locale('fr'), Locale('en'), Locale('ar')],
            localizationsDelegates: const [
              GlobalMaterialLocalizations.delegate,
              GlobalWidgetsLocalizations.delegate,
              GlobalCupertinoLocalizations.delegate,
            ],
            home: const ReportsScreen(),
          ),
        ),
      );
      await tester.pumpAndSettle();
      await tester.runAsync(() async {
        await Future<void>.delayed(const Duration(milliseconds: 450));
      });
      await tester.pumpAndSettle();

      final text = tester.widgetList<Text>(find.byType(Text)).map(
        (w) => w.data ?? w.textSpan?.toPlainText() ?? '',
      ).join('\n');
      final unverified = switch (locale.languageCode) {
        'fr' => 'Objectifs non vérifiés',
        'ar' => 'الأهداف غير مؤكدة',
        _ => 'Targets unverified',
      };
      final descriptive = switch (locale.languageCode) {
        'fr' => 'Ce rapport reste descriptif',
        'ar' => 'هذا التقرير وصفي فقط',
        _ => 'This report stays descriptive',
      };
      expect(text, contains(unverified));
      expect(text, contains(descriptive));
      expect(text, isNot(contains('103.25 mg/dL')));
      final forbiddenLabel = switch (locale.languageCode) {
        'fr' => 'Mesures dans la cible',
        'ar' => 'قياسات ضمن النطاق',
        _ => 'Measurements in range',
      };
      expect(text, isNot(contains(forbiddenLabel)));
      expect(tester.takeException(), isNull);
      await tester.pumpWidget(const SizedBox.shrink());
      await tester.pumpAndSettle();
    });
  }

  test('D22 F05 fail-closed code paths: no unapproved target for distribution',
      () {
    final report = File(
      'lib/features/journal/reports_screen_presentation.dart',
    ).readAsStringSync();
    expect(report, contains('const double? low = null;'));
    expect(report, contains('const double? high = null;'));
    expect(report, contains('if (stats.hasTarget)'));
    expect(report, contains('No classification is invented'));
    expect(report, isNot(contains('final low = profile?.targetRangeLow;')));
    expect(report, isNot(contains('final high = profile?.targetRangeHigh;')));

    // CGM AGP / TIR requires separate verified producer metadata.
    final summary = File(
      'lib/features/journal/ai_summary_screen_presentation.dart',
    ).readAsStringSync();
    expect(summary, contains('final hasEligibleAgp = agpData.isNotEmpty'));
    expect(summary, contains('kpis?.tirPct == null || kpis?.tarPct == null'));
    expect(summary, isNot(contains('kpis.tirPct ?? 0.0')));
    // PDF, CSV and sensor-source end-to-end are explicitly NOT_RUN here.
  });
}
