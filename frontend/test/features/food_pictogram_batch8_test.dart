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
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';

Finder _batch8Art() => find.byWidgetPredicate(
  (widget) => widget is CustomPaint && widget.painter is FoodPictogramPainterBatch8,
  description: 'Batch 8 food pictogram art',
);

void main() {
  test('batch 8 covers exact manifest-derived 24 and native union 192', () {
    const expected = <String>{
      'greek_yogurt',
      'fava_beans',
      'white_beans',
      'red_beans',
      'green_peas',
      'split_peas',
      'soybeans',
      'garlic',
      'artichoke',
      'eggplant',
      'beetroot',
      'broccoli',
      'carrot',
      'mushroom',
      'cabbage',
      'cauliflower',
      'preserved_lemon',
      'cucumber',
      'coriander',
      'pumpkin',
      'zucchini',
      'celery',
      'okra',
      'green_beans',
    };
    expect(codeFoodPictogramBatch8Ids, expected);
    expect(codeFoodPictogramBatch8Ids.length, 24);

    final previous = <String>{
      ...codeFoodPictogramIds,
      ...codeFoodPictogramBatch2Ids,
      ...codeFoodPictogramBatch3Ids,
      ...codeFoodPictogramBatch4Ids,
      ...codeFoodPictogramBatch5Ids,
      ...codeFoodPictogramBatch6Ids,
      ...codeFoodPictogramBatch7Ids,
    };
    expect(codeFoodPictogramBatch8Ids.intersection(previous), isEmpty);
    for (final id in codeFoodPictogramBatch8Ids) {
      expect(mealFoodById(id), isNotNull, reason: 'Missing catalog food: $id');
    }
    expect(<String>{...previous, ...codeFoodPictogramBatch8Ids}.length, 192);
  });

  testWidgets('batch 8 renders legume art with localized semantics', (tester) async {
    final item = mealFoodById('white_beans')!;
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
    expect(_batch8Art(), findsOneWidget);
    expect(
      tester.widget<CustomPaint>(_batch8Art()).painter,
      isA<FoodPictogramPainterBatch8>(),
    );
    expect(tester.getSemantics(find.byType(FoodPictogram)).label, contains('Haricots blancs'));
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
    expect(_batch8Art(), findsNothing);
  });
}
