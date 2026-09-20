import 'meal_food_catalog_v3.dart';

/// Reviewed Egypt core extension (B31).
const List<MealFoodItem> egyptCoreB31FoodCatalog = <MealFoodItem>[
  MealFoodItem('egyptian_koshary','Kochari égyptien','Egyptian koshary','كشري مصري',aliases:<String>['kochari','koshari','koshary','كشري'],category:MealFoodCategory.breadGrain,regions:const <MealFoodRegion>{MealFoodRegion.universal},moments:const <MealFoodMoment>{MealFoodMoment.lunch,MealFoodMoment.dinner},visual:'🍲'),
  MealFoodItem('egyptian_ful_medames','Foul medames égyptien','Egyptian ful medames','فول مدمس مصري',aliases:<String>['foul medames','ful medames','فول مدمس'],category:MealFoodCategory.legume,regions:const <MealFoodRegion>{MealFoodRegion.universal},moments:const <MealFoodMoment>{MealFoodMoment.breakfast,MealFoodMoment.lunch},visual:'🫘'),
  MealFoodItem('egyptian_molokhiya','Molokhiya égyptienne','Egyptian molokhiya','ملوخية مصرية',aliases:<String>['molokhia','molokhiya','mulukhiyah','ملوخية'],category:MealFoodCategory.soup,regions:const <MealFoodRegion>{MealFoodRegion.universal},moments:const <MealFoodMoment>{MealFoodMoment.lunch,MealFoodMoment.dinner},visual:'🥣'),
];
