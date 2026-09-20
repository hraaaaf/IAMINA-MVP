import 'package:flutter_test/flutter_test.dart';
import 'package:amina/core/data/meal_food_catalog.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter_batch28.dart';

void main(){
 const ids=<String>['moroccan_pastilla','marrakech_tanjia','moroccan_mrouzia'];
 test('B28 appends three Morocco concepts after certified B27 baseline',(){expect(mealFoodCatalog.length,386);expect(mealFoodCatalog.take(383).length,383);expect(mealFoodCatalog.skip(383).map((e)=>e.id).toList(),ids);expect(mealFoodCatalog.map((e)=>e.id).toSet().length,386);});
 test('B28 labels, search, categories and native pictograms are complete',(){for(final id in ids){final item=mealFoodById(id);expect(item,isNotNull);expect(item!.fr,isNotEmpty);expect(item.en,isNotEmpty);expect(item.ar,isNotEmpty);expect(hasCodeFoodPictogramBatch28(id),isTrue);expect(searchMealFoods(item.fr).map((e)=>e.id),contains(id));}expect(mealFoodById('moroccan_pastilla')!.category,MealFoodCategory.other);expect(mealFoodById('marrakech_tanjia')!.category,MealFoodCategory.meatPoultry);expect(mealFoodById('moroccan_mrouzia')!.category,MealFoodCategory.meatPoultry);});
}
