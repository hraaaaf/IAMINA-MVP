import 'package:amina/core/data/meal_food_catalog.dart';
import 'package:amina/features/journal/widgets/food_pictogram.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter_batch2.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter_batch3.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter_batch4.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter_batch5.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter_batch6.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter_batch7.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter_batch8.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter_batch9.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter_batch10.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter_batch11.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';

Finder _batch11Art() => find.byWidgetPredicate(
  (widget) => widget is CustomPaint && widget.painter is FoodPictogramPainterBatch11,
);

void main() {
  test('batch 11 covers exact manifest-derived 24 and native union 264', () {
    const expected = <String>{
      'flax_seeds', 'sunflower_seeds', 'hazelnuts', 'walnuts', 'cashews',
      'pistachios', 'almond_butter', 'sesame', 'chermoula', 'harissa',
      'argan_oil', 'sunflower_oil', 'ketchup', 'mayonnaise', 'olives',
      'barbecue_sauce', 'hot_sauce', 'soy_sauce', 'garlic_sauce', 'tahini',
      'ayran', 'energy_drink', 'coffee', 'water',
    };
    expect(codeFoodPictogramBatch11Ids, expected);
    final previous = <String>{
      ...codeFoodPictogramIds, ...codeFoodPictogramBatch2Ids,
      ...codeFoodPictogramBatch3Ids, ...codeFoodPictogramBatch4Ids,
      ...codeFoodPictogramBatch5Ids, ...codeFoodPictogramBatch6Ids,
      ...codeFoodPictogramBatch7Ids, ...codeFoodPictogramBatch8Ids,
      ...codeFoodPictogramBatch9Ids, ...codeFoodPictogramBatch10Ids,
    };
    expect(codeFoodPictogramBatch11Ids.intersection(previous), isEmpty);
    for (final id in codeFoodPictogramBatch11Ids) {
      expect(mealFoodById(id), isNotNull, reason: 'Missing catalog food: $id');
    }
    expect(<String>{...previous, ...codeFoodPictogramBatch11Ids}.length, 264);
  });

  testWidgets('batch 11 renders drink art with localized semantics', (tester) async {
    final item = mealFoodById('coffee')!;
    await tester.pumpWidget(MaterialApp(
      locale: const Locale('fr'),
      supportedLocales: const <Locale>[Locale('fr')],
      localizationsDelegates: GlobalMaterialLocalizations.delegates,
      home: Scaffold(body: FoodPictogram(item: item, size: 48)),
    ));
    await tester.pumpAndSettle();
    expect(find.text(item.visual), findsNothing);
    expect(_batch11Art(), findsOneWidget);
    expect(tester.getSemantics(find.byType(FoodPictogram)).label, contains('Café'));
  });

  testWidgets('first post-batch-11 item keeps emoji fallback', (tester) async {
    final item = mealFoodById('coconut_water')!;
    await tester.pumpWidget(MaterialApp(
      locale: const Locale('fr'),
      supportedLocales: const <Locale>[Locale('fr')],
      localizationsDelegates: GlobalMaterialLocalizations.delegates,
      home: Scaffold(body: FoodPictogram(item: item)),
    ));
    await tester.pumpAndSettle();
    expect(find.text(item.visual), findsOneWidget);
    expect(_batch11Art(), findsNothing);
  });
}
