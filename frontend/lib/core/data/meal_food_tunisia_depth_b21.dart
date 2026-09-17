import 'meal_food_catalog_v3.dart';

/// Reviewed Tunisia-depth extension (B21).
const List<MealFoodItem> tunisiaDepthB21FoodCatalog = <MealFoodItem>[
  MealFoodItem('tunisian_brik','Brik tunisienne','Tunisian brik','بريك تونسي',aliases:<String>['brik','brik a l oeuf','brick tunisien','بريك'],category:MealFoodCategory.snackFastFood,regions:const <MealFoodRegion>{MealFoodRegion.universal},moments:const <MealFoodMoment>{MealFoodMoment.lunch,MealFoodMoment.dinner,MealFoodMoment.ramadan},visual:'🥟'),
  MealFoodItem('tunisian_lablabi','Lablabi tunisien','Tunisian lablabi','لبلابي تونسي',aliases:<String>['lablabi','lablebi','لبلابي'],category:MealFoodCategory.soup,regions:const <MealFoodRegion>{MealFoodRegion.universal},moments:const <MealFoodMoment>{MealFoodMoment.breakfast,MealFoodMoment.lunch,MealFoodMoment.dinner},visual:'🥣'),
  MealFoodItem('tunisian_kafteji','Kafteji tunisien','Tunisian kafteji','كفتاجي تونسي',aliases:<String>['kafteji','kaftaji','kefteji','كفتاجي'],category:MealFoodCategory.snackFastFood,regions:const <MealFoodRegion>{MealFoodRegion.universal},moments:const <MealFoodMoment>{MealFoodMoment.lunch,MealFoodMoment.dinner},visual:'🍳'),
];
