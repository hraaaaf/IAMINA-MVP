import 'meal_food_catalog_v3.dart';

/// Reviewed Oman-depth extension (B27).
const List<MealFoodItem> omanDepthB27FoodCatalog = <MealFoodItem>[
  MealFoodItem('omani_madrouba','Madrouba omanaise','Omani madrouba','مضروبة عُمانية',aliases:<String>['madrouba','madrooba','mathrooba','مضروبة'],category:MealFoodCategory.gulfDish,regions:const <MealFoodRegion>{MealFoodRegion.gulf},moments:const <MealFoodMoment>{MealFoodMoment.lunch,MealFoodMoment.dinner,MealFoodMoment.ramadan},visual:'🥣'),
  MealFoodItem('omani_arsia','Arsia omanaise','Omani arsia','عرسية عُمانية',aliases:<String>['arsia','arsiya','عرسية'],category:MealFoodCategory.gulfDish,regions:const <MealFoodRegion>{MealFoodRegion.gulf},moments:const <MealFoodMoment>{MealFoodMoment.lunch,MealFoodMoment.dinner},visual:'🥣'),
  MealFoodItem('omani_paplou','Paplou omani','Omani paplou','بابلو عُماني',aliases:<String>['paplou','paplo','bablo','marqat pablo','بابلو'],category:MealFoodCategory.soup,regions:const <MealFoodRegion>{MealFoodRegion.gulf},moments:const <MealFoodMoment>{MealFoodMoment.lunch,MealFoodMoment.dinner,MealFoodMoment.ramadan},visual:'🐟'),
];
