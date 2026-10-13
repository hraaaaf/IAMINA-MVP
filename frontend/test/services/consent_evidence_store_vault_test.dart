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

  test('D7 consent evidence is isolated between two native vaults', () async {
    final a = ConsentEvidenceStore.forPatientVault(
      PatientVaultScope.nativeDjango(734),
    );
    final b = ConsentEvidenceStore.forPatientVault(
      PatientVaultScope.nativeDjango(812),
    );
    final claim = ConsentNoticeContract.forLocale('fr');
    await a.write(claim);
    expect(await a.hasCurrentEvidence(), isTrue);
    expect(await b.hasCurrentEvidence(), isFalse);

    await b.write(ConsentNoticeContract.forLocale('ar'));
    expect(await a.hasCurrentEvidence(), isTrue);
    expect(await b.hasCurrentEvidence(), isTrue);
    await b.clear();
    expect(await a.hasCurrentEvidence(), isTrue);
    expect(await b.hasCurrentEvidence(), isFalse);
  });

  test('D7 legacy consent evidence never migrates to native implicitly', () async {
    final legacy = ConsentEvidenceStore();
    final native = ConsentEvidenceStore.forPatientVault(
      PatientVaultScope.nativeDjango(734),
    );
    await legacy.write(ConsentNoticeContract.forLocale('fr'));
    expect(await legacy.hasCurrentEvidence(), isTrue);
    expect(await native.hasCurrentEvidence(), isFalse);
  });

  test('D7 local/audit consent cannot leak into a native account', () async {
    final local = ConsentEvidenceStore.forPatientVault(
      PatientVaultScope.deviceLocal('b32afafd-8d9d-4ad4-8513-7dcfb54299a6'),
    );
    final audit = ConsentEvidenceStore.forPatientVault(
      PatientVaultScope.auditOnly(),
    );
    final native = ConsentEvidenceStore.forPatientVault(
      PatientVaultScope.nativeDjango(734),
    );
    await local.write(ConsentNoticeContract.forLocale('fr'));
    await audit.write(ConsentNoticeContract.forLocale('ar'));
    expect(await native.hasCurrentEvidence(), isFalse);
    expect(await local.hasCurrentEvidence(), isTrue);
    expect(await audit.hasCurrentEvidence(), isTrue);
  });
}
