import 'package:amina/core/data/meal_food_catalog.dart';
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
import 'package:amina/features/journal/widgets/food_pictogram_painter_batch16.dart';
import 'package:flutter_test/flutter_test.dart';

void main(){
  test('sixteen pictogram batches cover the complete 349-item catalog',(){
    final fullBatches=<Set<String>>[codeFoodPictogramIds,codeFoodPictogramBatch2Ids,codeFoodPictogramBatch3Ids,codeFoodPictogramBatch4Ids,codeFoodPictogramBatch5Ids,codeFoodPictogramBatch6Ids,codeFoodPictogramBatch7Ids,codeFoodPictogramBatch8Ids,codeFoodPictogramBatch9Ids,codeFoodPictogramBatch10Ids,codeFoodPictogramBatch11Ids,codeFoodPictogramBatch12Ids,codeFoodPictogramBatch13Ids,codeFoodPictogramBatch15Ids];
    for(final batch in fullBatches){expect(batch.length,24);}
    expect(codeFoodPictogramBatch14Ids.length,10);
    expect(codeFoodPictogramBatch16Ids.length,3);
    final batches=<Set<String>>[codeFoodPictogramIds,codeFoodPictogramBatch2Ids,codeFoodPictogramBatch3Ids,codeFoodPictogramBatch4Ids,codeFoodPictogramBatch5Ids,codeFoodPictogramBatch6Ids,codeFoodPictogramBatch7Ids,codeFoodPictogramBatch8Ids,codeFoodPictogramBatch9Ids,codeFoodPictogramBatch10Ids,codeFoodPictogramBatch11Ids,codeFoodPictogramBatch12Ids,codeFoodPictogramBatch13Ids,codeFoodPictogramBatch14Ids,codeFoodPictogramBatch15Ids,codeFoodPictogramBatch16Ids];
    for(var i=0;i<batches.length;i++){for(var j=i+1;j<batches.length;j++){expect(batches[i].intersection(batches[j]),isEmpty);}}
    final union=batches.expand((batch)=>batch).toSet();
    expect(union.length,349);
    expect(union,mealFoodCatalog.map((item)=>item.id).toSet());
  });
}
