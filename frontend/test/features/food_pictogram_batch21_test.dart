import 'package:flutter_test/flutter_test.dart';
import 'package:amina/core/data/meal_food_catalog.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter_batch21.dart';

void main(){
 const ids=<String>['tunisian_brik','tunisian_lablabi','tunisian_kafteji'];
 test('B21 certified Tunisia prefix remains intact after later batches',(){expect(mealFoodCatalog.length,greaterThanOrEqualTo(365));expect(mealFoodCatalog.skip(362).take(3).map((e)=>e.id).toList(),ids);expect(mealFoodCatalog.map((e)=>e.id).toSet().length,mealFoodCatalog.length);});
 test('B21 labels, search, category and native pictograms remain complete',(){for(final id in ids){final item=mealFoodById(id);expect(item,isNotNull);expect(item!.fr,isNotEmpty);expect(item.en,isNotEmpty);expect(item.ar,isNotEmpty);expect(hasCodeFoodPictogramBatch21(id),isTrue);expect(searchMealFoods(item.fr).map((e)=>e.id),contains(id));}expect(mealFoodById('tunisian_brik')!.category,MealFoodCategory.snackFastFood);expect(mealFoodById('tunisian_lablabi')!.category,MealFoodCategory.soup);expect(mealFoodById('tunisian_kafteji')!.category,MealFoodCategory.snackFastFood);});
}
