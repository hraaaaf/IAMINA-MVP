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
      child: const AddLogSheet(isPage: true),
    ),
  ),
);

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
  await tester.tap(find.byKey(const Key('add-meal-button')));
  await tester.pumpAndSettle();
  await tester.enterText(
    find.byKey(const Key('meal-food-search')),
    locale.languageCode == 'ar' ? 'موز' : 'banana',
  );
  await tester.pumpAndSettle();
  await tester.tap(find.byKey(const Key('meal-search-banana')));
  await tester.pumpAndSettle();
  await tester.ensureVisible(find.byKey(const Key('nutrition-food-banana')));
  await tester.pumpAndSettle();
  await tester.tap(find.byKey(const Key('nutrition-banana-one_peeled')));
  await tester.pumpAndSettle();
  await tester.ensureVisible(find.byKey(const Key('nutrition-carbs-banana')));
  await tester.pumpAndSettle();
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
      expect(find.textContaining('22.1'), findsOneWidget);
      expect(find.textContaining('26.5'), findsOneWidget);
      expect(nutritionProfileFor('banana'), isNotNull);
      await expectLater(
        find.byType(MaterialApp),
        matchesGoldenFile('goldens/${item.$1}.png'),
      );
    });
  }
}
