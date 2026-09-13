import 'package:amina/features/journal/widgets/food_pictogram_painter.dart';
import 'package:amina/features/journal/widgets/food_pictogram_painter_batch2.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('native pictogram launch coverage reaches 48 without overlap', () {
    expect(codeFoodPictogramIds.length, 24);
    expect(codeFoodPictogramBatch2Ids.length, 24);
    expect(codeFoodPictogramIds.intersection(codeFoodPictogramBatch2Ids), isEmpty);
    expect(
      <String>{...codeFoodPictogramIds, ...codeFoodPictogramBatch2Ids}.length,
      48,
    );
  });
}
