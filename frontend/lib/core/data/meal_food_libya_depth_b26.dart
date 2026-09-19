import 'meal_food_catalog_v3.dart';

/// Reviewed Libya-depth extension (B26).
const List<MealFoodItem> libyaDepthB26FoodCatalog = <MealFoodItem>[
  MealFoodItem('libyan_bazin','Bazin libyen','Libyan bazin','البازين الليبي',aliases:<String>['bazin','bazeen','بازين','البازين'],category:MealFoodCategory.breadGrain,regions:const <MealFoodRegion>{MealFoodRegion.universal},moments:const <MealFoodMoment>{MealFoodMoment.lunch,MealFoodMoment.dinner,MealFoodMoment.ramadan},visual:'🥣'),
  MealFoodItem('libyan_mbakbaka','Mbakbaka libyenne','Libyan mbakbaka','المبكبكة الليبية',aliases:<String>['mbakbaka','imbakbaka','mabkaba','مبكبكة','المبكبكة'],category:MealFoodCategory.other,regions:const <MealFoodRegion>{MealFoodRegion.universal},moments:const <MealFoodMoment>{MealFoodMoment.lunch,MealFoodMoment.dinner},visual:'🍝'),
  MealFoodItem('libyan_shorba','Chorba libyenne','Libyan shorba','الشوربة الليبية',aliases:<String>['shorba libiya','shorba libya','chorba libyenne','شوربة ليبية','الشوربة الليبية'],category:MealFoodCategory.soup,regions:const <MealFoodRegion>{MealFoodRegion.universal},moments:const <MealFoodMoment>{MealFoodMoment.lunch,MealFoodMoment.dinner,MealFoodMoment.ramadan},visual:'🍲'),
];
