import 'package:amina/core/data/meal_food_catalog.dart';
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
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';

Finder _batch14Art()=>find.byWidgetPredicate((widget)=>widget is CustomPaint&&widget.painter is FoodPictogramPainterBatch14);

void main(){
  test('batch 14 preserves certified V3 native baseline of 322',(){
    const expected=<String>{'sandwich','tacos_wrap','chicken_caesar_salad','tuna_salad','greek_salad','chorba','lentil_soup','vegetable_soup','chicken_soup','tomato_soup'};
    expect(codeFoodPictogramBatch14Ids,expected);
    expect(codeFoodPictogramBatch14Ids.length,10);
    final previous=<String>{...codeFoodPictogramIds,...codeFoodPictogramBatch2Ids,...codeFoodPictogramBatch3Ids,...codeFoodPictogramBatch4Ids,...codeFoodPictogramBatch5Ids,...codeFoodPictogramBatch6Ids,...codeFoodPictogramBatch7Ids,...codeFoodPictogramBatch8Ids,...codeFoodPictogramBatch9Ids,...codeFoodPictogramBatch10Ids,...codeFoodPictogramBatch11Ids,...codeFoodPictogramBatch12Ids,...codeFoodPictogramBatch13Ids};
    expect(codeFoodPictogramBatch14Ids.intersection(previous),isEmpty);
    for(final id in codeFoodPictogramBatch14Ids){expect(mealFoodById(id),isNotNull,reason:'Missing catalog food: $id');}
    final union=<String>{...previous,...codeFoodPictogramBatch14Ids};
    expect(union.length,322);
    expect(mealFoodCatalog.map((item)=>item.id).toSet().containsAll(union),isTrue);
  });

  testWidgets('batch 14 renders soup art with localized semantics',(tester)async{
    final item=mealFoodById('lentil_soup')!;
    await tester.pumpWidget(MaterialApp(locale:const Locale('fr'),supportedLocales:const <Locale>[Locale('fr')],localizationsDelegates:GlobalMaterialLocalizations.delegates,home:Scaffold(body:FoodPictogram(item:item,size:48))));
    await tester.pumpAndSettle();
    expect(find.text(item.visual),findsNothing);
    expect(_batch14Art(),findsOneWidget);
    expect(tester.getSemantics(find.byType(FoodPictogram)).label,contains('Soupe de lentilles'));
  });
}
