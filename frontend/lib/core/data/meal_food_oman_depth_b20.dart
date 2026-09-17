import 'meal_food_catalog_v3.dart';

/// Reviewed Oman-depth extension (B20).
const List<MealFoodItem> omanDepthB20FoodCatalog = <MealFoodItem>[
  MealFoodItem('omani_shuwa','Shuwa omani','Omani shuwa','شواء عُماني',aliases:<String>['shuwa','shuwwa','شواء'],category:MealFoodCategory.gulfDish,regions:const <MealFoodRegion>{MealFoodRegion.gulf},moments:const <MealFoodMoment>{MealFoodMoment.lunch,MealFoodMoment.dinner},visual:'🍖'),
  MealFoodItem('dhofari_madhbi','Madhbi du Dhofar','Dhofari madhbi','مضبي ظفاري',aliases:<String>['madhbi','muthbe','مضبي'],category:MealFoodCategory.gulfDish,regions:const <MealFoodRegion>{MealFoodRegion.gulf},moments:const <MealFoodMoment>{MealFoodMoment.lunch,MealFoodMoment.dinner},visual:'🍖'),
  MealFoodItem('dhofari_maajeen','Maajeen du Dhofar','Dhofari maajeen','معاجين ظفاري',aliases:<String>['maajeen','muajeen','maajin','معاجين'],category:MealFoodCategory.meatPoultry,regions:const <MealFoodRegion>{MealFoodRegion.gulf},moments:const <MealFoodMoment>{MealFoodMoment.lunch,MealFoodMoment.dinner},visual:'🥩'),
];
