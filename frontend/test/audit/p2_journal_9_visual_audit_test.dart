import 'dart:io';
import 'dart:typed_data';

import 'package:amina/features/journal/widgets/post_save_receipt.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

const _boundaryKey = Key('p2-j9-visual-boundary');
const _auditFontFamily = 'AuditSans';

Future<void> _loadAuditFonts() async {
  final bytes = await File(
    '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
  ).readAsBytes();
  for (final family in <String>[_auditFontFamily, 'Roboto', 'Ahem']) {
    final loader = FontLoader(family);
    loader.addFont(Future<ByteData>.value(ByteData.sublistView(bytes)));
    await loader.load();
  }

  final flutterRoot = Platform.environment['FLUTTER_ROOT'];
  if (flutterRoot == null) {
    throw StateError('FLUTTER_ROOT is required for Material icon audit font');
  }
  final iconBytes = await File(
    '$flutterRoot/bin/cache/artifacts/material_fonts/MaterialIcons-Regular.otf',
  ).readAsBytes();
  final iconLoader = FontLoader('MaterialIcons');
  iconLoader.addFont(
    Future<ByteData>.value(ByteData.sublistView(iconBytes)),
  );
  await iconLoader.load();
}

Widget _host({required Locale locale, required bool rich}) {
  return MaterialApp(
    locale: locale,
    theme: ThemeData(fontFamily: _auditFontFamily),
    localizationsDelegates: AppLocalizations.localizationsDelegates,
    supportedLocales: AppLocalizations.supportedLocales,
    home: Builder(
      builder: (context) {
        final l10n = AppLocalizations.of(context)!;
        final data = PostSaveReceiptData(
          glucose: 126,
          unit: 'mg/dL',
          timeLabel: '${l10n.journalToday} · 13:05',
          measurementContextLabel: rich ? l10n.journalContextPostMeal : null,
          mealTypeLabel: rich ? l10n.journalMealLunch : null,
          insulinUnits: rich ? 2.5 : null,
          additionalContextLabels: rich
              ? <String>[
                  l10n.journalUnusualStress,
                  l10n.journalPhysicalActivity,
                  l10n.journalPoorSleep,
                ]
              : const <String>[],
        );
        return Scaffold(
          body: RepaintBoundary(
            key: _boundaryKey,
            child: PostSaveReceipt(
              data: data,
              onViewJournal: () {},
              onAddAnother: () {},
              onDone: () {},
            ),
          ),
        );
      },
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
  setUpAll(_loadAuditFonts);

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
    testWidgets('minimal receipt ${item.$1}', (tester) async {
      await _setSize(tester, item.$3);
      await tester.pumpWidget(_host(locale: item.$2, rich: false));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('post-save-view-journal')), findsOneWidget);
      expect(find.textContaining('126 mg/dL'), findsOneWidget);
      expect(tester.takeException(), isNull);
      await expectLater(
        find.byKey(_boundaryKey),
        matchesGoldenFile('goldens/p2j9-minimal-${item.$1}.png'),
      );
    });

    testWidgets('rich receipt ${item.$1}', (tester) async {
      await _setSize(tester, item.$3);
      await tester.pumpWidget(_host(locale: item.$2, rich: true));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('post-save-add-another')), findsOneWidget);
      expect(find.textContaining('2.5 U'), findsOneWidget);
      expect(tester.takeException(), isNull);
      await expectLater(
        find.byKey(_boundaryKey),
        matchesGoldenFile('goldens/p2j9-rich-${item.$1}.png'),
      );
    });
  }
}
