import 'package:amina/core/data/meal_food_catalog.dart';
import 'package:amina/features/journal/widgets/food_pictogram.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter_batch2.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter_batch3.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter_batch4.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter_batch5.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter_batch6.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';

Finder _batch6Art() => find.byWidgetPredicate(
  (widget) => widget is CustomPaint && widget.painter is FoodPictogramPainterBatch6,
  description: 'Batch 6 food pictogram art',
);

void main() {
  test('batch 6 covers the exact manifest-derived 24 and native union 144', () {
    const expected = <String>{
      'shawarma_beef', 'shuwa', 'tabbouleh', 'lamb', 'chicken_breast',
      'minced_beef', 'lamb_chops', 'turkey', 'liver', 'kefta', 'merguez',
      'roast_chicken', 'sausage', 'beef_steak', 'veal', 'sea_bass', 'squid',
      'crab', 'shrimp', 'sea_bream', 'prawns', 'mackerel', 'hake', 'mussels',
    };
    expect(codeFoodPictogramBatch6Ids, expected);
    expect(codeFoodPictogramBatch6Ids.length, 24);

    final previous = <String>{
      ...codeFoodPictogramIds,
      ...codeFoodPictogramBatch2Ids,
      ...codeFoodPictogramBatch3Ids,
      ...codeFoodPictogramBatch4Ids,
      ...codeFoodPictogramBatch5Ids,
    };
    expect(codeFoodPictogramBatch6Ids.intersection(previous), isEmpty);
    for (final id in codeFoodPictogramBatch6Ids) {
      expect(mealFoodById(id), isNotNull, reason: 'Missing catalog food: $id');
    }
    expect(<String>{...previous, ...codeFoodPictogramBatch6Ids}.length, 144);
  });

  testWidgets('batch 6 renders native art with localized semantics', (tester) async {
    final item = mealFoodById('beef_steak')!;
    await tester.pumpWidget(
      MaterialApp(
        locale: const Locale('fr'),
        supportedLocales: const <Locale>[Locale('fr')],
        localizationsDelegates: GlobalMaterialLocalizations.delegates,
        home: Scaffold(body: FoodPictogram(item: item, size: 48)),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text(item.visual), findsNothing);
    expect(_batch6Art(), findsOneWidget);
    expect(
      tester.widget<CustomPaint>(_batch6Art()).painter,
      isA<FoodPictogramPainterBatch6>(),
    );
    expect(tester.getSemantics(find.byType(FoodPictogram)).label, contains('Steak de bœuf'));
  });

  testWidgets('synthetic outside-catalog item keeps emoji fallback after full coverage', (tester) async {
    const item = MealFoodItem(
      '__fallback_probe__',
      'Probe fallback',
      'Fallback probe',
      'اختبار',
      visual: '🍽️',
    );
    await tester.pumpWidget(
      MaterialApp(
        locale: const Locale('fr'),
        supportedLocales: const <Locale>[Locale('fr')],
        localizationsDelegates: GlobalMaterialLocalizations.delegates,
        home: Scaffold(body: FoodPictogram(item: item)),
      ),
    );
    await tester.pumpAndSettle();

    expect(mealFoodById(item.id), isNull);
    expect(find.text(item.visual), findsOneWidget);
    expect(_batch6Art(), findsNothing);
  });
}