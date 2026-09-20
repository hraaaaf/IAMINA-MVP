import 'meal_food_catalog_v3.dart';

/// Reviewed international Italy extension (B30).
const List<MealFoodItem> internationalItalyB30FoodCatalog = <MealFoodItem>[
  MealFoodItem('pizza_margherita','Pizza Margherita','Margherita pizza','بيتزا مارغريتا',aliases:<String>['margherita','pizza margherita','مارغريتا'],category:MealFoodCategory.snackFastFood,regions:const <MealFoodRegion>{MealFoodRegion.universal},moments:const <MealFoodMoment>{MealFoodMoment.lunch,MealFoodMoment.dinner},visual:'🍕'),
  MealFoodItem('spaghetti_carbonara','Spaghetti carbonara','Spaghetti carbonara','سباغيتي كاربونارا',aliases:<String>['carbonara','spaghetti alla carbonara','كاربونارا'],category:MealFoodCategory.breadGrain,regions:const <MealFoodRegion>{MealFoodRegion.universal},moments:const <MealFoodMoment>{MealFoodMoment.lunch,MealFoodMoment.dinner},visual:'🍝'),
  MealFoodItem('lasagne_bolognese','Lasagnes à la bolognaise','Bolognese lasagna','لازانيا بولونيز',aliases:<String>['lasagne bolognaise','lasagna bolognese','lasagne alla bolognese','لازانيا'],category:MealFoodCategory.breadGrain,regions:const <MealFoodRegion>{MealFoodRegion.universal},moments:const <MealFoodMoment>{MealFoodMoment.lunch,MealFoodMoment.dinner},visual:'🍝'),
];
