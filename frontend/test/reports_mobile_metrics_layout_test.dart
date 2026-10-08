import 'package:amina/data/drift/database.dart';
import 'package:amina/features/journal/reports_screen.dart';
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

void main() {
  for (final testScale in <double>[1, 1.3, 1.6]) {
    testWidgets('report metrics at 390x844 scale $testScale preserve information', (
      tester,
    ) async {
      tester.view.physicalSize = const Size(390, 844);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      final db = AppDatabase(NativeDatabase.memory());
      addTearDown(db.close);
      await db.seedDemoData();

      await tester.pumpWidget(
        Provider<AppDatabase>.value(
          value: db,
          child: MaterialApp(
            locale: const Locale('fr'),
            supportedLocales: const [Locale('fr'), Locale('en'), Locale('ar')],
            localizationsDelegates: const [
              GlobalMaterialLocalizations.delegate,
              GlobalWidgetsLocalizations.delegate,
              GlobalCupertinoLocalizations.delegate,
            ],
            home: MediaQuery(
              data: MediaQueryData(textScaler: TextScaler.linear(testScale)),
              child: const Scaffold(body: ReportsScreen()),
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();
      // Drift streams emit asynchronously beyond the widget frame scheduler.
      await tester.runAsync(() async {
        await Future<void>.delayed(const Duration(milliseconds: 400));
      });
      await tester.pumpAndSettle();

      final first = find.text('Mesures enregistrées');
      if (first.evaluate().isEmpty) {
        final rendered = tester.widgetList<Text>(find.byType(Text))
            .map((text) => text.data ?? text.textSpan?.toPlainText() ?? '')
            .where((text) => text.isNotEmpty)
            .take(30)
            .toList();
        // Only printed on failure to locate the true async UI state.
        // ignore: avoid_print
        print('REPORT_TEST_RENDERED_TEXTS: $rendered');
      }
      final second = find.text('Moyenne enregistrée');
      expect(first, findsOneWidget);
      expect(second, findsOneWidget);
      expect(find.text('Jours renseignés'), findsOneWidget);
      expect(find.text('Mesures dans la cible'), findsOneWidget);
      expect(find.text('Répartition des mesures'), findsOneWidget);

      final a = tester.getRect(first);
      final b = tester.getRect(second);
      if (testScale == 1) {
        // Two KPI columns at standard phone text size.
        expect((a.top - b.top).abs(), lessThan(40));
        expect(a.left, lessThan(b.left));
      } else {
        // One column prevents cramped medical measurements with enlarged text.
        expect(b.top, greaterThan(a.bottom));
      }
      expect(tester.takeException(), isNull);
      // Detach Drift's watched streams before addTearDown closes the DB.
      await tester.pumpWidget(const SizedBox.shrink());
      await tester.pumpAndSettle();
    });
  }
}
