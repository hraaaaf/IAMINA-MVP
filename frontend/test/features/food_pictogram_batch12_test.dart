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
import 'package:amina/features/journal/widgets/food_pictogram_painter_batch12.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';

Finder _batch12Art() => find.byWidgetPredicate(
  (widget) => widget is CustomPaint && widget.painter is FoodPictogramPainterBatch12,
);

void main() {
  test('batch 12 covers exact manifest-derived 24 and native union 288', () {
    const expected = <String>{
      'coconut_water', 'sparkling_water', 'juice', 'orange_juice', 'apple_juice',
      'milkshake', 'protein_shake', 'smoothie', 'soft_drink', 'diet_soft_drink',
      'black_tea', 'green_tea', 'baklava', 'basbousa', 'cookie', 'chebakia',
      'chocolate', 'dark_chocolate', 'jam', 'gazelle_horns', 'croissant',
      'atayef_moroccan', 'ghriyba', 'ice_cream',
    };
    expect(codeFoodPictogramBatch12Ids, expected);
    expect(codeFoodPictogramBatch12Ids.length, 24);

    final previous = <String>{
      ...codeFoodPictogramIds, ...codeFoodPictogramBatch2Ids,
      ...codeFoodPictogramBatch3Ids, ...codeFoodPictogramBatch4Ids,
      ...codeFoodPictogramBatch5Ids, ...codeFoodPictogramBatch6Ids,
      ...codeFoodPictogramBatch7Ids, ...codeFoodPictogramBatch8Ids,
      ...codeFoodPictogramBatch9Ids, ...codeFoodPictogramBatch10Ids,
      ...codeFoodPictogramBatch11Ids,
    };
    expect(codeFoodPictogramBatch12Ids.intersection(previous), isEmpty);
    for (final id in codeFoodPictogramBatch12Ids) {
      expect(mealFoodById(id), isNotNull, reason: 'Missing catalog food: $id');
    }
    expect(<String>{...previous, ...codeFoodPictogramBatch12Ids}.length, 288);
  });

  testWidgets('batch 12 renders dessert art with localized semantics', (tester) async {
    final item = mealFoodById('chocolate')!;
    await tester.pumpWidget(MaterialApp(
      locale: const Locale('fr'),
      supportedLocales: const <Locale>[Locale('fr')],
      localizationsDelegates: GlobalMaterialLocalizations.delegates,
      home: Scaffold(body: FoodPictogram(item: item, size: 48)),
    ));
    await tester.pumpAndSettle();
    expect(find.text(item.visual), findsNothing);
    expect(_batch12Art(), findsOneWidget);
    expect(tester.getSemantics(find.byType(FoodPictogram)).label, contains('Chocolat'));
  });

  testWidgets('first post-batch-12 item keeps emoji fallback', (tester) async {
    final item = mealFoodById('cake')!;
    await tester.pumpWidget(MaterialApp(
      locale: const Locale('fr'),
      supportedLocales: const <Locale>[Locale('fr')],
      localizationsDelegates: GlobalMaterialLocalizations.delegates,
      home: Scaffold(body: FoodPictogram(item: item)),
    ));
    await tester.pumpAndSettle();
    expect(find.text(item.visual), findsOneWidget);
    expect(_batch12Art(), findsNothing);
  });
}
