import 'package:amina/core/data/food_pictogram_registry.dart';
import 'package:amina/core/data/meal_food_catalog.dart';
import 'package:amina/features/journal/widgets/food_pictogram.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

Finder _foodArtwork() => find.byWidgetPredicate(
  (widget) => widget is CustomPaint && widget.painter is FoodPictogramPainter,
  description: 'FoodPictogram CustomPaint',
);

void main() {
  testWidgets(
    'long-tail food keeps deterministic asset path and safe emoji fallback',
    (tester) async {
      final item = mealFoodById('rfissa')!;
      await tester.pumpWidget(
        MaterialApp(
          locale: const Locale('fr'),
          home: Scaffold(body: FoodPictogram(item: item)),
        ),
      );
      await tester.pumpAndSettle();

      final widget = tester.widget<FoodPictogram>(find.byType(FoodPictogram));
      expect(widget.assetPath, 'assets/food/pictograms/v1/rfissa.webp');
      expect(find.text(item.visual), findsOneWidget);
      expect(_foodArtwork(), findsNothing);

      final semantics = tester.getSemantics(find.byType(FoodPictogram));
      expect(semantics.label, contains('Rfissa'));
    },
  );

  testWidgets('batch 1 renders native IAMINA vector art instead of emoji', (
    tester,
  ) async {
    final item = mealFoodById('harira')!;
    await tester.pumpWidget(
      MaterialApp(
        locale: const Locale('fr'),
        home: Scaffold(body: FoodPictogram(item: item, size: 48)),
      ),
    );
    await tester.pumpAndSettle();

    expect(hasCodeFoodPictogram('harira'), isTrue);
    expect(find.text(item.visual), findsNothing);
    expect(_foodArtwork(), findsOneWidget);
    final painter = tester.widget<CustomPaint>(_foodArtwork()).painter;
    expect(painter, isA<FoodPictogramPainter>());

    final semantics = tester.getSemantics(find.byType(FoodPictogram));
    expect(semantics.label, contains('Harira'));
  });

  test('batch 1 code artwork covers exactly the 24 launch concepts', () {
    expect(codeFoodPictogramIds.length, 24);
    const expected = <String>{
      'egg',
      'whole_grain_bread',
      'chicken',
      'grilled_chicken',
      'beef',
      'sardines',
      'salmon',
      'milk',
      'plain_yogurt',
      'apple',
      'banana',
      'orange',
      'tomato',
      'potato',
      'lentils',
      'chickpeas',
      'olive_oil',
      'pizza',
      'burger',
      'moroccan_bread',
      'msemen',
      'baghrir',
      'couscous_7_vegetables',
      'harira',
    };
    expect(codeFoodPictogramIds, expected);
    for (final id in codeFoodPictogramIds) {
      expect(mealFoodById(id), isNotNull, reason: 'Missing catalog food: $id');
    }
  });

  test('every catalog concept resolves to a unique pictogram path', () {
    final paths = <String>{};
    for (final item in mealFoodCatalog) {
      final path = certifiedFoodPictogramPath(item.pictogramKey);
      expect(
        paths.add(path),
        isTrue,
        reason: 'Duplicate pictogram path: $path',
      );
    }
    expect(paths.length, mealFoodCatalog.length);
  });

  test('certified pictogram registry can never reference an unknown food', () {
    for (final id in certifiedFoodPictogramIds) {
      expect(
        mealFoodById(id),
        isNotNull,
        reason: 'Certified pictogram has no catalog food: $id',
      );
    }
  });
}
