import 'package:amina/features/companion/local_reading_context.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('recognizes a first reading request across languages', () {
    expect(refersToRecordedGlucose('Ma première mesure ?'), isTrue);
    expect(refersToRecordedGlucose('What was my glucose reading?'), isTrue);
    expect(refersToRecordedGlucose('قياس سكر'), isTrue);
    expect(refersToRecordedGlucose('Salut IAmina'), isFalse);
  });

  test('uses local provenance and avoids trend inference', () {
    final fr = localReadingFact(128, 'fr');
    expect(fr, contains('128 mg/dL'));
    expect(fr, contains('sur cet appareil'));
    expect(fr, contains('n’est pas vérifiée'));
    expect(fr, contains('ne permet pas'));
    expect(localReadingFact(128.5, 'en'), contains('128.5 mg/dL'));
    expect(localReadingFact(128, 'ar'), contains('128 mg/dL'));
  });
}
