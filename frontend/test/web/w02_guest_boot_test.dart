import 'package:amina/data/drift/database.dart';
import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:drift/drift.dart' as drift;
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter_test/flutter_test.dart';

Uri _ciWasm() {
  const value = String.fromEnvironment('W02_TEST_WASM_URL');
  final uri = Uri.tryParse(value);
  if (uri == null || uri.scheme != 'http' || uri.host != '127.0.0.1' ||
      uri.port != 7399 || uri.path != '/sqlite3.wasm') {
    throw StateError('w02_test_wasm_url_must_be_loopback');
  }
  return uri;
}

void main() {
  test('W02 web guest opens isolated volatile SQLite and does not retain rows', () async {
    expect(kIsWeb, isTrue);
    final guest = AppDatabase.guestAuditOnly(sqlite3Wasm: _ciWasm());
    expect(guest.patientVaultScope?.databaseName, 'amina_vault_v1_audit');
    try {
      final initially = await guest.select(guest.patientProfiles).get();
      expect(initially, isEmpty);
      await guest.into(guest.patientProfiles).insert(
        PatientProfilesCompanion.insert(
          userId: const drift.Value(1),
          updatedAt: DateTime.utc(2026, 10, 28),
        ),
      );
      expect(await guest.select(guest.patientProfiles).get(), hasLength(1));
    } finally {
      await guest.close();
    }

    final newGuest = AppDatabase.guestAuditOnly(sqlite3Wasm: _ciWasm());
    try {
      expect(await newGuest.select(newGuest.patientProfiles).get(), isEmpty);
    } finally {
      await newGuest.close();
    }
  });

  test('W02 still refuses authenticated unencrypted patient vault on Web', () {
    expect(kIsWeb, isTrue);
    expect(
      () => AppDatabase.forPatientVault(PatientVaultScope.nativeDjango(734)),
      throwsA(isA<StateError>().having(
        (e) => e.message, 'message', 'encrypted_web_patient_vault_unavailable',
      )),
    );
  });
}
