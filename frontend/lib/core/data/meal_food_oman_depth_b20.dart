import 'meal_food_catalog_v3.dart';

/// Reviewed Oman-depth extension (B20).
const List<MealFoodItem> omanDepthB20FoodCatalog = <MealFoodItem>[
  MealFoodItem('omani_shuwa','Shuwa omani','Omani shuwa','شواء عُماني',aliases:<String>['shuwa','shuwwa','شواء'],category:MealFoodCategory.gulfDish,regions:const <MealFoodRegion>{MealFoodRegion.gulf},moments:const <MealFoodMoment>{MealFoodMoment.lunch,MealFoodMoment.dinner},visual:'🍖'),
  MealFoodItem('omani_qabooli','Qabooli omani','Omani qabooli','قبولي عُماني',aliases:<String>['qabooli','qaboli','قبولي'],category:MealFoodCategory.gulfDish,regions:const <MealFoodRegion>{MealFoodRegion.gulf},moments:const <MealFoodMoment>{MealFoodMoment.lunch,MealFoodMoment.dinner},visual:'🍚'),
  MealFoodItem('omani_mishkak','Mishkak omani','Omani mishkak','مشكاك عُماني',aliases:<String>['mishkak','mashakeek','مشكاك'],category:MealFoodCategory.gulfDish,regions:const <MealFoodRegion>{MealFoodRegion.gulf},moments:const <MealFoodMoment>{MealFoodMoment.lunch,MealFoodMoment.dinner,MealFoodMoment.snack},visual:'🍢'),
];
