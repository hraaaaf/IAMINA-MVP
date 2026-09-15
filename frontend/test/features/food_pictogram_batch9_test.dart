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
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';

Finder _batch9Art() => find.byWidgetPredicate(
  (widget) => widget is CustomPaint && widget.painter is FoodPictogramPainterBatch9,
  description: 'Batch 9 food pictogram art',
);

void main() {
  test('batch 9 covers exact manifest-derived 24 and native union 216', () {
    const expected = <String>{
      'lettuce', 'vegetables', 'mint', 'turnip', 'onion', 'sweet_potato',
      'parsley', 'bell_pepper', 'salad', 'spinach', 'apricot',
      'dried_apricots', 'pineapple', 'avocado', 'cherry', 'lemon',
      'clementine', 'khalas_dates', 'medjool_dates', 'sukkari_dates',
      'fig', 'dried_figs', 'strawberry', 'raspberry',
    };
    expect(codeFoodPictogramBatch9Ids, expected);
    expect(codeFoodPictogramBatch9Ids.length, 24);

    final previous = <String>{
      ...codeFoodPictogramIds,
      ...codeFoodPictogramBatch2Ids,
      ...codeFoodPictogramBatch3Ids,
      ...codeFoodPictogramBatch4Ids,
      ...codeFoodPictogramBatch5Ids,
      ...codeFoodPictogramBatch6Ids,
      ...codeFoodPictogramBatch7Ids,
      ...codeFoodPictogramBatch8Ids,
    };
    expect(codeFoodPictogramBatch9Ids.intersection(previous), isEmpty);
    for (final id in codeFoodPictogramBatch9Ids) {
      expect(mealFoodById(id), isNotNull, reason: 'Missing catalog food: $id');
    }
    expect(<String>{...previous, ...codeFoodPictogramBatch9Ids}.length, 216);
  });

  testWidgets('batch 9 renders fruit art with localized semantics', (tester) async {
    final item = mealFoodById('strawberry')!;
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
    expect(_batch9Art(), findsOneWidget);
    expect(tester.getSemantics(find.byType(FoodPictogram)).label, contains('Fraise'));
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
    expect(_batch9Art(), findsNothing);
  });
}
