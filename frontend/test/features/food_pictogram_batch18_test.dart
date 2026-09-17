import 'package:amina/core/data/meal_food_catalog.dart';
import 'package:amina/core/data/meal_food_catalog_v3.dart' as baseline;
import 'package:amina/core/data/meal_food_gulf_core.dart';
import 'package:amina/core/data/meal_food_morocco_regional_b16.dart';
import 'package:amina/core/data/meal_food_morocco_depth_b17.dart';
import 'package:amina/core/data/meal_food_morocco_amazigh_b18.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter_batch18.dart';
import 'package:flutter_test/flutter_test.dart';

void main(){
  const expected=<String>{'tagoula','ourkimen','tehal_stuffed_spleen'};
  test('B18 appends exactly three concepts after certified B17',(){
    expect(baseline.mealFoodCatalog,hasLength(322));expect(gulfCoreFoodCatalog,hasLength(24));expect(moroccoRegionalB16FoodCatalog,hasLength(3));expect(moroccoDepthB17FoodCatalog,hasLength(4));expect(moroccoAmazighB18FoodCatalog,hasLength(3));expect(mealFoodCatalog,hasLength(356));
    expect(mealFoodCatalog.take(353).map((e)=>e.id),<String>[...baseline.mealFoodCatalog.map((e)=>e.id),...gulfCoreFoodCatalog.map((e)=>e.id),...moroccoRegionalB16FoodCatalog.map((e)=>e.id),...moroccoDepthB17FoodCatalog.map((e)=>e.id)]);
    expect(mealFoodCatalog.skip(353).map((e)=>e.id).toSet(),expected);
  });
  test('B18 labels, search, categories and native pictograms are complete',(){
    expect(mealFoodCatalog.map((e)=>e.id).toSet(),hasLength(356));expect(codeFoodPictogramBatch18Ids,expected);
    for(final id in expected){final item=mealFoodById(id)!;expect(item.fr.trim(),isNotEmpty);expect(item.en.trim(),isNotEmpty);expect(item.ar.trim(),isNotEmpty);expect(item.regions,contains(MealFoodRegion.morocco));expect(searchMealFoods(item.fr).map((e)=>e.id),contains(id));expect(hasCodeFoodPictogramBatch18(id),isTrue);}
    expect(mealFoodById('tagoula')!.category,MealFoodCategory.moroccanDish);expect(mealFoodById('ourkimen')!.category,MealFoodCategory.moroccanDish);expect(mealFoodById('tehal_stuffed_spleen')!.category,MealFoodCategory.meatPoultry);
  });
  test('B18 concepts do not collide with the certified B17 prefix',(){final prefix=mealFoodCatalog.take(353).map((e)=>e.id).toSet();expect(prefix.intersection(expected),isEmpty);});
}
