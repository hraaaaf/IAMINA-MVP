import 'package:amina/data/drift/database.dart';
import 'package:amina/features/journal/reports_screen.dart';
import 'package:drift/drift.dart' as drift;
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

/// D22 F07: REAL Flutter widget reflow at 200% text scale in FR and AR.
/// NOT a certification of native Chrome toolbar zoom, screen readers or
/// independent expert Arabic review. Synthetic records only.
void main() {
  for (final language in ['fr', 'ar']) {
    for (final width in [390.0, 768.0, 1280.0]) {
      testWidgets(
        'F07 ${language} at 200% text, ${width.toInt()}px: report remains descriptive',
        (tester) async {
          tester.view.physicalSize = Size(width, width == 390 ? 844 : 900);
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
              targetRangeLow: const drift.Value(70),
              targetRangeHigh: const drift.Value(180),
            ),
          );
          await db.into(db.logEntries).insert(
            LogEntriesCompanion.insert(
              createdAt: DateTime.now().subtract(const Duration(hours: 2)),
              bloodSugar: 103.25,
              clientUuid: 'f07-text200-${language}-${width.toInt()}',
            ),
          );

          final locale = Locale(language);
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
                home: MediaQuery(
                  data: const MediaQueryData(
                    textScaler: TextScaler.linear(2.0),
                  ),
                  child: const ReportsScreen(),
                ),
              ),
            ),
          );
          await tester.pumpAndSettle();
          await tester.runAsync(() async {
            await Future<void>.delayed(const Duration(milliseconds: 400));
          });
          await tester.pumpAndSettle();

          final texts = tester.widgetList<Text>(find.byType(Text))
              .map((w) => w.data ?? w.textSpan?.toPlainText() ?? '')
              .join('\n');
          expect(texts, contains(language == 'ar' ?
              'الأهداف غير مؤكدة' : 'Objectifs non vérifiés'));
          expect(texts, contains(language == 'ar' ?
              'هذا التقرير وصفي فقط' : 'Ce rapport reste descriptif'));
          expect(tester.takeException(), isNull,
              reason: 'Never mask RenderFlex overflow at 200% text');
          if (language == 'ar') {
            final element = tester.element(find.byType(ReportsScreen));
            expect(Directionality.of(element), TextDirection.rtl);
          }
          await tester.pumpWidget(const SizedBox.shrink());
          await tester.pumpAndSettle();
        },
      );
    }
  }
}
