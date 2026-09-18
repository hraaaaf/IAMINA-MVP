import 'meal_food_catalog_v3.dart';

/// Reviewed Saudi-depth extension (B25).
const List<MealFoodItem> saudiDepthB25FoodCatalog = <MealFoodItem>[
  MealFoodItem('saudi_jareesh','Jareesh saoudien','Saudi jareesh','الجريش السعودي',aliases:<String>['jareesh','jarish','جريش','الجريش'],category:MealFoodCategory.gulfDish,regions:const <MealFoodRegion>{MealFoodRegion.gulf},moments:const <MealFoodMoment>{MealFoodMoment.lunch,MealFoodMoment.dinner,MealFoodMoment.ramadan},visual:'🥣'),
  MealFoodItem('saudi_saleeg','Saleeg saoudien','Saudi saleeg','السليق السعودي',aliases:<String>['saleeg','saleeq','سليق','السليق'],category:MealFoodCategory.gulfDish,regions:const <MealFoodRegion>{MealFoodRegion.gulf},moments:const <MealFoodMoment>{MealFoodMoment.lunch,MealFoodMoment.dinner},visual:'🍚'),
  MealFoodItem('saudi_marqooq','Marqooq saoudien','Saudi marqooq','المرقوق السعودي',aliases:<String>['marqooq','margoog','مرقوق','المرقوق'],category:MealFoodCategory.gulfDish,regions:const <MealFoodRegion>{MealFoodRegion.gulf},moments:const <MealFoodMoment>{MealFoodMoment.lunch,MealFoodMoment.dinner},visual:'🍲'),
];
