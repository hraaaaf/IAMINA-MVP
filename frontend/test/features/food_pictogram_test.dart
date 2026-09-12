import 'package:amina/core/data/meal_food_catalog.dart';
import 'package:amina/features/journal/widgets/food_pictogram.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('food pictogram has deterministic premium asset path and safe fallback', (
    tester,
  ) async {
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

    final semantics = tester.getSemantics(find.byType(FoodPictogram));
    expect(semantics.label, contains('Rfissa'));
  });

  test('every catalog concept resolves to a unique pictogram path', () {
    final paths = <String>{};
    for (final item in mealFoodCatalog) {
      final path = 'assets/food/pictograms/v1/${item.pictogramKey}.webp';
      expect(paths.add(path), isTrue, reason: 'Duplicate pictogram path: $path');
    }
    expect(paths.length, mealFoodCatalog.length);
  });
}
