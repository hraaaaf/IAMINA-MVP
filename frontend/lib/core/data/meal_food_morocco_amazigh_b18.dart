import 'meal_food_catalog_v3.dart';

/// Reviewed Morocco Amazigh-depth extension (B18).
const List<MealFoodItem> moroccoAmazighB18FoodCatalog = <MealFoodItem>[
  MealFoodItem('tagoula','Tagoula','Tagoula','تاكولا',aliases:<String>['tagoulla','tagla','tarwayt','تاغولا'],category:MealFoodCategory.moroccanDish,regions:const <MealFoodRegion>{MealFoodRegion.morocco},moments:const <MealFoodMoment>{MealFoodMoment.breakfast,MealFoodMoment.snack},visual:'🥣'),
  MealFoodItem('ourkimen','Ourkimen','Ourkimen','أوركيمن',aliases:<String>['orkimen','ourkemen','أوركيمن'],category:MealFoodCategory.moroccanDish,regions:const <MealFoodRegion>{MealFoodRegion.morocco},moments:const <MealFoodMoment>{MealFoodMoment.lunch,MealFoodMoment.dinner},visual:'🍲'),
  MealFoodItem('tehal_stuffed_spleen','Tihane / rate farcie','Tehal stuffed spleen','الطحال المعمر',aliases:<String>['tihane','tehane','tehal','tihal','rate farcie','طحال معمر'],category:MealFoodCategory.meatPoultry,regions:const <MealFoodRegion>{MealFoodRegion.morocco},moments:const <MealFoodMoment>{MealFoodMoment.lunch,MealFoodMoment.dinner},visual:'🥩'),
];
