import 'package:flutter_test/flutter_test.dart';
import 'package:amina/core/data/meal_food_catalog.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter_batch31.dart';

void main(){
  const ids=<String>['egyptian_koshary','egyptian_ful_medames','egyptian_molokhiya'];
  test('B31 appends three Egypt concepts after certified B30 baseline',(){expect(mealFoodCatalog.length,395);expect(mealFoodCatalog.take(392).length,392);expect(mealFoodCatalog.skip(392).map((e)=>e.id).toList(),ids);expect(mealFoodCatalog.map((e)=>e.id).toSet().length,395);});
  test('B31 labels search categories and native pictograms are complete',(){for(final id in ids){final item=mealFoodById(id);expect(item,isNotNull);expect(item!.fr,isNotEmpty);expect(item.en,isNotEmpty);expect(item.ar,isNotEmpty);expect(item.regions,contains(MealFoodRegion.universal));expect(hasCodeFoodPictogramBatch31(id),isTrue);expect(searchMealFoods(item.fr).map((e)=>e.id),contains(id));}expect(mealFoodById('egyptian_koshary')!.category,MealFoodCategory.breadGrain);expect(mealFoodById('egyptian_ful_medames')!.category,MealFoodCategory.legume);expect(mealFoodById('egyptian_molokhiya')!.category,MealFoodCategory.soup);});
}
