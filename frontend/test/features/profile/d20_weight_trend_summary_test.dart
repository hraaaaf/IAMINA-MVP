import 'package:amina/data/drift/patient_weight_history_store.dart';
import 'package:amina/features/profile/d20_weight_trend_summary.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';

const _uuid1 = '123e4567-e89b-42d3-a456-426614174000';
const _uuid2 = '123e4567-e89b-42d3-a456-426614174001';

LocalWeightObservation _weight(String uuid, int value, int day,
    {int owner = 734}) => LocalWeightObservation(
  ownerId: owner,
  clientUuid: uuid,
  valueHundredths: value,
  unit: 'kg',
  kilogramsHundredths: value,
  measuredAtUtc: DateTime.utc(2026, 10, day, 9),
  provenance: 'patient_declared',
);

Future<void> _pump(WidgetTester tester, {
  required List<LocalWeightObservation> history,
  String locale = 'fr',
}) async {
  await tester.pumpWidget(MaterialApp(
    locale: Locale(locale),
    supportedLocales: const [Locale('fr'), Locale('en'), Locale('ar')],
    localizationsDelegates: const [
      GlobalMaterialLocalizations.delegate,
      GlobalWidgetsLocalizations.delegate,
      GlobalCupertinoLocalizations.delegate,
    ],
    home: Scaffold(body: SingleChildScrollView(
      padding: const EdgeInsets.all(12),
      child: D20WeightTrendSummary(
        history: history, asOfUtc: DateTime.utc(2026, 10, 16)),
    )),
  ));
  await tester.pumpAndSettle();
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('D20-E no measurements means no inferred trend',
      (tester) async {
    await _pump(tester, history: []);
    expect(find.byKey(const Key('d20-trend-insufficient')), findsOneWidget);
    expect(find.byKey(const Key('d20-trend-delta')), findsNothing);
    expect(find.byKey(const Key('d20-trend-disclaimer')), findsOneWidget);
  });

  testWidgets('D20-E one measurement is never a comparison',
      (tester) async {
    await _pump(tester, history: [_weight(_uuid1, 7000, 1)]);
    expect(find.byKey(const Key('d20-trend-insufficient')), findsOneWidget);
    expect(find.byKey(const Key('d20-trend-delta')), findsNothing);
  });

  testWidgets('D20-E sourced difference has explicit period and neutral label',
      (tester) async {
    await _pump(tester, history: [
      _weight(_uuid2, 7100, 14), _weight(_uuid1, 7000, 1),
    ]);
    expect(find.byKey(const Key('d20-trend-delta')), findsOneWidget);
    expect(find.byKey(const Key('d20-trend-period')), findsOneWidget);
    expect(find.byKey(const Key('d20-trend-provenance')), findsOneWidget);
    expect(find.textContaining('alerte médicale'), findsOneWidget);
  });

  testWidgets('D20-E mixed owners or duplicated timestamps fail closed',
      (tester) async {
    await _pump(tester, history: [
      _weight(_uuid1, 7000, 1), _weight(_uuid2, 7100, 14, owner: 812),
    ]);
    expect(find.byKey(const Key('d20-trend-delta')), findsNothing);
    await _pump(tester, history: [
      _weight(_uuid1, 7000, 1), _weight(_uuid2, 7100, 1),
    ]);
    expect(find.byKey(const Key('d20-trend-delta')), findsNothing);
  });

  testWidgets('D20-E FR/EN/AR RTL across 390/430/768/1280 without overflow',
      (tester) async {
    for (final width in [390.0, 430.0, 768.0, 1280.0]) {
      tester.view.devicePixelRatio = 1;
      tester.view.physicalSize = Size(width, 900);
      for (final locale in ['fr', 'en', 'ar']) {
        await _pump(tester, locale: locale, history: [
          _weight(_uuid2, 7100, 14), _weight(_uuid1, 7000, 1),
        ]);
        expect(find.byKey(const Key('d20-trend-section')), findsOneWidget);
        expect(Directionality.of(tester.element(
          find.byKey(const Key('d20-trend-section')),
        )), locale == 'ar' ? TextDirection.rtl : TextDirection.ltr);
        expect(tester.takeException(), isNull);
      }
    }
    tester.view.resetPhysicalSize();
    tester.view.resetDevicePixelRatio();
  });
}
