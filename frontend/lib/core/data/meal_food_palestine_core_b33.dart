import 'meal_food_catalog_v3.dart';

/// Reviewed Palestine core extension (B33).
const List<MealFoodItem> palestineCoreB33FoodCatalog = <MealFoodItem>[
  MealFoodItem('palestinian_musakhan','Musakhan palestinien','Palestinian musakhan','مسخن فلسطيني',aliases:<String>['musakhan','mussakhan','مسخن'],category:MealFoodCategory.meatPoultry,regions:const <MealFoodRegion>{MealFoodRegion.universal},moments:const <MealFoodMoment>{MealFoodMoment.lunch,MealFoodMoment.dinner},visual:'🍗'),
  MealFoodItem('palestinian_qidreh','Qidreh d’Hébron','Hebron qidreh','قدرة خليلية',aliases:<String>['qidreh','qidra','kidra','قدرة','القدرة الخليلية'],category:MealFoodCategory.breadGrain,regions:const <MealFoodRegion>{MealFoodRegion.universal},moments:const <MealFoodMoment>{MealFoodMoment.lunch,MealFoodMoment.dinner},visual:'🍚'),
  MealFoodItem('jerusalem_kaak','Ka’ak de Jérusalem','Jerusalem ka’ak','كعك القدس',aliases:<String>['kaak al quds','ka’ak al-quds','jerusalem sesame bread','كعك القدس'],category:MealFoodCategory.breadGrain,regions:const <MealFoodRegion>{MealFoodRegion.universal},moments:const <MealFoodMoment>{MealFoodMoment.breakfast,MealFoodMoment.snack},visual:'🥯'),
];
