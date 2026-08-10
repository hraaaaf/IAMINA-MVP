import 'package:amina/data/models/personal_response_models.dart';
import 'package:amina/features/journal/widgets/personal_response_section.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

PersonalResponseResult _readyResult() {
  return const PersonalResponseResult(
    status: 'ready',
    dataScope: 'server_synced_logs',
    windowDays: 90,
    totalReadings: 12,
    distinctDays: 8,
    windowMedianGlucoseMgDl: 142,
    minimumObservations: 3,
    minimumDistinctDays: 2,
    confidenceDefinition: 'descriptive only',
    causalityNotice: 'no causality',
    patterns: [
      PersonalResponsePattern(
        key: 'context:stress',
        kind: 'context',
        observations: 5,
        distinctDays: 4,
        medianGlucoseMgDl: 156,
        windowMedianGlucoseMgDl: 142,
        confidence: 'moderate',
      ),
    ],
  );
}

PersonalResponseResult _insufficientResult() {
  return const PersonalResponseResult(
    status: 'insufficient_data',
    dataScope: 'server_synced_logs',
    windowDays: 90,
    totalReadings: 2,
    distinctDays: 2,
    windowMedianGlucoseMgDl: null,
    minimumObservations: 3,
    minimumDistinctDays: 2,
    confidenceDefinition: 'descriptive only',
    causalityNotice: 'no causality',
    patterns: [],
  );
}

Widget _host({required Locale locale, required PersonalResponseResult result}) {
  return MaterialApp(
    locale: locale,
    localizationsDelegates: AppLocalizations.localizationsDelegates,
    supportedLocales: AppLocalizations.supportedLocales,
    home: Scaffold(
      body: SingleChildScrollView(
        child: SizedBox(
          width: 360,
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: PersonalResponseSection(
              unit: 'mg/dL',
              loader: () async => result,
            ),
          ),
        ),
      ),
    ),
  );
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('FR ready state is truthful and usable at 360x560', (tester) async {
    tester.view.physicalSize = const Size(360, 560);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(
      _host(locale: const Locale('fr'), result: _readyResult()),
    );
    await tester.pumpAndSettle();

    expect(find.text('Réponses personnelles'), findsOneWidget);
    expect(find.text('Stress signalé'), findsOneWidget);
    expect(find.textContaining('Association observée'), findsOneWidget);
    expect(find.textContaining('données synchronisées'), findsWidgets);
    expect(tester.takeException(), isNull);
  });

  testWidgets('AR ready state keeps RTL hierarchy without overflow', (tester) async {
    tester.view.physicalSize = const Size(360, 560);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(
      _host(locale: const Locale('ar'), result: _readyResult()),
    );
    await tester.pumpAndSettle();

    expect(find.text('استجابتك الشخصية'), findsOneWidget);
    expect(find.text('الضغط النفسي المسجل'), findsOneWidget);
    expect(
      Directionality.of(tester.element(find.text('استجابتك الشخصية'))),
      TextDirection.rtl,
    );
    expect(tester.takeException(), isNull);
  });

  testWidgets('insufficient state exposes product evidence threshold', (
    tester,
  ) async {
    await tester.pumpWidget(
      _host(locale: const Locale('fr'), result: _insufficientResult()),
    );
    await tester.pumpAndSettle();

    expect(find.text('Pas encore assez de répétitions'), findsOneWidget);
    expect(find.textContaining('3 observations'), findsOneWidget);
    expect(find.textContaining('2 jours'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
