import 'meal_food_catalog_v3.dart';

/// Reviewed Yemen-depth extension (B23).
const List<MealFoodItem> yemenDepthB23FoodCatalog = <MealFoodItem>[
  MealFoodItem('yemeni_saltah','Saltah yéménite','Yemeni saltah','سلتة يمنية',aliases:<String>['saltah','salta','سلتة'],category:MealFoodCategory.other,regions:const <MealFoodRegion>{MealFoodRegion.universal},moments:const <MealFoodMoment>{MealFoodMoment.lunch},visual:'🥘'),
  MealFoodItem('yemeni_fahsa','Fahsa yéménite','Yemeni fahsa','فحسة يمنية',aliases:<String>['fahsa','fahsah','فحسة'],category:MealFoodCategory.other,regions:const <MealFoodRegion>{MealFoodRegion.universal},moments:const <MealFoodMoment>{MealFoodMoment.lunch,MealFoodMoment.dinner},visual:'🍲'),
  MealFoodItem('yemeni_bint_al_sahn','Bint al-sahn yéménite','Yemeni bint al-sahn','بنت الصحن اليمنية',aliases:<String>['bint al sahn','bint al-sahn','sabayah','بنت الصحن'],category:MealFoodCategory.sweetDessert,regions:const <MealFoodRegion>{MealFoodRegion.universal},moments:const <MealFoodMoment>{MealFoodMoment.breakfast,MealFoodMoment.snack},visual:'🍯'),
];
