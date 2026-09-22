import 'package:flutter_test/flutter_test.dart';
import 'package:amina/core/data/meal_food_catalog.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter_batch32.dart';

void main(){
  const ids=<String>['sudanese_kisra','sudanese_aseeda','sudanese_gurraasa'];
  test('B32 appends three Sudan concepts after certified B31 baseline',(){expect(mealFoodCatalog.length,398);expect(mealFoodCatalog.take(395).length,395);expect(mealFoodCatalog.skip(395).map((e)=>e.id).toList(),ids);expect(mealFoodCatalog.map((e)=>e.id).toSet().length,398);});
  test('B32 labels search categories and native pictograms are complete',(){for(final id in ids){final item=mealFoodById(id);expect(item,isNotNull);expect(item!.fr,isNotEmpty);expect(item.en,isNotEmpty);expect(item.ar,isNotEmpty);expect(item.regions,contains(MealFoodRegion.universal));expect(hasCodeFoodPictogramBatch32(id),isTrue);expect(searchMealFoods(item.fr).map((e)=>e.id),contains(id));expect(item.category,MealFoodCategory.breadGrain);}});
}
