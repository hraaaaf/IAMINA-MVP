import 'meal_food_catalog.dart';

class MealFoodQuery {
  final String text;
  final MealFoodCategory? category;
  final MealFoodRegion? region;
  final MealFoodMoment? moment;
  final int limit;

  const MealFoodQuery({
    this.text = '',
    this.category,
    this.region,
    this.moment,
    this.limit = 24,
  });
}

List<MealFoodItem> queryMealFoods(MealFoodQuery query) {
  final normalized = foldMealText(query.text);
  final source = normalized.length >= 2
      ? searchMealFoods(query.text, limit: mealFoodCatalog.length)
      : mealFoodCatalog;

  final filtered = source.where((item) {
    if (query.category != null && item.category != query.category) return false;
    if (query.region != null && !item.regions.contains(query.region)) return false;
    if (query.moment != null && !item.moments.contains(query.moment)) return false;
    return true;
  });

  final result = filtered.take(query.limit).toList(growable: false);
  if (normalized.length >= 2) return result;

  final sorted = result.toList(growable: true)
    ..sort((a, b) => a.fr.compareTo(b.fr));
  return sorted;
}
