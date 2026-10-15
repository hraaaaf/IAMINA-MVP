import 'package:amina/data/drift/patient_weight_history_store.dart';
import 'package:amina/features/profile/d20_weight_trend_card.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';

const _idA = '123e4567-e89b-42d3-a456-426614174000';
const _idB = '123e4567-e89b-42d3-a456-426614174001';

LocalWeightObservation _reading({
  String id = _idA,
  int owner = 734,
  int amount = 7000,
  DateTime? at,
}) => LocalWeightObservation(
  ownerId: owner, clientUuid: id,
  valueHundredths: amount, unit: 'kg',
  kilogramsHundredths: amount,
  measuredAtUtc: at ?? DateTime.utc(2026, 10, 11, 9, 20),
  provenance: 'patient_declared',
);

Widget _app(List<LocalWeightObservation> items, {String lang = 'fr'}) =>
    MaterialApp(
      locale: Locale(lang),
      supportedLocales: const [Locale('fr'), Locale('en'), Locale('ar')],
      localizationsDelegates: GlobalMaterialLocalizations.delegates,
      home: Scaffold(
        body: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 820),
            child: SingleChildScrollView(
              child: D20WeightTrendCard(
                observations: items,
                asOfUtc: DateTime.utc(2026, 10, 15, 12),
              ),
            ),
          ),
        ),
      ),
    );

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('D20 trend 0/1 samples fail closed, never invent kg delta',
      (tester) async {
    await tester.pumpWidget(_app(const []));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('d20-weight-trend-unavailable')),
        findsOneWidget);
    expect(find.byKey(const Key('d20-weight-trend-delta')), findsNothing);
    await tester.pumpWidget(_app([_reading()]));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('d20-weight-trend-unavailable')),
        findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('D20 FR shows source-bound descriptive +2,50 kg and dates',
      (tester) async {
    await tester.pumpWidget(_app([
      _reading(id: _idB, amount: 7250,
          at: DateTime.utc(2026, 10, 14, 9, 20)),
      _reading(),
    ]));
    await tester.pumpAndSettle();
    expect(find.text('+2,50 kg'), findsOneWidget);
    expect(find.byKey(const Key('d20-weight-trend-period')),
        findsOneWidget);
    expect(find.byKey(const Key('d20-weight-trend-source')),
        findsOneWidget);
    expect(find.textContaining('traitement'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('D20 English negative signed difference is not an alert',
      (tester) async {
    await tester.pumpWidget(_app([
      _reading(amount: 7250),
      _reading(id: _idB, amount: 7000,
          at: DateTime.utc(2026, 10, 14)),
    ], lang: 'en'));
    await tester.pumpAndSettle();
    expect(find.text('−2.50 kg'), findsOneWidget);
    expect(find.textContaining('Does not change treatment'), findsOneWidget);
    expect(find.textContaining('dangerous'), findsNothing);
  });

  testWidgets('D20 refuses mixed patient and ambiguous time on surface',
      (tester) async {
    await tester.pumpWidget(_app([
      _reading(), _reading(id: _idB, owner: 812,
          at: DateTime.utc(2026, 10, 14)),
    ]));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('d20-weight-trend-delta')), findsNothing);
    await tester.pumpWidget(_app([
      _reading(), _reading(id: _idB),
    ]));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('d20-weight-trend-unavailable')),
        findsOneWidget);
  });

  testWidgets('D20 Arabic RTL descriptive content and numerical readability',
      (tester) async {
    await tester.pumpWidget(_app([
      _reading(),
      _reading(id: _idB, amount: 7250,
          at: DateTime.utc(2026, 10, 14)),
    ], lang: 'ar'));
    await tester.pumpAndSettle();
    expect(find.text('+2.50 kg'), findsOneWidget);
    expect(find.textContaining('معلومة وصفية'), findsOneWidget);
    final numeric = tester.widget<Text>(
      find.byKey(const Key('d20-weight-trend-delta')),
    );
    expect(numeric.textDirection, TextDirection.ltr);
    expect(tester.takeException(), isNull);
  });

  testWidgets('D20 card fits 390, 430, 768, 1280 without overflow',
      (tester) async {
    final items = [_reading(), _reading(id: _idB, amount: 7250,
        at: DateTime.utc(2026, 10, 14))];
    for (final width in <double>[390, 430, 768, 1280]) {
      tester.view.devicePixelRatio = 1;
      tester.view.physicalSize = Size(width, 932);
      await tester.pumpWidget(_app(items));
      await tester.pumpAndSettle();
      expect(find.byKey(const Key('d20-weight-trend-card')), findsOneWidget);
      expect(tester.takeException(), isNull);
      await tester.pumpWidget(const SizedBox.shrink());
      await tester.pump();
    }
    tester.view.resetPhysicalSize();
    tester.view.resetDevicePixelRatio();
  });
}
