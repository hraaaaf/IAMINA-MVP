import 'package:flutter_test/flutter_test.dart';
import 'package:amina/core/data/meal_food_catalog.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter_batch28.dart';

void main(){
 const ids=<String>['moroccan_pastilla','marrakech_tanjia','moroccan_mrouzia'];
 test('B28 remains the certified 386-item prefix after B29',(){final prefix=mealFoodCatalog.take(386).toList();expect(prefix.length,386);expect(prefix.skip(383).map((e)=>e.id).toList(),ids);expect(prefix.map((e)=>e.id).toSet().length,386);});
 test('B28 labels, search, categories and native pictograms are complete',(){for(final id in ids){final item=mealFoodById(id);expect(item,isNotNull);expect(item!.fr,isNotEmpty);expect(item.en,isNotEmpty);expect(item.ar,isNotEmpty);expect(hasCodeFoodPictogramBatch28(id),isTrue);expect(searchMealFoods(item.fr).map((e)=>e.id),contains(id));}expect(mealFoodById('moroccan_pastilla')!.category,MealFoodCategory.other);expect(mealFoodById('marrakech_tanjia')!.category,MealFoodCategory.meatPoultry);expect(mealFoodById('moroccan_mrouzia')!.category,MealFoodCategory.meatPoultry);});
}
