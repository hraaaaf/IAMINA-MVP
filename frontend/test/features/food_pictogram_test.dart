import 'package:amina/core/data/food_pictogram_registry.dart';
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

Finder _foodArtwork() => find.byWidgetPredicate(
  (widget) =>
      widget is CustomPaint &&
      (widget.painter is FoodPictogramPainter ||
          widget.painter is FoodPictogramPainterBatch2 ||
          widget.painter is FoodPictogramPainterBatch3 ||
          widget.painter is FoodPictogramPainterBatch4 ||
          widget.painter is FoodPictogramPainterBatch5 ||
          widget.painter is FoodPictogramPainterBatch6),
  description: 'IAMINA FoodPictogram CustomPaint',
);

void main() {
  testWidgets(
    'long-tail food keeps deterministic asset path and safe emoji fallback',
    (tester) async {
      final item = mealFoodById('lettuce')!;
      const locale = Locale('fr');
      await tester.pumpWidget(
        MaterialApp(
          locale: locale,
          supportedLocales: const <Locale>[locale],
          localizationsDelegates: GlobalMaterialLocalizations.delegates,
          home: Scaffold(body: FoodPictogram(item: item)),
        ),
      );
      await tester.pumpAndSettle();

      final widget = tester.widget<FoodPictogram>(find.byType(FoodPictogram));
      expect(widget.assetPath, 'assets/food/pictograms/v1/lettuce.webp');
      expect(find.text(item.visual), findsOneWidget);
      expect(_foodArtwork(), findsNothing);

      final semantics = tester.getSemantics(find.byType(FoodPictogram));
      expect(semantics.label, contains(item.plainLabelFor(locale)));
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
  });

  testWidgets('batch 2 renders regional IAMINA vector art instead of emoji', (
    tester,
  ) async {
    final item = mealFoodById('rfissa')!;
    await tester.pumpWidget(
      MaterialApp(
        locale: const Locale('fr'),
        home: Scaffold(body: FoodPictogram(item: item, size: 48)),
      ),
    );
    await tester.pumpAndSettle();

    expect(hasCodeFoodPictogramBatch2(item.id), isTrue);
    expect(find.text(item.visual), findsNothing);
    expect(_foodArtwork(), findsOneWidget);
    final painter = tester.widget<CustomPaint>(_foodArtwork()).painter;
    expect(painter, isA<FoodPictogramPainterBatch2>());
  });

  testWidgets('batch 3 renders catalog-order IAMINA vector art instead of emoji', (
    tester,
  ) async {
    final item = mealFoodById('bissara')!;
    await tester.pumpWidget(
      MaterialApp(
        locale: const Locale('fr'),
        home: Scaffold(body: FoodPictogram(item: item, size: 48)),
      ),
    );
    await tester.pumpAndSettle();

    expect(hasCodeFoodPictogramBatch3(item.id), isTrue);
    expect(find.text(item.visual), findsNothing);
    expect(_foodArtwork(), findsOneWidget);
    final painter = tester.widget<CustomPaint>(_foodArtwork()).painter;
    expect(painter, isA<FoodPictogramPainterBatch3>());
  });

  testWidgets('batch 4 renders Moroccan catalog art instead of emoji', (
    tester,
  ) async {
    final item = mealFoodById('zaalouk')!;
    await tester.pumpWidget(
      MaterialApp(
        locale: const Locale('fr'),
        home: Scaffold(body: FoodPictogram(item: item, size: 48)),
      ),
    );
    await tester.pumpAndSettle();

    expect(hasCodeFoodPictogramBatch4(item.id), isTrue);
    expect(find.text(item.visual), findsNothing);
    expect(_foodArtwork(), findsOneWidget);
    final painter = tester.widget<CustomPaint>(_foodArtwork()).painter;
    expect(painter, isA<FoodPictogramPainterBatch4>());
  });

  testWidgets('batch 5 renders Gulf catalog art instead of emoji', (
    tester,
  ) async {
    final item = mealFoodById('machboos')!;
    await tester.pumpWidget(
      MaterialApp(
        locale: const Locale('fr'),
        home: Scaffold(body: FoodPictogram(item: item, size: 48)),
      ),
    );
    await tester.pumpAndSettle();

    expect(hasCodeFoodPictogramBatch5(item.id), isTrue);
    expect(find.text(item.visual), findsNothing);
    expect(_foodArtwork(), findsOneWidget);
    final painter = tester.widget<CustomPaint>(_foodArtwork()).painter;
    expect(painter, isA<FoodPictogramPainterBatch5>());
  });

  testWidgets('batch 6 renders native protein art instead of emoji', (
    tester,
  ) async {
    final item = mealFoodById('beef_steak')!;
    await tester.pumpWidget(
      MaterialApp(
        locale: const Locale('fr'),
        home: Scaffold(body: FoodPictogram(item: item, size: 48)),
      ),
    );
    await tester.pumpAndSettle();

    expect(hasCodeFoodPictogramBatch6(item.id), isTrue);
    expect(find.text(item.visual), findsNothing);
    expect(_foodArtwork(), findsOneWidget);
    final painter = tester.widget<CustomPaint>(_foodArtwork()).painter;
    expect(painter, isA<FoodPictogramPainterBatch6>());
  });

  test('batch 1 code artwork covers exactly the first 24 launch concepts', () {
    expect(codeFoodPictogramIds.length, 24);
  });

  test('batch 2 code artwork covers exactly the next 24 launch concepts', () {
    expect(codeFoodPictogramBatch2Ids.length, 24);
  });

  test('batch 3 covers the exact manifest-derived catalog batch', () {
    expect(codeFoodPictogramBatch3Ids.length, 24);
  });

  test('batch 4 covers the exact manifest-derived catalog batch', () {
    expect(codeFoodPictogramBatch4Ids.length, 24);
  });

  test('batch 5 covers the exact manifest-derived catalog batch', () {
    expect(codeFoodPictogramBatch5Ids.length, 24);
  });

  test('every catalog concept resolves to a unique pictogram path', () {
    expect(foodPictogramRegistry.keys.toSet().length, foodPictogramRegistry.length);
    for (final food in MealFoodCatalog.items) {
      expect(foodPictogramAssetPath(food.id), isNotNull);
    }
  });

  test('certified pictogram registry can never reference an unknown food', () {
    for (final id in foodPictogramRegistry.keys) {
      expect(mealFoodById(id), isNotNull, reason: 'Unknown registry food: $id');
    }
  });
}