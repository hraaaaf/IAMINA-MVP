import 'package:flutter_test/flutter_test.dart';
import 'package:iamina/core/data/meal_food_catalog.dart';
import 'package:iamina/features/journal/widgets/food_pictogram_painter_batch19.dart';

void main(){
 const ids=<String>['qatari_saloona','qatari_margoog','qatari_sago'];
 test('B19 appends three Qatar concepts after certified B18 baseline',(){expect(mealFoodCatalog.length,359);expect(mealFoodCatalog.take(356).length,356);expect(mealFoodCatalog.skip(356).map((e)=>e.id).toList(),ids);expect(mealFoodCatalog.map((e)=>e.id).toSet().length,359);});
 test('B19 labels, search, category and native pictograms are complete',(){for(final id in ids){final item=mealFoodById(id);expect(item,isNotNull);expect(item!.fr,isNotEmpty);expect(item.en,isNotEmpty);expect(item.ar,isNotEmpty);expect(hasCodeFoodPictogramBatch19(id),isTrue);expect(searchMealFoods(item.fr).map((e)=>e.id),contains(id));}expect(mealFoodById('qatari_saloona')!.category,MealFoodCategory.gulfDish);expect(mealFoodById('qatari_margoog')!.category,MealFoodCategory.gulfDish);expect(mealFoodById('qatari_sago')!.category,MealFoodCategory.sweetDessert);});
}
