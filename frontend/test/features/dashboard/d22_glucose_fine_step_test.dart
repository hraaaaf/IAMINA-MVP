import 'package:amina/data/drift/database.dart';
import 'package:amina/features/dashboard/widgets/add_log_sheet.dart';
import 'package:amina/features/dashboard/widgets/glucose_half_dial_input.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

Widget _harness(AppDatabase db, Locale locale) => MultiProvider(
  providers: [
    Provider<AppDatabase>.value(value: db),
    Provider<PatientProfileData?>.value(value: null),
  ],
  child: MaterialApp(
    locale: locale,
    localizationsDelegates: AppLocalizations.localizationsDelegates,
    supportedLocales: AppLocalizations.supportedLocales,
    home: const Scaffold(body: AddLogSheet()),
  ),
);

void main() {
  test('D22 fine adjustment does not invent or clamp medical readings', () {
    expect(d22FineAdjustedMgdl(null, 'mg/dL', 1), isNull);
    expect(d22FineAdjustedMgdl(double.nan, 'mg/dL', 1), isNull);
    expect(d22FineAdjustedMgdl(double.infinity, 'mg/dL', 1), isNull);
    expect(d22FineAdjustedMgdl(-1, 'mg/dL', 1), isNull);
    expect(d22FineAdjustedMgdl(126, 'g/L', 1), isNull);
    expect(d22FineAdjustedMgdl(126, 'mg/dL', 2), isNull);
    expect(d22FineAdjustedMgdl(1, 'mg/dL', -1), isNull);
    expect(d22FineAdjustedMgdl(126, 'mg/dL', 1), 127);
    expect(d22FineAdjustedMgdl(127, 'mg/dL', -1), 126);
    expect(d22FineAdjustedMgdl(126, 'mmol/L', 1), closeTo(127.8, 1e-8));
    expect(d22FineAdjustedMgdl(127.8, 'mmol/L', -1), closeTo(126, 1e-8));
    // The visual half-dial tops out at 320, never the direct-input range.
    expect(d22FineAdjustedMgdl(500, 'mg/dL', 1), 501);
    expect(d22FineAdjustedMgdl(500, 'mg/dL', -1), 499);
  });

  for (final locale in [const Locale('fr'), const Locale('ar')]) {
    for (final viewport in const [
      Size(390, 844),
      Size(768, 1024),
      Size(1280, 900),
    ]) {
      testWidgets(
        'D22 fine step ${locale.languageCode} ${viewport.width.toInt()}'
        'x${viewport.height.toInt()}: exact value and one Drift record',
        (tester) async {
          tester.view.physicalSize = viewport;
          tester.view.devicePixelRatio = 1;
          addTearDown(tester.view.resetPhysicalSize);
          addTearDown(tester.view.resetDevicePixelRatio);

          final db = AppDatabase(NativeDatabase.memory());
          addTearDown(db.close);
          await tester.pumpWidget(_harness(db, locale));
          await tester.pumpAndSettle();

          final input = find.byKey(const Key('glucose-input'));
          final minus = find.byKey(const Key('glucose-fine-minus'));
          final plus = find.byKey(const Key('glucose-fine-plus'));
          final unitSwitch = find.byKey(
            const Key('glucose-half-dial-unit-toggle'),
          );
          final save = find.byKey(const Key('save-log-button'));

          expect(input, findsOneWidget);
          expect(minus, findsOneWidget);
          expect(plus, findsOneWidget);

          // No defaults or guessed readings, including from the new buttons.
          expect(tester.widget<IconButton>(minus).onPressed, isNull);
          expect(tester.widget<IconButton>(plus).onPressed, isNull);
          expect(await db.select(db.logEntries).get(), isEmpty);

          await tester.enterText(input, '126');
          await tester.pump();
          expect(tester.widget<IconButton>(plus).onPressed, isNotNull);
          expect(tester.getSize(plus).width, greaterThanOrEqualTo(48));
          expect(tester.getSize(minus).height, greaterThanOrEqualTo(48));
          expect(
            tester.getTopLeft(plus).dy,
            greaterThan(tester.getTopLeft(
              find.byKey(const Key('glucose-half-dial-gesture')),
            ).dy),
          );

          await tester.tap(plus);
          await tester.pump();
          expect(tester.widget<TextField>(input).controller?.text, '127');
          await tester.tap(minus);
          await tester.pump();
          expect(tester.widget<TextField>(input).controller?.text, '126');

          await tester.tap(unitSwitch);
          await tester.pump();
          expect(tester.widget<TextField>(input).controller?.text, '7.0');
          expect(tester.widget<IconButton>(plus).tooltip, contains('0.1').or(contains('0,1')));
          await tester.tap(plus);
          await tester.pump();
          expect(tester.widget<TextField>(input).controller?.text, '7.1');
          await tester.tap(minus);
          await tester.pump();
          expect(tester.widget<TextField>(input).controller?.text, '7.0');
          await tester.tap(unitSwitch);
          await tester.pump();
          expect(tester.widget<TextField>(input).controller?.text, '126');

          // Direct input above the dial's illustrative 320 remains adjustable.
          await tester.enterText(input, '500');
          await tester.pump();
          await tester.tap(plus);
          await tester.pump();
          expect(tester.widget<TextField>(input).controller?.text, '501');

          await tester.enterText(input, '126');
          await tester.pump();
          await tester.tap(save);
          await tester.pumpAndSettle();

          final rows = await db.select(db.logEntries).get();
          expect(rows, hasLength(1));
          expect(rows.single.bloodSugar, 126.0);
          expect(find.byKey(const Key('post-save-receipt')), findsOneWidget);
          expect(tester.takeException(), isNull);
        },
      );
    }
  }
}
