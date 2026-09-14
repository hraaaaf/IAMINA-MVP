import 'package:amina/core/data/meal_food_catalog.dart';
import 'package:amina/features/journal/widgets/food_pictogram.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter_batch2.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter_batch3.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter_batch4.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter_batch5.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter_batch6.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter_batch7.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';

Finder _batch7Art() => find.byWidgetPredicate(
  (widget) => widget is CustomPaint && widget.painter is FoodPictogramPainterBatch7,
  description: 'Batch 7 food pictogram art',
);

void main() {
  test('batch 7 covers the exact manifest-derived 24 and native union 168', () {
    const expected = <String>{
      'fish', 'octopus', 'tuna', 'omelette', 'fried_egg', 'boiled_egg',
      'butter', 'cream', 'feta', 'cheese', 'processed_cheese', 'fresh_cheese',
      'cream_cheese', 'halloumi', 'laban', 'labneh', 'camel_milk',
      'semi_skimmed_milk', 'whole_milk', 'skimmed_milk', 'mozzarella',
      'qishta', 'raib', 'yogurt',
    };
    expect(codeFoodPictogramBatch7Ids, expected);
    expect(codeFoodPictogramBatch7Ids.length, 24);

    final previous = <String>{
      ...codeFoodPictogramIds,
      ...codeFoodPictogramBatch2Ids,
      ...codeFoodPictogramBatch3Ids,
      ...codeFoodPictogramBatch4Ids,
      ...codeFoodPictogramBatch5Ids,
      ...codeFoodPictogramBatch6Ids,
    };
    expect(codeFoodPictogramBatch7Ids.intersection(previous), isEmpty);
    for (final id in codeFoodPictogramBatch7Ids) {
      expect(mealFoodById(id), isNotNull, reason: 'Missing catalog food: $id');
    }
    expect(<String>{...previous, ...codeFoodPictogramBatch7Ids}.length, 168);
  });

  testWidgets('batch 7 renders dairy art with localized semantics', (tester) async {
    final item = mealFoodById('whole_milk')!;
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
    expect(_batch7Art(), findsOneWidget);
    expect(
      tester.widget<CustomPaint>(_batch7Art()).painter,
      isA<FoodPictogramPainterBatch7>(),
    );
    expect(tester.getSemantics(find.byType(FoodPictogram)).label, contains('Lait entier'));
  });

  testWidgets('first post-batch-7 dairy item keeps emoji fallback', (tester) async {
    final item = mealFoodById('greek_yogurt')!;
    await tester.pumpWidget(
      MaterialApp(
        locale: const Locale('fr'),
        supportedLocales: const <Locale>[Locale('fr')],
        localizationsDelegates: GlobalMaterialLocalizations.delegates,
        home: Scaffold(body: FoodPictogram(item: item)),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text(item.visual), findsOneWidget);
    expect(_batch7Art(), findsNothing);
  });
}
