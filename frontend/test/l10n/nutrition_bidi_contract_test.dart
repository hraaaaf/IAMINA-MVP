import 'package:amina/core/data/nutrition_catalog.dart';
import 'package:amina/features/journal/widgets/nutrition_portion_editor.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:amina/l10n/app_localizations_ar.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets(
    'CAL-11 renders source-backed 100g apple range in FR EN AR across viewports',
    (tester) async {
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      const expected = <String, String>{
        'fr': '≈ 14.1–15.7 g de glucides',
        'en': '≈ 14.1–15.7 g carbohydrates',
        'ar': '≈ \u206614.1–15.7\u2069 غ كربوهيدرات',
      };
      expect(estimateCarbsForGrams('apple', 100)!.low, 14.1);
      expect(estimateCarbsForGrams('apple', 100)!.high, 15.7);

      for (final locale in const <Locale>[
        Locale('fr'),
        Locale('en'),
        Locale('ar'),
      ]) {
        for (final viewport in const <Size>[
          Size(390, 844),
          Size(768, 1024),
          Size(1280, 900),
        ]) {
          tester.view.devicePixelRatio = 1;
          tester.view.physicalSize = viewport;
          await tester.pumpWidget(
            MaterialApp(
              locale: locale,
              localizationsDelegates: AppLocalizations.localizationsDelegates,
              supportedLocales: AppLocalizations.supportedLocales,
              home: Scaffold(
                body: SingleChildScrollView(
                  child: NutritionPortionEditor(
                    selectedFoodIds: const <String>['apple'],
                    selections: const <String, MealPortionSelection>{
                      'apple': MealPortionSelection(
                        foodId: 'apple',
                        grams: 100,
                      ),
                    },
                    onChanged: (_) {},
                  ),
                ),
              ),
            ),
          );
          await tester.pumpAndSettle();
          final range = find.byKey(const Key('nutrition-carbs-apple'));
          expect(range, findsOneWidget);
          final rendered = tester.widget<Text>(range).data;
          expect(
            rendered,
            expected[locale.languageCode],
            reason: '${locale.languageCode} at ${viewport.width}x${viewport.height}',
          );
          expect(
            find.textContaining('USDA Agricultural Research Service'),
            findsOneWidget,
          );
          if (locale.languageCode == 'ar') {
            expect(
              Directionality.of(tester.element(range)),
              TextDirection.rtl,
            );
          }
          expect(tester.takeException(), isNull);
        }
      }
    },
  );

  testWidgets('Arabic nutrition range keeps low-to-high order', (tester) async {
    late String rendered;
    await tester.pumpWidget(
      MaterialApp(
        home: Builder(
          builder: (context) {
            rendered = formatLocalizedCarbRange(
              AppLocalizationsAr(),
              const Locale('ar'),
              '22.1',
              '26.4',
            );
            return const SizedBox.shrink();
          },
        ),
      ),
    );
    expect(
      rendered,
      contains(
        '${String.fromCharCode(0x2066)}22.1–26.4${String.fromCharCode(0x2069)}',
      ),
    );
    expect(rendered, isNot(contains('26.4–22.1')));
  });
}
