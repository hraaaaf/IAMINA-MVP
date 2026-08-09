import 'package:amina/core/data/nutrition_catalog.dart';
import 'package:amina/data/drift/database.dart';
import 'package:amina/features/dashboard/widgets/add_log_sheet.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

Widget _sheet(AppDatabase db, Locale locale) => MaterialApp(
  locale: locale,
  localizationsDelegates: AppLocalizations.localizationsDelegates,
  supportedLocales: AppLocalizations.supportedLocales,
  home: Scaffold(
    body: MultiProvider(
      providers: [
        Provider<AppDatabase>.value(value: db),
        Provider<PatientProfileData?>.value(value: null),
      ],
      child: const RepaintBoundary(
        key: Key('visual-audit-boundary'),
        child: AddLogSheet(isPage: true),
      ),
    ),
  ),
);

Future<void> _visible(WidgetTester tester, Finder finder) async {
  await tester.ensureVisible(finder);
  await tester.pumpAndSettle();
}

Future<void> _prepare(WidgetTester tester, Locale locale, Size size) async {
  tester.view.physicalSize = size;
  tester.view.devicePixelRatio = 1;
  final db = AppDatabase(NativeDatabase.memory());
  addTearDown(() async {
    tester.view.resetPhysicalSize();
    tester.view.resetDevicePixelRatio();
    await db.close();
  });
  await tester.pumpWidget(_sheet(db, locale));
  await tester.pumpAndSettle();

  final addMeal = find.byKey(const Key('add-meal-button'));
  await _visible(tester, addMeal);
  await tester.tap(addMeal);
  await tester.pumpAndSettle();

  final search = find.byKey(const Key('meal-food-search'));
  await _visible(tester, search);
  await tester.enterText(search, locale.languageCode == 'ar' ? 'موز' : 'banana');
  await tester.pumpAndSettle();

  final banana = find.byKey(const Key('meal-search-banana'));
  await _visible(tester, banana);
  await tester.tap(banana);
  await tester.pumpAndSettle();

  final card = find.byKey(const Key('nutrition-food-banana'));
  await _visible(tester, card);

  final portion = find.byKey(const Key('nutrition-banana-one_peeled'));
  await _visible(tester, portion);
  await tester.tap(portion);
  await tester.pumpAndSettle();

  await _visible(tester, find.byKey(const Key('nutrition-carbs-banana')));
}

void main() {
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
    testWidgets('render ${item.$1}', (tester) async {
      await _prepare(tester, item.$2, item.$3);
      expect(find.byKey(const Key('nutrition-carbs-banana')), findsOneWidget);
      expect(nutritionProfileFor('banana'), isNotNull);
      await expectLater(
        find.byKey(const Key('visual-audit-boundary')),
        matchesGoldenFile('goldens/${item.$1}.png'),
      );
    });
  }
}
