import 'meal_food_catalog_v3.dart';

/// Reviewed Morocco regional-depth extension (B16).
///
/// Provenance is recorded in the lot handover. These concepts are appended
/// without modifying the certified V3 baseline or Gulf Core B15 ordering.
const List<MealFoodItem> moroccoRegionalB16FoodCatalog = <MealFoodItem>[
  MealFoodItem(
    'medfouna_rissani',
    'Medfouna de Rissani',
    'Rissani medfouna',
    'مدفونة الريصاني',
    aliases: <String>['medfouna', 'madfouna', 'pizza berbère', 'pizza du désert', 'مدفونة'],
    category: MealFoodCategory.moroccanDish,
    regions: const <MealFoodRegion>{MealFoodRegion.morocco},
    moments: const <MealFoodMoment>{MealFoodMoment.lunch, MealFoodMoment.dinner},
    visual: '🥙',
  ),
  MealFoodItem(
    'tafernout_bread',
    'Pain Tafernout',
    'Tafernout bread',
    'خبز تفرنوت',
    aliases: <String>['tafarnout', 'tafernout', 'تفرنوت'],
    category: MealFoodCategory.breadGrain,
    regions: const <MealFoodRegion>{MealFoodRegion.morocco},
    moments: const <MealFoodMoment>{MealFoodMoment.breakfast, MealFoodMoment.lunch, MealFoodMoment.dinner},
    visual: '🫓',
  ),
  MealFoodItem(
    'berkoukes',
    'Berkoukes',
    'Berkoukes',
    'بركوكس',
    aliases: <String>['berkoukech', 'avazine', 'aïch', 'بركوكش'],
    category: MealFoodCategory.moroccanDish,
    regions: const <MealFoodRegion>{MealFoodRegion.morocco},
    moments: const <MealFoodMoment>{MealFoodMoment.lunch, MealFoodMoment.dinner},
    visual: '🍲',
  ),
];
