import 'package:amina/core/data/meal_food_catalog.dart';
import 'package:amina/core/data/meal_food_query.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('browse query filters Gulf dishes independently from Morocco', () {
    final gulf = queryMealFoods(
      const MealFoodQuery(
        category: MealFoodCategory.gulfDish,
        region: MealFoodRegion.gulf,
        limit: 100,
      ),
    );
    expect(gulf, isNotEmpty);
    expect(gulf.every((item) => item.category == MealFoodCategory.gulfDish), isTrue);
    expect(gulf.every((item) => item.regions.contains(MealFoodRegion.gulf)), isTrue);
    expect(gulf.map((item) => item.id), contains('harees'));
    expect(gulf.map((item) => item.id), isNot(contains('rfissa')));
  });

  test('browse query combines multilingual text and category without losing ranking', () {
    final results = queryMealFoods(
      const MealFoodQuery(
        text: 'شاورما',
        category: MealFoodCategory.gulfDish,
        limit: 12,
      ),
    );
    expect(results, isNotEmpty);
    expect(results.first.id, 'shawarma_beef');
    expect(results.map((item) => item.id), contains('shawarma_chicken'));
  });

  test('browse query supports Ramadan vocabulary', () {
    final results = queryMealFoods(
      const MealFoodQuery(moment: MealFoodMoment.ramadan, limit: 200),
    );
    expect(results, isNotEmpty);
    expect(results.map((item) => item.id), contains('harira'));
    expect(results.map((item) => item.id), contains('harees'));
    expect(results.map((item) => item.id), contains('luqaimat'));
  });
}
