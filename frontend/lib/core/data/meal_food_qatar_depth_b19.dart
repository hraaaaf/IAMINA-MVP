import 'meal_food_catalog_v3.dart';

/// Reviewed Qatar-depth extension (B19).
const List<MealFoodItem> qatarDepthB19FoodCatalog = <MealFoodItem>[
  MealFoodItem('qatari_saloona','Saloona qatarie','Qatari saloona','صالونة قطرية',aliases:<String>['salona','saloona','صالونة'],category:MealFoodCategory.gulfDish,regions:const <MealFoodRegion>{MealFoodRegion.gulf},moments:const <MealFoodMoment>{MealFoodMoment.lunch,MealFoodMoment.dinner,MealFoodMoment.ramadan},visual:'🍲'),
  MealFoodItem('qatari_margoog','Margoog qatari','Qatari margoog','مرقوق قطري',aliases:<String>['margoog','margooq','marqooq','مرقوق'],category:MealFoodCategory.gulfDish,regions:const <MealFoodRegion>{MealFoodRegion.gulf},moments:const <MealFoodMoment>{MealFoodMoment.lunch,MealFoodMoment.dinner},visual:'🍲'),
  MealFoodItem('qatari_sago','Sago qatari','Qatari sago pudding','ساقو قطري',aliases:<String>['sago pudding','sago hisso','ساقو'],category:MealFoodCategory.sweetDessert,regions:const <MealFoodRegion>{MealFoodRegion.gulf},moments:const <MealFoodMoment>{MealFoodMoment.snack,MealFoodMoment.ramadan},visual:'🍮'),
];
