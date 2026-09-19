import 'package:flutter_test/flutter_test.dart';
import 'package:amina/core/data/meal_food_catalog.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter_batch26.dart';

void main(){
 const ids=<String>['libyan_bazin','libyan_mbakbaka','libyan_shorba'];
 test('B26 remains the certified 377 to 380 prefix',(){expect(mealFoodCatalog.length,greaterThanOrEqualTo(380));expect(mealFoodCatalog.skip(377).take(3).map((e)=>e.id).toList(),ids);expect(mealFoodCatalog.map((e)=>e.id).toSet().length,mealFoodCatalog.length);});
 test('B26 labels, search, categories and native pictograms are complete',(){for(final id in ids){final item=mealFoodById(id);expect(item,isNotNull);expect(item!.fr,isNotEmpty);expect(item.en,isNotEmpty);expect(item.ar,isNotEmpty);expect(hasCodeFoodPictogramBatch26(id),isTrue);expect(searchMealFoods(item.fr).map((e)=>e.id),contains(id));}expect(mealFoodById('libyan_bazin')!.category,MealFoodCategory.breadGrain);expect(mealFoodById('libyan_mbakbaka')!.category,MealFoodCategory.other);expect(mealFoodById('libyan_shorba')!.category,MealFoodCategory.soup);});
}
