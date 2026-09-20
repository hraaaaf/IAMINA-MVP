import 'meal_food_catalog_v3.dart';

/// Reviewed Morocco-depth extension (B28).
const List<MealFoodItem> moroccoDepthB28FoodCatalog = <MealFoodItem>[
  MealFoodItem('moroccan_pastilla','Pastilla marocaine','Moroccan pastilla','بسطيلة مغربية',aliases:<String>['pastilla','bastilla','b\u0027stilla','بسطيلة'],category:MealFoodCategory.other,regions:const <MealFoodRegion>{MealFoodRegion.morocco},moments:const <MealFoodMoment>{MealFoodMoment.lunch,MealFoodMoment.dinner},visual:'🥧'),
  MealFoodItem('marrakech_tanjia','Tanjia marrakchia','Marrakech tanjia','طنجية مراكشية',aliases:<String>['tanjia','tangia','tanjia marrakchia','طنجية','طنجية مراكشية'],category:MealFoodCategory.meatPoultry,regions:const <MealFoodRegion>{MealFoodRegion.morocco},moments:const <MealFoodMoment>{MealFoodMoment.lunch,MealFoodMoment.dinner},visual:'🍖'),
  MealFoodItem('moroccan_mrouzia','Mrouzia marocaine','Moroccan mrouzia','مروزية مغربية',aliases:<String>['mrouzia','marozia','mrouziya','مروزية'],category:MealFoodCategory.meatPoultry,regions:const <MealFoodRegion>{MealFoodRegion.morocco},moments:const <MealFoodMoment>{MealFoodMoment.lunch,MealFoodMoment.dinner},visual:'🍖'),
];
