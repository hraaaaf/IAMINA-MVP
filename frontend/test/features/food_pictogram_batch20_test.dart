import 'package:flutter_test/flutter_test.dart';
import 'package:amina/core/data/meal_food_catalog.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter_batch20.dart';

void main(){
 const ids=<String>['omani_shuwa','dhofari_madhbi','dhofari_maajeen'];
 test('B20 certified Oman prefix remains intact after later batches',(){expect(mealFoodCatalog.length,greaterThanOrEqualTo(362));expect(mealFoodCatalog.skip(359).take(3).map((e)=>e.id).toList(),ids);expect(mealFoodCatalog.map((e)=>e.id).toSet().length,mealFoodCatalog.length);});
 test('B20 labels, search, category and native pictograms remain complete',(){for(final id in ids){final item=mealFoodById(id);expect(item,isNotNull);expect(item!.fr,isNotEmpty);expect(item.en,isNotEmpty);expect(item.ar,isNotEmpty);expect(hasCodeFoodPictogramBatch20(id),isTrue);expect(searchMealFoods(item.fr).map((e)=>e.id),contains(id));}expect(mealFoodById('omani_shuwa')!.category,MealFoodCategory.gulfDish);expect(mealFoodById('dhofari_madhbi')!.category,MealFoodCategory.gulfDish);expect(mealFoodById('dhofari_maajeen')!.category,MealFoodCategory.meatPoultry);});
}
