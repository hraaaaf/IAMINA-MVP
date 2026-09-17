import 'package:amina/core/data/meal_food_catalog.dart';
import 'package:amina/core/data/meal_food_catalog_v3.dart' as baseline;
import 'package:amina/core/data/meal_food_gulf_core.dart';
import 'package:amina/core/data/meal_food_morocco_regional_b16.dart';
import 'package:amina/core/data/meal_food_morocco_depth_b17.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter_batch17.dart';
import 'package:flutter_test/flutter_test.dart';

void main(){
  const expected=<String>{'tanjia_marrakchia','boulfaf','lben_moroccan','raib_moroccan'};
  test('B17 appends exactly four concepts after certified B16',(){
    expect(baseline.mealFoodCatalog,hasLength(322)); expect(gulfCoreFoodCatalog,hasLength(24)); expect(moroccoRegionalB16FoodCatalog,hasLength(3)); expect(moroccoDepthB17FoodCatalog,hasLength(4)); expect(mealFoodCatalog,hasLength(353));
    expect(mealFoodCatalog.take(349).map((e)=>e.id),<String>[...baseline.mealFoodCatalog.map((e)=>e.id),...gulfCoreFoodCatalog.map((e)=>e.id),...moroccoRegionalB16FoodCatalog.map((e)=>e.id)]);
    expect(mealFoodCatalog.skip(349).map((e)=>e.id).toSet(),expected);
  });
  test('B17 labels, search, categories and native pictograms are complete',(){
    expect(mealFoodCatalog.map((e)=>e.id).toSet(),hasLength(353)); expect(codeFoodPictogramBatch17Ids,expected);
    for(final id in expected){final item=mealFoodById(id)!;expect(item.fr.trim(),isNotEmpty);expect(item.en.trim(),isNotEmpty);expect(item.ar.trim(),isNotEmpty);expect(item.regions,contains(MealFoodRegion.morocco));expect(searchMealFoods(item.fr).map((e)=>e.id),contains(id));expect(hasCodeFoodPictogramBatch17(id),isTrue);}
    expect(mealFoodById('tanjia_marrakchia')!.category,MealFoodCategory.moroccanDish); expect(mealFoodById('boulfaf')!.category,MealFoodCategory.meatPoultry); expect(mealFoodById('lben_moroccan')!.category,MealFoodCategory.dairy); expect(mealFoodById('raib_moroccan')!.category,MealFoodCategory.dairy);
  });
  test('B17 does not reintroduce the pre-existing chebakia concept',(){
    expect(moroccoDepthB17FoodCatalog.map((e)=>e.id),isNot(contains('chebakia')));
    expect(mealFoodCatalog.where((e)=>e.id=='chebakia'),hasLength(1));
  });
}
