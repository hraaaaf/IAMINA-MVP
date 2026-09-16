import 'package:amina/core/data/meal_food_catalog.dart';
import 'package:amina/core/data/meal_food_catalog_v3.dart' as v3;
import 'package:amina/features/journal/widgets/food_pictogram.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter_batch2.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter_batch3.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter_batch4.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter_batch5.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter_batch6.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter_batch7.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter_batch8.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter_batch9.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter_batch10.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter_batch11.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter_batch12.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter_batch13.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter_batch14.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter_batch15.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';

Finder _batch15Art()=>find.byWidgetPredicate((widget)=>widget is CustomPaint&&widget.painter is FoodPictogramPainterBatch15);

void main(){
  test('Gulf Core B15 appends 24 foods without changing certified V3 baseline',(){
    const expected=<String>{'matazeez','areeka','masoub','haneeth','maghsh','samak_mkashan','mahshoosh','marsah','gahwa_gishr','tasabea','mashgotha','miva_bread','qabooli','mishkak','omani_halwa','lamb_khuzi','bahraini_halwa','malgoum','louba_bahraini','bahraini_tikka','tashreeb','murabiyan','mutabbaq_zubaidi','dakkous'};
    expect(codeFoodPictogramBatch15Ids,expected);
    expect(codeFoodPictogramBatch15Ids.length,24);
    expect(v3.mealFoodCatalog.length,322);
    expect(mealFoodCatalog.length,greaterThanOrEqualTo(346));
    expect(mealFoodCatalog.take(322).map((item)=>item.id).toList(),v3.mealFoodCatalog.map((item)=>item.id).toList());
    final baselineNative=<String>{...codeFoodPictogramIds,...codeFoodPictogramBatch2Ids,...codeFoodPictogramBatch3Ids,...codeFoodPictogramBatch4Ids,...codeFoodPictogramBatch5Ids,...codeFoodPictogramBatch6Ids,...codeFoodPictogramBatch7Ids,...codeFoodPictogramBatch8Ids,...codeFoodPictogramBatch9Ids,...codeFoodPictogramBatch10Ids,...codeFoodPictogramBatch11Ids,...codeFoodPictogramBatch12Ids,...codeFoodPictogramBatch13Ids,...codeFoodPictogramBatch14Ids};
    expect(baselineNative.length,322);
    expect(codeFoodPictogramBatch15Ids.intersection(baselineNative),isEmpty);
    final union=<String>{...baselineNative,...codeFoodPictogramBatch15Ids};
    expect(union.length,346);
    expect(mealFoodCatalog.take(346).map((item)=>item.id).toSet(),union);
    for(final id in codeFoodPictogramBatch15Ids){expect(mealFoodById(id),isNotNull,reason:'Missing Gulf Core food: $id');}
  });

  test('new Gulf foods survive search and meal-item serialization',(){
    expect(searchMealFoods('qabooli',limit:3).first.id,'qabooli');
    expect(searchMealFoods('قبولي',limit:3).first.id,'qabooli');
    expect(searchMealFoods('mishkak',limit:3).first.id,'mishkak');
    final encoded=encodeMealItemIds(<String>['qabooli','murabiyan']);
    expect(decodeMealItemIds(encoded),containsAll(<String>['qabooli','murabiyan']));
  });

  testWidgets('B15 renders native Gulf art with localized semantics',(tester)async{
    final item=mealFoodById('qabooli')!;
    await tester.pumpWidget(MaterialApp(locale:const Locale('fr'),supportedLocales:const <Locale>[Locale('fr')],localizationsDelegates:GlobalMaterialLocalizations.delegates,home:Scaffold(body:FoodPictogram(item:item,size:48))));
    await tester.pumpAndSettle();
    expect(find.text(item.visual),findsNothing);
    expect(_batch15Art(),findsOneWidget);
    expect(tester.getSemantics(find.byType(FoodPictogram)).label,contains('Qabooli omanais'));
  });
}
