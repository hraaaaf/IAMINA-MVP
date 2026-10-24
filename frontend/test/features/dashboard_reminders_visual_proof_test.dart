import 'dart:io';
import 'dart:typed_data';

import 'package:amina/data/drift/database.dart';
import 'package:amina/features/dashboard/widgets/dashboard_reminders_summary_card.dart';
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart' show FontLoader;
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

/// A throwaway in-memory W03 fixture; no authenticated patient, HTTP or push.
/// This exact test file is copied into both source and candidate worktrees.
class _W03VisualFixtureDb extends AppDatabase {
  _W03VisualFixtureDb() : super(NativeDatabase.memory());

  @override
  Stream<List<ReminderData>> watchReminders() => Stream.value([
        for (var i = 0; i < 4; i++)
          ReminderData(
            id: i + 1,
            title: 'SYNTHETIC PRIVATE CLINICAL TITLE $i',
            dueAt: DateTime(2099, 1, 10 + i, 9, 30),
            enabled: true,
            createdAt: DateTime(2099, 1, 1),
          ),
        ReminderData(
          id: 5,
          title: 'SYNTHETIC PRIVATE DISABLED',
          dueAt: DateTime(2099, 1, 4),
          enabled: false,
          createdAt: DateTime(2099, 1, 1),
        ),
      ]);
}

void main() {
  // Ordinary CI runs all *_test.dart files but has no committed golden PNGs.
  // Keep golden generation exclusive to the explicit W03 visual workflow.
  const enabled = bool.fromEnvironment('IAMINA_W03_D3_GOLDEN_PROOF');
  if (!enabled) {
    test('W03 D3 golden capture is an opt-in visual harness', () {
      expect(enabled, isFalse);
    });
    return;
  }

  // Widget tests otherwise render opaque Ahem glyph blocks.
  // Use the runner's real system font for readable FR/AR evidence.
  setUpAll(() async {
    final fontPath = Platform.environment['IAMINA_W03_GOLDEN_FONT'] ??
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';
    final bytes = await File(fontPath).readAsBytes();
    final loader = FontLoader('Roboto')
      ..addFont(Future<ByteData>.value(ByteData.sublistView(bytes)));
    await loader.load();
    // The widget renderer also needs the MaterialIcons font for real symbols.
    // Unlike this test font setup, the production Flutter asset is unchanged.
    final flutterRoot = Platform.environment['FLUTTER_ROOT'];
    if (flutterRoot != null) {
      final iconFile = File(
        '${flutterRoot}/bin/cache/artifacts/material_fonts/MaterialIcons-Regular.otf',
      );
      if (iconFile.existsSync()) {
        final iconBytes = await iconFile.readAsBytes();
        final icons = FontLoader('MaterialIcons')
          ..addFont(
            Future<ByteData>.value(ByteData.sublistView(iconBytes)),
          );
        await icons.load();
      }
    }
  });

  for (final locale in const [Locale('fr'), Locale('ar')]) {
    for (final size in const [
      Size(390, 844),
      Size(430, 932),
      Size(768, 1024),
      Size(1280, 900),
    ]) {
      testWidgets(
        'W03 D3 screenshot ${locale.languageCode} ${size.width}x${size.height}',
        (tester) async {
          tester.view.physicalSize = size;
          tester.view.devicePixelRatio = 1;
          addTearDown(tester.view.resetPhysicalSize);
          addTearDown(tester.view.resetDevicePixelRatio);
          final db = _W03VisualFixtureDb();
          addTearDown(db.close);
          await tester.pumpWidget(
            Provider<AppDatabase>.value(
              value: db,
              child: MaterialApp(
                locale: locale,
                supportedLocales: const [Locale('fr'), Locale('ar')],
                localizationsDelegates: const [
                  GlobalMaterialLocalizations.delegate,
                  GlobalWidgetsLocalizations.delegate,
                  GlobalCupertinoLocalizations.delegate,
                ],
                home: Scaffold(
                  backgroundColor: const Color(0xFFF4FBF9),
                  body: RepaintBoundary(
                    key: const ValueKey('w03-d3-full-viewport-proof'),
                    child: SizedBox.expand(
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Align(
                          alignment: AlignmentDirectional.topCenter,
                          child: ConstrainedBox(
                            constraints: const BoxConstraints(maxWidth: 600),
                            child: const DashboardRemindersSummaryCard(),
                          ),
                        ),
                      ),
                    ),
                  ),
                ),
              ),
            ),
          );
          await tester.pumpAndSettle();
          expect(find.byKey(const ValueKey('dashboard-reminders-card')),
              findsOneWidget);
          expect(find.textContaining('SYNTHETIC PRIVATE'), findsNothing);
          expect(tester.takeException(), isNull);
          final file =
              'goldens/w03-d3-${locale.languageCode}-${size.width.toInt()}x${size.height.toInt()}.png';
          await expectLater(
            find.byKey(const ValueKey('w03-d3-full-viewport-proof')),
            matchesGoldenFile(file),
          );
        },
      );
    }
  }
}
