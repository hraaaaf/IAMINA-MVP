import 'package:flutter_test/flutter_test.dart';
import 'package:amina/core/data/meal_food_catalog.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter_batch22.dart';

void main(){
 const ids=<String>['algerian_rechta','algerian_chakhchoukha','algerian_mhadjeb'];
 test('B22 appends three Algeria concepts after certified B21 baseline',(){expect(mealFoodCatalog.length,368);expect(mealFoodCatalog.take(365).length,365);expect(mealFoodCatalog.skip(365).map((e)=>e.id).toList(),ids);expect(mealFoodCatalog.map((e)=>e.id).toSet().length,368);});
 test('B22 labels, search, category and native pictograms are complete',(){for(final id in ids){final item=mealFoodById(id);expect(item,isNotNull);expect(item!.fr,isNotEmpty);expect(item.en,isNotEmpty);expect(item.ar,isNotEmpty);expect(hasCodeFoodPictogramBatch22(id),isTrue);expect(searchMealFoods(item.fr).map((e)=>e.id),contains(id));}expect(mealFoodById('algerian_rechta')!.category,MealFoodCategory.other);expect(mealFoodById('algerian_chakhchoukha')!.category,MealFoodCategory.other);expect(mealFoodById('algerian_mhadjeb')!.category,MealFoodCategory.snackFastFood);});
}
