import 'package:amina/services/consent_evidence_store.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

class _SecureStorageMock extends Mock implements FlutterSecureStorage {}

void main() {
  const key = 'iamina.ai_consent.local_declined_v1';

  test('device refusal survives store recreation until explicit clearing', () async {
    String? marker;
    final storage = _SecureStorageMock();
    when(() => storage.read(key: key)).thenAnswer((_) async => marker);
    when(() => storage.write(key: key, value: '1')).thenAnswer((_) async {
      marker = '1';
    });
    when(() => storage.delete(key: key)).thenAnswer((_) async {
      marker = null;
    });

    final before = ConsentEvidenceStore(storage: storage);
    expect(await before.hasPersistedLocalDecline(), isFalse);
    await before.persistLocalDecline();
    expect(marker, '1');

    // New store instance shares only the same per-installation secure data.
    final restarted = ConsentEvidenceStore(storage: storage);
    expect(await restarted.hasPersistedLocalDecline(), isTrue);

    await restarted.clearPersistedLocalDecline();
    expect(await before.hasPersistedLocalDecline(), isFalse);
    verify(() => storage.write(key: key, value: '1')).called(1);
    verify(() => storage.delete(key: key)).called(1);
  });

  test('unknown non-null marker fails closed', () async {
    final storage = _SecureStorageMock();
    when(() => storage.read(key: key)).thenAnswer((_) async => 'malformed');
    expect(
      await ConsentEvidenceStore(storage: storage).hasPersistedLocalDecline(),
      isTrue,
    );
  });

  test('secure storage read error propagates to fail-closed bootstrap', () async {
    final storage = _SecureStorageMock();
    when(() => storage.read(key: key)).thenThrow(StateError('locked'));
    await expectLater(
      ConsentEvidenceStore(storage: storage).hasPersistedLocalDecline(),
      throwsStateError,
    );
  });
}
