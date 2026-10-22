import 'package:flutter_test/flutter_test.dart';
import 'package:amina/core/data/meal_food_catalog.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter_batch33.dart';

void main(){
  const ids=<String>['palestinian_musakhan','palestinian_qidreh','jerusalem_kaak'];
  test('B33 remains the certified 401-item prefix after later batches',(){expect(mealFoodCatalog.length,greaterThanOrEqualTo(401));expect(mealFoodCatalog.take(398).length,398);expect(mealFoodCatalog.skip(398).take(3).map((e)=>e.id).toList(),ids);expect(mealFoodCatalog.take(401).map((e)=>e.id).toSet().length,401);});
  test('B33 labels search categories and native pictograms are complete',(){for(final id in ids){final item=mealFoodById(id);expect(item,isNotNull);expect(item!.fr,isNotEmpty);expect(item.en,isNotEmpty);expect(item.ar,isNotEmpty);expect(item.regions,contains(MealFoodRegion.universal));expect(hasCodeFoodPictogramBatch33(id),isTrue);expect(searchMealFoods(item.fr).map((e)=>e.id),contains(id));}expect(mealFoodById('palestinian_musakhan')!.category,MealFoodCategory.meatPoultry);expect(mealFoodById('palestinian_qidreh')!.category,MealFoodCategory.breadGrain);expect(mealFoodById('jerusalem_kaak')!.category,MealFoodCategory.breadGrain);});
}
