import 'package:amina/features/journal/widgets/food_pictogram_painter.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter_batch2.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter_batch3.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('native pictogram coverage reaches 72 without overlap', () {
    expect(codeFoodPictogramIds.length, 24);
    expect(codeFoodPictogramBatch2Ids.length, 24);
    expect(codeFoodPictogramBatch3Ids.length, 24);
    expect(codeFoodPictogramIds.intersection(codeFoodPictogramBatch2Ids), isEmpty);
    expect(codeFoodPictogramIds.intersection(codeFoodPictogramBatch3Ids), isEmpty);
    expect(
      codeFoodPictogramBatch2Ids.intersection(codeFoodPictogramBatch3Ids),
      isEmpty,
    );
    expect(
      <String>{
        ...codeFoodPictogramIds,
        ...codeFoodPictogramBatch2Ids,
        ...codeFoodPictogramBatch3Ids,
      }.length,
      72,
    );
  });
}
