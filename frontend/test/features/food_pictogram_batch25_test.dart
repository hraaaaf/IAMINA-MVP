import 'package:flutter_test/flutter_test.dart';
import 'package:amina/core/data/meal_food_catalog.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter_batch25.dart';

void main(){
 const ids=<String>['saudi_jareesh','saudi_saleeg','saudi_marqooq'];
 test('B25 appends three Saudi concepts after certified B24 baseline',(){expect(mealFoodCatalog.length,greaterThanOrEqualTo(377));expect(mealFoodCatalog.take(374).length,374);expect(mealFoodCatalog.skip(374).take(3).map((e)=>e.id).toList(),ids);expect(mealFoodCatalog.map((e)=>e.id).toSet().length,mealFoodCatalog.length);});
 test('B25 labels, search, Gulf region, categories and native pictograms are complete',(){for(final id in ids){final item=mealFoodById(id);expect(item,isNotNull);expect(item!.fr,isNotEmpty);expect(item.en,isNotEmpty);expect(item.ar,isNotEmpty);expect(item.regions,contains(MealFoodRegion.gulf));expect(item.category,MealFoodCategory.gulfDish);expect(hasCodeFoodPictogramBatch25(id),isTrue);expect(searchMealFoods(item.fr).map((e)=>e.id),contains(id));}});
}
