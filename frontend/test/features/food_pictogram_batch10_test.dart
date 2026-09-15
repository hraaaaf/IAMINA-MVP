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
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';

Finder _batch10Art() => find.byWidgetPredicate(
  (widget) => widget is CustomPaint && widget.painter is FoodPictogramPainterBatch10,
  description: 'Batch 10 food pictogram art',
);

void main() {
  test('batch 10 covers exact manifest-derived 24 and native union 240', () {
    const expected = <String>{
      'guava', 'pomegranate', 'kiwi', 'mandarin', 'mango', 'melon',
      'blueberry', 'nectarine', 'coconut', 'orange_cinnamon', 'grapefruit',
      'papaya', 'watermelon', 'pear', 'plum', 'prunes', 'peach', 'grapes',
      'raisins', 'fruit_salad', 'almonds', 'peanut_butter', 'peanuts',
      'chia_seeds',
    };
    expect(codeFoodPictogramBatch10Ids, expected);
    expect(codeFoodPictogramBatch10Ids.length, 24);

    final previous = <String>{
      ...codeFoodPictogramIds,
      ...codeFoodPictogramBatch2Ids,
      ...codeFoodPictogramBatch3Ids,
      ...codeFoodPictogramBatch4Ids,
      ...codeFoodPictogramBatch5Ids,
      ...codeFoodPictogramBatch6Ids,
      ...codeFoodPictogramBatch7Ids,
      ...codeFoodPictogramBatch8Ids,
      ...codeFoodPictogramBatch9Ids,
    };
    expect(codeFoodPictogramBatch10Ids.intersection(previous), isEmpty);
    for (final id in codeFoodPictogramBatch10Ids) {
      expect(mealFoodById(id), isNotNull, reason: 'Missing catalog food: $id');
    }
    expect(<String>{...previous, ...codeFoodPictogramBatch10Ids}.length, 240);
  });

  testWidgets('batch 10 renders fruit art with localized semantics', (tester) async {
    final item = mealFoodById('watermelon')!;
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
    expect(_batch10Art(), findsOneWidget);
    expect(tester.getSemantics(find.byType(FoodPictogram)).label, contains('Pastèque'));
  });

  testWidgets('current post-batch-12 item keeps emoji fallback', (tester) async {
    final item = mealFoodById('cake')!;
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
    expect(_batch10Art(), findsNothing);
  });
}
