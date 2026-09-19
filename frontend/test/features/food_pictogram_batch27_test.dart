import 'package:flutter_test/flutter_test.dart';
import 'package:amina/core/data/meal_food_catalog.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter_batch27.dart';

void main(){
 const ids=<String>['omani_madrouba','omani_arsia','omani_paplou'];
 test('B27 appends three Oman concepts after certified B26 baseline',(){expect(mealFoodCatalog.length,383);expect(mealFoodCatalog.take(380).length,380);expect(mealFoodCatalog.skip(380).map((e)=>e.id).toList(),ids);expect(mealFoodCatalog.map((e)=>e.id).toSet().length,383);});
 test('B27 labels, search, categories and native pictograms are complete',(){for(final id in ids){final item=mealFoodById(id);expect(item,isNotNull);expect(item!.fr,isNotEmpty);expect(item.en,isNotEmpty);expect(item.ar,isNotEmpty);expect(hasCodeFoodPictogramBatch27(id),isTrue);expect(searchMealFoods(item.fr).map((e)=>e.id),contains(id));}expect(mealFoodById('omani_madrouba')!.category,MealFoodCategory.gulfDish);expect(mealFoodById('omani_arsia')!.category,MealFoodCategory.gulfDish);expect(mealFoodById('omani_paplou')!.category,MealFoodCategory.soup);});
}
