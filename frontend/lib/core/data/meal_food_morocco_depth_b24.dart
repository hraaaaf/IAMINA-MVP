import 'meal_food_catalog_v3.dart';

/// Reviewed Morocco-depth extension (B24).
const List<MealFoodItem> moroccoDepthB24FoodCatalog = <MealFoodItem>[
  MealFoodItem('moroccan_amlou','Amlou marocain','Moroccan amlou','أملو مغربي',aliases:<String>['amlou','amlu','أملو'],category:MealFoodCategory.fatSauce,regions:const <MealFoodRegion>{MealFoodRegion.morocco},moments:const <MealFoodMoment>{MealFoodMoment.breakfast,MealFoodMoment.snack},visual:'🥜'),
  MealFoodItem('moroccan_khlii','Khlii marocain','Moroccan khlii','الخليع المغربي',aliases:<String>['khlii','khlea','khlia','خليع','الخليع'],category:MealFoodCategory.meatPoultry,regions:const <MealFoodRegion>{MealFoodRegion.morocco},moments:const <MealFoodMoment>{MealFoodMoment.breakfast,MealFoodMoment.lunch,MealFoodMoment.dinner},visual:'🥩'),
  MealFoodItem('moroccan_taktouka','Taktouka marocaine','Moroccan taktouka','تكتوكة مغربية',aliases:<String>['taktouka','tektouta','تكتوكة'],category:MealFoodCategory.saladMeal,regions:const <MealFoodRegion>{MealFoodRegion.morocco},moments:const <MealFoodMoment>{MealFoodMoment.lunch,MealFoodMoment.dinner},visual:'🫑'),
];
