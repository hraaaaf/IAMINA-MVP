import 'dart:io';
import 'dart:typed_data';

import 'package:amina/data/models/personal_response_models.dart';
import 'package:amina/features/journal/widgets/personal_response_section.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

const _boundaryKey = Key('p2-j8-visual-boundary');
const _auditFontFamily = 'AuditSans';

Future<void> _loadAuditFont() async {
  final bytes = await File(
    '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
  ).readAsBytes();
  final loader = FontLoader(_auditFontFamily);
  loader.addFont(Future<ByteData>.value(ByteData.sublistView(bytes)));
  await loader.load();
}

PersonalResponseResult _ready() => const PersonalResponseResult(
      status: 'ready',
      dataScope: 'server_synced_logs',
      windowDays: 90,
      totalReadings: 28,
      distinctDays: 18,
      windowMedianGlucoseMgDl: 142,
      minimumObservations: 3,
      minimumDistinctDays: 2,
      confidenceDefinition: 'descriptive repeatability only',
      causalityNotice: 'association only',
      patterns: [
        PersonalResponsePattern(
          key: 'context:stress',
          kind: 'context',
          observations: 8,
          distinctDays: 6,
          medianGlucoseMgDl: 158,
          windowMedianGlucoseMgDl: 142,
          confidence: 'strong',
        ),
        PersonalResponsePattern(
          key: 'meal:lunch',
          kind: 'meal',
          observations: 6,
          distinctDays: 4,
          medianGlucoseMgDl: 151,
          windowMedianGlucoseMgDl: 142,
          confidence: 'moderate',
        ),
        PersonalResponsePattern(
          key: 'context:poor_sleep',
          kind: 'context',
          observations: 3,
          distinctDays: 2,
          medianGlucoseMgDl: 149,
          windowMedianGlucoseMgDl: 142,
          confidence: 'limited',
        ),
      ],
    );

PersonalResponseResult _insufficient() => const PersonalResponseResult(
      status: 'insufficient_data',
      dataScope: 'server_synced_logs',
      windowDays: 90,
      totalReadings: 2,
      distinctDays: 2,
      windowMedianGlucoseMgDl: null,
      minimumObservations: 3,
      minimumDistinctDays: 2,
      confidenceDefinition: 'descriptive repeatability only',
      causalityNotice: 'association only',
      patterns: [],
    );

Widget _host({
  required Locale locale,
  required PersonalResponseResult result,
}) {
  return MaterialApp(
    locale: locale,
    theme: ThemeData(fontFamily: _auditFontFamily),
    localizationsDelegates: AppLocalizations.localizationsDelegates,
    supportedLocales: AppLocalizations.supportedLocales,
    home: Scaffold(
      backgroundColor: const Color(0xFFF7FAFA),
      body: RepaintBoundary(
        key: _boundaryKey,
        child: SingleChildScrollView(
          child: Padding(
            padding: const EdgeInsetsDirectional.fromSTEB(20, 24, 20, 24),
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

Future<void> _setSize(WidgetTester tester, Size size) async {
  tester.view.physicalSize = size;
  tester.view.devicePixelRatio = 1;
  addTearDown(() {
    tester.view.resetPhysicalSize();
    tester.view.resetDevicePixelRatio();
  });
}

void main() {
  setUpAll(_loadAuditFont);

  final cases = <(String, Locale, Size)>[
    ('fr-desktop-1440x1000', const Locale('fr'), const Size(1440, 1000)),
    ('fr-tablet-768x1024', const Locale('fr'), const Size(768, 1024)),
    ('fr-mobile-390x844', const Locale('fr'), const Size(390, 844)),
    ('fr-small-360x560', const Locale('fr'), const Size(360, 560)),
    ('ar-desktop-1440x1000', const Locale('ar'), const Size(1440, 1000)),
    ('ar-tablet-768x1024', const Locale('ar'), const Size(768, 1024)),
    ('ar-mobile-390x844', const Locale('ar'), const Size(390, 844)),
    ('ar-small-360x560', const Locale('ar'), const Size(360, 560)),
  ];

  for (final item in cases) {
    testWidgets('ready max-density ${item.$1}', (tester) async {
      await _setSize(tester, item.$3);
      await tester.pumpWidget(_host(locale: item.$2, result: _ready()));
      await tester.pumpAndSettle();

      expect(find.byType(PersonalResponseSection), findsOneWidget);
      expect(find.textContaining('158'), findsOneWidget);
      expect(tester.takeException(), isNull);
      await expectLater(
        find.byKey(_boundaryKey),
        matchesGoldenFile('goldens/p2j8-ready-${item.$1}.png'),
      );
    });

    testWidgets('insufficient ${item.$1}', (tester) async {
      await _setSize(tester, item.$3);
      await tester.pumpWidget(_host(locale: item.$2, result: _insufficient()));
      await tester.pumpAndSettle();

      expect(find.byType(PersonalResponseSection), findsOneWidget);
      expect(tester.takeException(), isNull);
      await expectLater(
        find.byKey(_boundaryKey),
        matchesGoldenFile('goldens/p2j8-insufficient-${item.$1}.png'),
      );
    });
  }
}
