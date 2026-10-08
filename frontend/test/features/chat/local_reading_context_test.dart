import 'package:amina/features/companion/local_reading_context.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('recognizes a first reading request across languages', () {
    expect(refersToRecordedGlucose('Ma première mesure ?'), isTrue);
    expect(refersToRecordedGlucose('What was my glucose reading?'), isTrue);
    expect(refersToRecordedGlucose('قياس سكر'), isTrue);
    expect(refersToRecordedGlucose('Salut IAmina'), isFalse);
  });

  test('missing local reading never implies an empty server account', () {
    for (final language in ['fr', 'en', 'ar']) {
      final copy = localReadingUnavailableFact(language);
      expect(copy, isNotEmpty);
      expect(copy, isNot(contains('128')));
    }
    expect(localReadingUnavailableFact('fr'), contains('sur cet appareil'));
    expect(localReadingUnavailableFact('fr'), contains('serveur'));
    expect(localReadingUnavailableFact('en'), contains('this device'));
    expect(localReadingUnavailableFact('en'), contains('server'));
    expect(localReadingUnavailableFact('ar'), contains('الجهاز'));
    expect(localReadingUnavailableFact('ar'), contains('الخادم'));
  });

  test('local synchronization status never promises server AI context', () {
    for (final language in ['fr', 'en', 'ar']) {
      final pending = localReadingSyncDisclosure('pending', language);
      final synced = localReadingSyncDisclosure('synced', language);
      final failed = localReadingSyncDisclosure(
        'pending',
        language,
        syncFailed: true,
      );
      expect(pending, isNotEmpty);
      expect(synced, isNotEmpty);
      expect(failed, isNotEmpty);
      expect(pending, isNot(equals(synced)));
      expect(failed, isNot(equals(pending)));
      expect(localReadingSyncDisclosure(null, language), isEmpty);
    }
    expect(localReadingSyncDisclosure('pending', 'fr'),
        contains('en attente de synchronisation'));
    expect(localReadingSyncDisclosure('synced', 'fr'),
        contains('son accès par IAmina n’est pas vérifié'));
    expect(localReadingSyncDisclosure('pending', 'en'),
        contains('awaiting synchronization'));
    expect(localReadingSyncDisclosure('synced', 'en'),
        contains('unverified'));
    expect(localReadingSyncDisclosure('pending', 'ar'),
        contains('انتظار المزامنة'));
    expect(localReadingSyncDisclosure('synced', 'ar'),
        contains('التحقق'));
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
