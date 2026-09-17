import 'package:flutter_test/flutter_test.dart';
import 'package:amina/core/data/meal_food_catalog.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter_batch19.dart';

void main(){
 const ids=<String>['qatari_saloona','qatari_margoog','qatari_sago'];
 test('B19 remains the certified 359-item prefix after later batches',(){expect(mealFoodCatalog.length,greaterThanOrEqualTo(359));expect(mealFoodCatalog.take(359).skip(356).map((e)=>e.id).toList(),ids);expect(mealFoodCatalog.take(359).map((e)=>e.id).toSet().length,359);});
 test('B19 labels, search, category and native pictograms are complete',(){for(final id in ids){final item=mealFoodById(id);expect(item,isNotNull);expect(item!.fr,isNotEmpty);expect(item.en,isNotEmpty);expect(item.ar,isNotEmpty);expect(hasCodeFoodPictogramBatch19(id),isTrue);expect(searchMealFoods(item.fr).map((e)=>e.id),contains(id));}expect(mealFoodById('qatari_saloona')!.category,MealFoodCategory.gulfDish);expect(mealFoodById('qatari_margoog')!.category,MealFoodCategory.gulfDish);expect(mealFoodById('qatari_sago')!.category,MealFoodCategory.sweetDessert);});
}
