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
import 'package:amina/features/journal/widgets/food_pictogram_painter_batch13.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';

Finder _batch13Art() => find.byWidgetPredicate(
  (widget) => widget is CustomPaint && widget.painter is FoodPictogramPainterBatch13,
);

void main() {
  test('batch 13 covers exact manifest-derived 24 and native union 312', () {
    const expected = <String>{
      'cake', 'bastilla_milk', 'khanfaroosh', 'kunafa', 'maamoul', 'mhalbiya',
      'mhancha', 'honey', 'molasses', 'umm_ali', 'qatayef', 'sago_dessert',
      'date_syrup', 'stevia', 'sugar', 'brown_sugar', 'bocadillo', 'chips',
      'fries', 'hot_dog', 'nuggets', 'panini', 'popcorn', 'fried_chicken',
    };
    expect(codeFoodPictogramBatch13Ids, expected);
    expect(codeFoodPictogramBatch13Ids.length, 24);

    final previous = <String>{
      ...codeFoodPictogramIds, ...codeFoodPictogramBatch2Ids,
      ...codeFoodPictogramBatch3Ids, ...codeFoodPictogramBatch4Ids,
      ...codeFoodPictogramBatch5Ids, ...codeFoodPictogramBatch6Ids,
      ...codeFoodPictogramBatch7Ids, ...codeFoodPictogramBatch8Ids,
      ...codeFoodPictogramBatch9Ids, ...codeFoodPictogramBatch10Ids,
      ...codeFoodPictogramBatch11Ids, ...codeFoodPictogramBatch12Ids,
    };
    expect(codeFoodPictogramBatch13Ids.intersection(previous), isEmpty);
    for (final id in codeFoodPictogramBatch13Ids) {
      expect(mealFoodById(id), isNotNull, reason: 'Missing catalog food: $id');
    }
    expect(<String>{...previous, ...codeFoodPictogramBatch13Ids}.length, 312);
  });

  testWidgets('batch 13 renders fast-food art with localized semantics', (tester) async {
    final item = mealFoodById('fries')!;
    await tester.pumpWidget(MaterialApp(
      locale: const Locale('fr'),
      supportedLocales: const <Locale>[Locale('fr')],
      localizationsDelegates: GlobalMaterialLocalizations.delegates,
      home: Scaffold(body: FoodPictogram(item: item, size: 48)),
    ));
    await tester.pumpAndSettle();
    expect(find.text(item.visual), findsNothing);
    expect(_batch13Art(), findsOneWidget);
    expect(tester.getSemantics(find.byType(FoodPictogram)).label, contains('Frites'));
  });

  testWidgets('first post-batch-13 item keeps emoji fallback', (tester) async {
    final item = mealFoodById('sandwich')!;
    await tester.pumpWidget(MaterialApp(
      locale: const Locale('fr'),
      supportedLocales: const <Locale>[Locale('fr')],
      localizationsDelegates: GlobalMaterialLocalizations.delegates,
      home: Scaffold(body: FoodPictogram(item: item)),
    ));
    await tester.pumpAndSettle();
    expect(find.text(item.visual), findsOneWidget);
    expect(_batch13Art(), findsNothing);
  });
}
