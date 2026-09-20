import 'package:flutter_test/flutter_test.dart';
import 'package:amina/core/data/meal_food_catalog.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter_batch30.dart';

void main(){
  const ids=<String>['pizza_margherita','spaghetti_carbonara','lasagne_bolognese'];
  test('B30 appends three international Italy concepts after certified B29 baseline',(){
    expect(mealFoodCatalog.length,392);
    expect(mealFoodCatalog.take(389).length,389);
    expect(mealFoodCatalog.skip(389).map((e)=>e.id).toList(),ids);
    expect(mealFoodCatalog.map((e)=>e.id).toSet().length,392);
  });
  test('B30 labels search categories region and native pictograms are complete',(){
    for(final id in ids){
      final item=mealFoodById(id);
      expect(item,isNotNull);
      expect(item!.fr,isNotEmpty);
      expect(item.en,isNotEmpty);
      expect(item.ar,isNotEmpty);
      expect(item.regions,contains(MealFoodRegion.universal));
      expect(hasCodeFoodPictogramBatch30(id),isTrue);
      expect(searchMealFoods(item.fr).map((e)=>e.id),contains(id));
    }
    expect(mealFoodById('pizza_margherita')!.category,MealFoodCategory.snackFastFood);
    expect(mealFoodById('spaghetti_carbonara')!.category,MealFoodCategory.breadGrain);
    expect(mealFoodById('lasagne_bolognese')!.category,MealFoodCategory.breadGrain);
  });
}
