import 'package:amina/features/journal/widgets/food_pictogram_painter.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter_batch2.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter_batch3.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter_batch4.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter_batch5.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('native food pictogram batches are fixed, disjoint and total 120', () {
    expect(codeFoodPictogramIds.length, 24);
    expect(codeFoodPictogramBatch2Ids.length, 24);
    expect(codeFoodPictogramBatch3Ids.length, 24);
    expect(codeFoodPictogramBatch4Ids.length, 24);
    expect(codeFoodPictogramBatch5Ids.length, 24);

    final batches = <Set<String>>[
      codeFoodPictogramIds,
      codeFoodPictogramBatch2Ids,
      codeFoodPictogramBatch3Ids,
      codeFoodPictogramBatch4Ids,
      codeFoodPictogramBatch5Ids,
    ];
    for (var i = 0; i < batches.length; i++) {
      for (var j = i + 1; j < batches.length; j++) {
        expect(batches[i].intersection(batches[j]), isEmpty);
      }
    }

    expect(<String>{for (final batch in batches) ...batch}.length, 120);
  });
}
