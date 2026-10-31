import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:amina/services/consent_evidence_store.dart';
import 'package:amina/services/consent_notice_contract.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    FlutterSecureStorage.setMockInitialValues({});
  });

  test('D7 withdrawal-pending marker survives owner A reload and excludes B', () async {
    final scopeA = PatientVaultScope.nativeDjango(1001);
    final scopeB = PatientVaultScope.nativeDjango(1002);
    final a = ConsentEvidenceStore.forPatientVault(scopeA);
    final b = ConsentEvidenceStore.forPatientVault(scopeB);
    final claim = ConsentNoticeContract.forLocale('fr');
    await a.write(claim);
    await b.write(claim);
    expect(await a.hasCurrentEvidence(), isTrue);
    expect(await b.hasCurrentEvidence(), isTrue);

    await a.markWithdrawalPending();
    expect(await a.hasWithdrawalPending(), isTrue);
    expect(await a.readCurrent(), isNull);
    expect(await b.hasWithdrawalPending(), isFalse);
    expect(await b.hasCurrentEvidence(), isTrue);

    final aReloaded = ConsentEvidenceStore.forPatientVault(scopeA);
    expect(await aReloaded.hasWithdrawalPending(), isTrue);
    expect(await aReloaded.hasCurrentEvidence(), isFalse);

    await aReloaded.clear();
    await aReloaded.clearWithdrawalPending();
    expect(await aReloaded.hasWithdrawalPending(), isFalse);
    expect(await aReloaded.hasCurrentEvidence(), isFalse);
    expect(await b.hasCurrentEvidence(), isTrue);
  });

  test('pending marker only disappears after explicit clear', () async {
    final store = ConsentEvidenceStore.forPatientVault(
      PatientVaultScope.nativeDjango(42),
    );
    await store.markWithdrawalPending();
    expect(await store.hasWithdrawalPending(), isTrue);
    await store.clear();
    expect(await store.hasWithdrawalPending(), isTrue);
    await store.clearWithdrawalPending();
    expect(await store.hasWithdrawalPending(), isFalse);
  });
}
