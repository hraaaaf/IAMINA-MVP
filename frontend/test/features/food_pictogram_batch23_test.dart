import 'package:flutter_test/flutter_test.dart';
import 'package:amina/core/data/meal_food_catalog.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter_batch23.dart';

void main(){
 const ids=<String>['yemeni_saltah','yemeni_fahsa','yemeni_bint_al_sahn'];
 test('B23 remains the certified 371-item prefix after B24',(){expect(mealFoodCatalog.length,greaterThanOrEqualTo(371));expect(mealFoodCatalog.skip(368).take(3).map((e)=>e.id).toList(),ids);expect(mealFoodCatalog.take(371).map((e)=>e.id).toSet().length,371);});
 test('B23 labels, search, category and native pictograms are complete',(){for(final id in ids){final item=mealFoodById(id);expect(item,isNotNull);expect(item!.fr,isNotEmpty);expect(item.en,isNotEmpty);expect(item.ar,isNotEmpty);expect(hasCodeFoodPictogramBatch23(id),isTrue);expect(searchMealFoods(item.fr).map((e)=>e.id),contains(id));}expect(mealFoodById('yemeni_saltah')!.category,MealFoodCategory.other);expect(mealFoodById('yemeni_fahsa')!.category,MealFoodCategory.other);expect(mealFoodById('yemeni_bint_al_sahn')!.category,MealFoodCategory.sweetDessert);});
}
