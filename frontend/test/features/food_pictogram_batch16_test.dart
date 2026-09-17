import 'package:amina/core/data/meal_food_catalog.dart';
import 'package:amina/core/data/meal_food_catalog_v3.dart' as baseline;
import 'package:amina/core/data/meal_food_gulf_core.dart';
import 'package:amina/core/data/meal_food_morocco_regional_b16.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter_batch16.dart';
import 'package:flutter_test/flutter_test.dart';

void main(){
 const expectedIds=<String>{'medfouna_rissani','tafernout_bread','berkoukes'};
 test('B16 remains the exact three-concept prefix after certified B15',(){expect(baseline.mealFoodCatalog,hasLength(322));expect(gulfCoreFoodCatalog,hasLength(24));expect(moroccoRegionalB16FoodCatalog,hasLength(3));expect(mealFoodCatalog.length,greaterThanOrEqualTo(349));expect(mealFoodCatalog.take(322).map((e)=>e.id),baseline.mealFoodCatalog.map((e)=>e.id));expect(mealFoodCatalog.skip(322).take(24).map((e)=>e.id),gulfCoreFoodCatalog.map((e)=>e.id));expect(mealFoodCatalog.skip(346).take(3).map((e)=>e.id).toSet(),expectedIds);});
 test('B16 IDs labels categories search and native pictograms remain complete',(){expect(mealFoodCatalog.map((e)=>e.id).toSet(),hasLength(mealFoodCatalog.length));expect(codeFoodPictogramBatch16Ids,expectedIds);for(final id in expectedIds){final item=mealFoodById(id)!;expect(item.fr.trim(),isNotEmpty);expect(item.en.trim(),isNotEmpty);expect(item.ar.trim(),isNotEmpty);expect(item.regions,contains(MealFoodRegion.morocco));expect(hasCodeFoodPictogramBatch16(id),isTrue);expect(searchMealFoods(item.fr).map((e)=>e.id),contains(id));}expect(mealFoodById('tafernout_bread')!.category,MealFoodCategory.breadGrain);expect(mealFoodById('medfouna_rissani')!.category,MealFoodCategory.moroccanDish);expect(mealFoodById('berkoukes')!.category,MealFoodCategory.moroccanDish);});
}
