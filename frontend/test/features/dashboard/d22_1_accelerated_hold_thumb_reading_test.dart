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
  test('D22.1 repeat intervals accelerate and remain bounded', () {
    expect(d221HoldRepeatDelay(0), const Duration(milliseconds: 270));
    expect(d221HoldRepeatDelay(2), const Duration(milliseconds: 270));
    expect(d221HoldRepeatDelay(3), const Duration(milliseconds: 155));
    expect(d221HoldRepeatDelay(8), const Duration(milliseconds: 155));
    expect(d221HoldRepeatDelay(9), const Duration(milliseconds: 85));
    expect(d221HoldRepeatDelay(100), const Duration(milliseconds: 85));
    expect(d22FineAdjustedMgdl(null, 'mg/dL', 1), isNull);
  });

  for (final locale in [const Locale('fr'), const Locale('ar')]) {
    for (final viewport in const [
      Size(390, 844),
      Size(768, 1024),
      Size(1280, 900),
    ]) {
      testWidgets(
        'D22.1 off-thumb reading ${locale.languageCode} '
        '${viewport.width.toInt()}x${viewport.height.toInt()}',
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
          final gestureSurface =
              find.byKey(const Key('glucose-half-dial-gesture'));
          final reading = find.byKey(const Key('glucose-drag-reading'));
          final readingValue =
              find.byKey(const Key('glucose-drag-reading-value'));
          final save = find.byKey(const Key('save-log-button'));
          final plus = find.byKey(const Key('glucose-fine-plus'));
          final minus = find.byKey(const Key('glucose-fine-minus'));

          expect(reading, findsNothing);
          expect(tester.widget<IconButton>(plus).onPressed, isNull);
          expect(tester.widget<IconButton>(minus).onPressed, isNull);
          expect(await db.select(db.logEntries).get(), isEmpty);

          final arcTop = tester.getTopLeft(gestureSurface);
          final arcSize = tester.getSize(gestureSurface);
          // At the upper (green) center of the semicircle, the thumb
          // obscures the original inline text, not the fixed header above.
          final radius = arcSize.width / 2 - 30;
          final greenPoint = arcTop +
              Offset(arcSize.width / 2, arcSize.height - 18 - radius);

          final finger = await tester.startGesture(greenPoint);
          await tester.pump();
          expect(reading, findsOneWidget);
          expect(readingValue, findsOneWidget);
          expect(tester.getTopLeft(reading).dy,
              lessThan(tester.getTopLeft(gestureSurface).dy));
          expect(tester.getTopLeft(gestureSurface).dy, arcTop.dy,
              reason: 'Floating feedback must not shift the arc during drag.');
          expect(tester.widget<Text>(readingValue).data, contains('mg/dL'));

          await finger.moveBy(const Offset(12, 0));
          await tester.pump();
          expect(readingValue, findsOneWidget);
          expect(tester.getTopLeft(gestureSurface).dy, arcTop.dy);
          await finger.up();
          await tester.pump();
          expect(reading, findsNothing);

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

  for (final locale in [const Locale('fr'), const Locale('ar')]) {
    testWidgets('D22.1 ${locale.languageCode} accelerated +/- release stops',
        (tester) async {
      tester.view.physicalSize = const Size(390, 844);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      final db = AppDatabase(NativeDatabase.memory());
      addTearDown(db.close);
      await tester.pumpWidget(_harness(db, locale));
      await tester.pumpAndSettle();

      final input = find.byKey(const Key('glucose-input'));
      final plus = find.byKey(const Key('glucose-fine-plus'));
      final minus = find.byKey(const Key('glucose-fine-minus'));
      final toggle =
          find.byKey(const Key('glucose-half-dial-unit-toggle'));
      String readingText() => tester.widget<TextField>(input).controller!.text;

      await tester.enterText(input, '126');
      await tester.pump();
      // Short tap remains exactly one unit, without an early hold timer.
      await tester.tap(plus);
      await tester.pump();
      expect(readingText(), '127');
      await tester.tap(minus);
      await tester.pump();
      expect(readingText(), '126');

      final finger = await tester.startGesture(tester.getCenter(plus));
      await tester.pump(const Duration(milliseconds: 580));
      final early = int.parse(readingText());
      expect(early, greaterThan(126),
          reason: 'Long press must advance before finger release.');

      await tester.pump(const Duration(milliseconds: 720));
      final medium = int.parse(readingText());
      expect(medium, greaterThan(early));

      await tester.pump(const Duration(milliseconds: 1300));
      final late = int.parse(readingText());
      expect(late, greaterThan(medium));
      expect(late - medium, greaterThan(medium - early),
          reason: 'Hold repeat rate must increase with duration.');

      // Leaving the 48-pixel button must stop a still-pressed finger, too.
      await finger.moveBy(const Offset(120, 0));
      await tester.pump();
      final slidOutside = readingText();
      await tester.pump(const Duration(milliseconds: 650));
      expect(readingText(), slidOutside,
          reason: 'No repeated step after the finger leaves the button.');
      await finger.up();
      await tester.pump();
      final released = readingText();
      await tester.pump(const Duration(seconds: 2));
      expect(readingText(), released,
          reason: 'Release must cancel all accelerated timers.');

      await tester.tap(toggle);
      await tester.pump();
      await tester.enterText(input, '7.0');
      await tester.pump();
      final back = await tester.startGesture(tester.getCenter(minus));
      await tester.pump(const Duration(milliseconds: 1350));
      expect(double.parse(readingText()), lessThan(7.0));
      await back.up();
      await tester.pump();
      final stopped = readingText();
      await tester.pump(const Duration(milliseconds: 700));
      expect(readingText(), stopped);

      await tester.pumpWidget(const SizedBox.shrink());
      await tester.pump(const Duration(seconds: 1));
      expect(tester.takeException(), isNull);
      expect(await db.select(db.logEntries).get(), isEmpty,
          reason: 'Hold never writes a glucose reading before Save.');
    });
  }
}
