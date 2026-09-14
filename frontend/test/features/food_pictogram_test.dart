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
      final item = mealFoodById('guava')!;
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
      expect(widget.assetPath, 'assets/food/pictograms/v1/guava.webp');
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

    expect(hasCodeFoodPictogramBatch2('rfissa'), isTrue);
    expect(find.text(item.visual), findsNothing);
    expect(_foodArtwork(), findsOneWidget);
    final painter = tester.widget<CustomPaint>(_foodArtwork()).painter;
    expect(painter, isA<FoodPictogramPainterBatch2>());
  });

  testWidgets('batch 3 renders catalog-order IAMINA vector art instead of emoji', (
    tester,
  ) async {
    final item = mealFoodById('baguette')!;
    await tester.pumpWidget(
      MaterialApp(
        locale: const Locale('fr'),
        home: Scaffold(body: FoodPictogram(item: item, size: 48)),
      ),
    );
    await tester.pumpAndSettle();

    expect(hasCodeFoodPictogramBatch3('baguette'), isTrue);
    expect(find.text(item.visual), findsNothing);
    expect(_foodArtwork(), findsOneWidget);
    final painter = tester.widget<CustomPaint>(_foodArtwork()).painter;
    expect(painter, isA<FoodPictogramPainterBatch3>());
  });

  testWidgets('batch 4 renders Moroccan catalog art instead of emoji', (
    tester,
  ) async {
    final item = mealFoodById('tajine')!;
    await tester.pumpWidget(
      MaterialApp(
        locale: const Locale('fr'),
        home: Scaffold(body: FoodPictogram(item: item, size: 48)),
      ),
    );
    await tester.pumpAndSettle();

    expect(hasCodeFoodPictogramBatch4('tajine'), isTrue);
    expect(find.text(item.visual), findsNothing);
    expect(_foodArtwork(), findsOneWidget);
    final painter = tester.widget<CustomPaint>(_foodArtwork()).painter;
    expect(painter, isA<FoodPictogramPainterBatch4>());
  });

  testWidgets('batch 5 renders Gulf catalog art instead of emoji', (
    tester,
  ) async {
    final item = mealFoodById('machboos_fish')!;
    await tester.pumpWidget(
      MaterialApp(
        locale: const Locale('fr'),
        home: Scaffold(body: FoodPictogram(item: item, size: 48)),
      ),
    );
    await tester.pumpAndSettle();

    expect(hasCodeFoodPictogramBatch5('machboos_fish'), isTrue);
    expect(find.text(item.visual), findsNothing);
    expect(_foodArtwork(), findsOneWidget);
    final painter = tester.widget<CustomPaint>(_foodArtwork()).painter;
    expect(painter, isA<FoodPictogramPainterBatch5>());
  });

  testWidgets('batch 6 renders native protein art instead of emoji', (
    tester,
  ) async {
    final item = mealFoodById('chicken_breast')!;
    await tester.pumpWidget(
      MaterialApp(
        locale: const Locale('fr'),
        home: Scaffold(body: FoodPictogram(item: item, size: 48)),
      ),
    );
    await tester.pumpAndSettle();

    expect(hasCodeFoodPictogramBatch6('chicken_breast'), isTrue);
    expect(find.text(item.visual), findsNothing);
    expect(_foodArtwork(), findsOneWidget);
    final painter = tester.widget<CustomPaint>(_foodArtwork()).painter;
    expect(painter, isA<FoodPictogramPainterBatch6>());
  });

  test('batch 1 code artwork covers exactly the first 24 launch concepts', () {
    expect(codeFoodPictogramIds.length, 24);
    const expected = <String>{
      'egg', 'whole_grain_bread', 'chicken', 'grilled_chicken', 'beef',
      'sardines', 'salmon', 'milk', 'plain_yogurt', 'apple', 'banana',
      'orange', 'tomato', 'potato', 'lentils', 'chickpeas', 'olive_oil',
      'pizza', 'burger', 'moroccan_bread', 'msemen', 'baghrir',
      'couscous_7_vegetables', 'harira',
    };
    expect(codeFoodPictogramIds, expected);
  });

  test('batch 2 code artwork covers exactly the next 24 launch concepts', () {
    expect(codeFoodPictogramBatch2Ids.length, 24);
    const expected = <String>{
      'rfissa', 'chicken_preserved_lemon_tagine', 'kefta_tagine', 'zaalouk',
      'taktouka', 'amlou', 'mint_tea', 'moroccan_sweet_tea',
      'arabic_flatbread', 'tannour_bread', 'machboos_chicken', 'kabsa_chicken',
      'mandi_chicken', 'harees', 'jareesh', 'thareed', 'balaleet', 'luqaimat',
      'dates', 'ajwa_dates', 'arabic_coffee', 'karak_tea', 'shawarma_chicken',
      'hummus',
    };
    expect(codeFoodPictogramBatch2Ids, expected);
  });

  test('batch 3 covers the exact manifest-derived catalog batch', () {
    expect(codeFoodPictogramBatch3Ids.length, 24);
    const expected = <String>{
      'baguette', 'batbout', 'bulgur', 'chebab', 'couscous', 'crepe',
      'cereal', 'oats', 'waffle', 'granola', 'harcha', 'krachel', 'corn',
      'muesli', 'barley', 'white_bread', 'toast_bread', 'khameer_bread',
      'pita_bread', 'regag_bread', 'pancake', 'porridge', 'pasta', 'quinoa',
    };
    expect(codeFoodPictogramBatch3Ids, expected);
  });

  test('batch 4 covers the exact manifest-derived catalog batch', () {
    expect(codeFoodPictogramBatch4Ids.length, 24);
    const expected = <String>{
      'rice', 'basmati_rice', 'brown_rice', 'semolina', 'vermicelli',
      'bissara', 'briouat_cheese', 'briouat_meat', 'couscous_tfaya',
      'hssoua', 'khlii', 'maakouda', 'mrouzia', 'mechoui',
      'pastilla_chicken', 'pastilla_seafood', 'seffa', 'sellou', 'sfenj',
      'tajine', 'lamb_prune_tagine', 'tanjia', 'zammita', 'aseeda',
    };
    expect(codeFoodPictogramBatch4Ids, expected);
  });

  test('batch 5 covers the exact manifest-derived catalog batch', () {
    expect(codeFoodPictogramBatch5Ids.length, 24);
    const expected = <String>{
      'fish_biryani', 'chicken_biryani', 'lamb_biryani', 'falafel',
      'fattoush', 'foul_medames', 'kabsa_lamb', 'khabeesa',
      'machboos_fish', 'majboos_shrimp', 'machboos_lamb', 'madrooba',
      'manakish_cheese', 'manakish_zaatar', 'mandi_lamb', 'margoog',
      'moutabal', 'mutabbaq', 'muhammar_rice', 'saleeg', 'saloona',
      'samboosa_cheese', 'samboosa_meat', 'shakshuka',
    };
    expect(codeFoodPictogramBatch5Ids, expected);

    final previous = <String>{
      ...codeFoodPictogramIds,
      ...codeFoodPictogramBatch2Ids,
      ...codeFoodPictogramBatch3Ids,
      ...codeFoodPictogramBatch4Ids,
    };
    expect(codeFoodPictogramBatch5Ids.intersection(previous), isEmpty);
    for (final id in codeFoodPictogramBatch5Ids) {
      expect(mealFoodById(id), isNotNull, reason: 'Missing catalog food: $id');
    }
    expect(<String>{...previous, ...codeFoodPictogramBatch5Ids}.length, 120);
  });

  test('every catalog concept resolves to a unique pictogram path', () {
    final paths = <String>{};
    for (final item in mealFoodCatalog) {
      final path = certifiedFoodPictogramPath(item.pictogramKey);
      expect(paths.add(path), isTrue, reason: 'Duplicate pictogram path: $path');
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