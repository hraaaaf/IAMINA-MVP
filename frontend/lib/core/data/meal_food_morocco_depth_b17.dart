import 'meal_food_catalog_v3.dart';

/// Reviewed Morocco depth extension (B17).
const List<MealFoodItem> moroccoDepthB17FoodCatalog = <MealFoodItem>[
  MealFoodItem('tanjia_marrakchia','Tanjia marrakchia','Marrakesh tanjia','طنجية مراكشية',aliases:<String>['tanjia','tangia','tanjia marrakech','الطنجية'],category:MealFoodCategory.moroccanDish,regions:const <MealFoodRegion>{MealFoodRegion.morocco},moments:const <MealFoodMoment>{MealFoodMoment.lunch,MealFoodMoment.dinner},visual:'🍖'),
  MealFoodItem('boulfaf','Boulfaf','Boulfaf','بولفاف',aliases:<String>['bulfaf','bolfaf','boulfef','brochettes de foie','بولفاف'],category:MealFoodCategory.meatPoultry,regions:const <MealFoodRegion>{MealFoodRegion.morocco},moments:const <MealFoodMoment>{MealFoodMoment.lunch,MealFoodMoment.dinner},visual:'🍢'),
  MealFoodItem('lben_moroccan','Lben marocain','Moroccan lben','اللبن المغربي',aliases:<String>['lben','leben','buttermilk marocain','لبن'],category:MealFoodCategory.dairy,regions:const <MealFoodRegion>{MealFoodRegion.morocco},moments:const <MealFoodMoment>{MealFoodMoment.breakfast,MealFoodMoment.lunch,MealFoodMoment.dinner},visual:'🥛'),
  MealFoodItem('raib_moroccan','Raïb marocain','Moroccan raib','الرايب المغربي',aliases:<String>['raib','raïb','rayeb','الرايب'],category:MealFoodCategory.dairy,regions:const <MealFoodRegion>{MealFoodRegion.morocco},moments:const <MealFoodMoment>{MealFoodMoment.breakfast,MealFoodMoment.snack},visual:'🥣'),
];
