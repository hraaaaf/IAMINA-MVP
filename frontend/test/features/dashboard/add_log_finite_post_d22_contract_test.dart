import 'package:amina/data/drift/database.dart';
import 'package:amina/features/dashboard/widgets/add_log_sheet.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

Widget _addLogHarness(AppDatabase db, Locale locale) => MultiProvider(
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
  test('D12 never guesses or accepts missing/negative/non-numeric glucose', () {
    for (final raw in ['', ' ', 'not-a-reading', '0', '-0', '-1', '-2,3']) {
      expect(parsePositiveFiniteGlucoseInput(raw), isNull, reason: raw);
      expect(normalizeFiniteGlucoseMgdl(raw, 'mg/dL'), isNull, reason: raw);
      expect(normalizeFiniteGlucoseMgdl(raw, 'mmol/L'), isNull, reason: raw);
    }
  });

  test('D12 rejects NaN, both infinities, overflow, unsupported unit', () {
    for (final raw in ['NaN', 'Infinity', '-Infinity', '1e999']) {
      expect(parsePositiveFiniteGlucoseInput(raw), isNull, reason: raw);
      expect(normalizeFiniteGlucoseMgdl(raw, 'mg/dL'), isNull);
      expect(normalizeFiniteGlucoseMgdl(raw, 'mmol/L'), isNull);
    }
    // Finite source, overflow only during multiplication by the unchanged 18.
    expect(parsePositiveFiniteGlucoseInput('1e308'), 1e308);
    expect(normalizeFiniteGlucoseMgdl('1e308', 'mmol/L'), isNull);
    expect(normalizeFiniteGlucoseMgdl('1e308', 'mg/dL'), 1e308);
    expect(normalizeFiniteGlucoseMgdl('126', 'g/L'), isNull);
  });

  test('D12 preserves valid comma decimals and existing D22 18.0 conversion', () {
    expect(parsePositiveFiniteGlucoseInput(' 5,5 '), 5.5);
    expect(normalizeFiniteGlucoseMgdl(' 5,5 ', 'mmol/L'), 99.0);
    expect(normalizeFiniteGlucoseMgdl('126', 'mg/dL'), 126.0);
    expect(normalizeFiniteGlucoseMgdl('7.0', 'mmol/L'), 126.0);
    // No new medical minimum/maximum or implicit default is introduced.
    expect(normalizeFiniteGlucoseMgdl('', 'mg/dL'), isNull);
  });

  for (final locale in [const Locale('fr'), const Locale('ar')]) {
    for (final viewport in const [
      Size(390, 844),
      Size(768, 1024),
      Size(1280, 900),
    ]) {
      testWidgets(
        'D12 ${locale.languageCode} ${viewport.width.toInt()}x'
        '${viewport.height.toInt()}: invalid stays disabled, D22 roundtrip is exact',
        (tester) async {
          tester.view.physicalSize = viewport;
        tester.view.devicePixelRatio = 1;
        addTearDown(tester.view.resetPhysicalSize);
        addTearDown(tester.view.resetDevicePixelRatio);

        final db = AppDatabase(NativeDatabase.memory());
        addTearDown(db.close);

        await tester.pumpWidget(_addLogHarness(db, locale));
        await tester.pumpAndSettle();

        final input = find.byKey(const Key('glucose-input'));
        final save = find.byKey(const Key('save-log-button'));
        final toggle = find.byKey(const Key('glucose-half-dial-unit-toggle'));
        expect(input, findsOneWidget);
        expect(toggle, findsOneWidget);

        // 400 digits are allowed by the decimal keypad filter but parse
        // to nonfinite double; the UI must not let this reach Drift.
        await tester.enterText(input, List<String>.filled(400, '9').join());
        await tester.pump();
        expect(
          tester.widget<FilledButton>(save).onPressed,
          isNull,
          reason: 'Nonfinite or overflow input must disable Save.',
        );
        expect(await db.select(db.logEntries).get(), isEmpty);

        await tester.enterText(input, '126');
        await tester.pump();
        expect(tester.widget<FilledButton>(save).onPressed, isNotNull);

        await tester.tap(toggle);
        await tester.pump();
        expect(tester.widget<TextField>(input).controller?.text, '7.0');

        await tester.tap(toggle);
        await tester.pump();
        expect(tester.widget<TextField>(input).controller?.text, '126');
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
