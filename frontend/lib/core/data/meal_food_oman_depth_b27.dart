import 'meal_food_catalog_v3.dart';

/// Reviewed Oman-depth extension (B27).
const List<MealFoodItem> omanDepthB27FoodCatalog = <MealFoodItem>[
  MealFoodItem('omani_halwa','Halwa omani','Omani halwa','الحلوى العُمانية',aliases:<String>['omani halwa','halwa oman','حلوى عمانية','الحلوى العمانية'],category:MealFoodCategory.sweetDessert,regions:const <MealFoodRegion>{MealFoodRegion.gulf},moments:const <MealFoodMoment>{MealFoodMoment.snack},visual:'🍮'),
  MealFoodItem('omani_mishkak','Mishkak omani','Omani mishkak','مشكاك عُماني',aliases:<String>['mishkak','mishakik','meshkak','مشكاك'],category:MealFoodCategory.meatPoultry,regions:const <MealFoodRegion>{MealFoodRegion.gulf},moments:const <MealFoodMoment>{MealFoodMoment.lunch,MealFoodMoment.dinner},visual:'🍢'),
  MealFoodItem('omani_qabooli','Qabooli omani','Omani qabooli','قبولي عُماني',aliases:<String>['qabooli','qaboli','kabouli','قبولي'],category:MealFoodCategory.gulfDish,regions:const <MealFoodRegion>{MealFoodRegion.gulf},moments:const <MealFoodMoment>{MealFoodMoment.lunch,MealFoodMoment.dinner},visual:'🍚'),
];
