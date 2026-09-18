import 'package:flutter_test/flutter_test.dart';
import 'package:amina/core/data/meal_food_catalog.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter_batch24.dart';

void main(){
 const ids=<String>['moroccan_amlou','moroccan_khlii','moroccan_taktouka'];
 test('B24 appends three Morocco concepts after certified B23 baseline',(){expect(mealFoodCatalog.length,greaterThanOrEqualTo(374));expect(mealFoodCatalog.take(371).length,371);expect(mealFoodCatalog.skip(371).take(3).map((e)=>e.id).toList(),ids);expect(mealFoodCatalog.map((e)=>e.id).toSet().length,mealFoodCatalog.length);});
 test('B24 labels, search, Morocco region, categories and native pictograms are complete',(){for(final id in ids){final item=mealFoodById(id);expect(item,isNotNull);expect(item!.fr,isNotEmpty);expect(item.en,isNotEmpty);expect(item.ar,isNotEmpty);expect(item.regions,contains(MealFoodRegion.morocco));expect(hasCodeFoodPictogramBatch24(id),isTrue);expect(searchMealFoods(item.fr).map((e)=>e.id),contains(id));}expect(mealFoodById('moroccan_amlou')!.category,MealFoodCategory.fatSauce);expect(mealFoodById('moroccan_khlii')!.category,MealFoodCategory.meatPoultry);expect(mealFoodById('moroccan_taktouka')!.category,MealFoodCategory.saladMeal);});
}
