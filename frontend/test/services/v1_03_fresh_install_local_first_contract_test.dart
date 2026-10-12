import 'dart:io';

import 'package:amina/data/drift/database.dart';
import 'package:amina/services/auth_service.dart';
import 'package:amina/services/companion_service.dart';
import 'package:amina/services/consent_evidence_store.dart';
import 'package:amina/services/consent_service.dart';
import 'package:amina/services/api_client.dart';
import 'package:drift/drift.dart' as drift;
import 'package:drift/native.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/testing.dart';
import 'package:mocktail/mocktail.dart';

class _StorageMock extends Mock implements FlutterSecureStorage {}

_StorageMock _deviceStorage(Map<String, String> onDevice) {
  final storage = _StorageMock();
  when(() => storage.read(key: any(named: 'key'))).thenAnswer(
    (call) async => onDevice[call.namedArguments[#key] as String],
  );
  when(
    () => storage.write(
      key: any(named: 'key'),
      value: any(named: 'value'),
    ),
  ).thenAnswer((call) async {
    onDevice[call.namedArguments[#key] as String] =
        call.namedArguments[#value] as String;
  });
  when(() => storage.delete(key: any(named: 'key'))).thenAnswer(
    (call) async {
      onDevice.remove(call.namedArguments[#key] as String);
    },
  );
  return storage;
}

void main() {
  test('fresh device enrolls and reopens without a server or remote token',
      () async {
    final device = <String, String>{};
    final storage = _deviceStorage(device);
    var httpCalls = 0;
    final network = MockClient((_) async {
      httpCalls++;
      throw StateError('First enrollment must not contact a server');
    });

    final first = AuthService(storage: storage, httpClient: network);
    await expectLater(first.enrollLocalDevice(), throwsStateError);
    await first.initialize();
    expect(first.isInitialized, isTrue);
    expect(first.isAuthenticated, isFalse);
    expect(first.hasRemoteApiCredential, isFalse);
    expect(device, isEmpty);

    await first.enrollLocalDevice();
    expect(first.isAuthenticated, isTrue);
    expect(first.isRemoteCredentialVerified, isFalse);
    expect(await first.getIdToken(), isNull);
    expect(device['iamina_local_session_v1'], 'enrolled');
    final deviceId = device['iamina_local_device_id_v1'];
    expect(deviceId, isNotNull);
    expect(deviceId, isNotEmpty);
    expect(device.containsKey('iamina_native_access_token'), isFalse);
    expect(httpCalls, 0);
    first.dispose();

    final reopened = AuthService(
      storage: storage,
      httpClient: MockClient((_) async {
        httpCalls++;
        throw StateError('Local reopen must not contact a server');
      }),
    );
    await reopened.initialize();
    expect(reopened.isAuthenticated, isTrue);
    expect(reopened.hasRemoteApiCredential, isFalse);
    expect(reopened.isRemoteCredentialVerified, isFalse);
    expect(device['iamina_local_device_id_v1'], deviceId);
    expect(httpCalls, 0);

    // Account creation remains explicitly disabled in the prelaunch build.
    expect(kRemoteAccountEnrollmentEnabled, isFalse);
    await expectLater(
      reopened.registerWithEmail('synthetic@example.invalid', 'not-a-secret'),
      throwsStateError,
    );
    expect(httpCalls, 0);

    await reopened.signOut();
    expect(reopened.isAuthenticated, isFalse);
    expect(device.containsKey('iamina_local_session_v1'), isFalse);
    expect(device.containsKey('iamina_local_device_id_v1'), isFalse);
    expect(httpCalls, 0);
    reopened.dispose();

    final afterSignout = AuthService(
      storage: storage,
      httpClient: MockClient((_) async {
        httpCalls++;
        throw StateError('Reopen after signout must stay offline');
      }),
    );
    await afterSignout.initialize();
    expect(afterSignout.isAuthenticated, isFalse);
    expect(afterSignout.hasRemoteApiCredential, isFalse);
    expect(httpCalls, 0);
    afterSignout.dispose();
  });

  test('first synthetic glucose log survives closing and reopening local SQLite',
      () async {
    final directory = await Directory.systemTemp.createTemp(
      'iamina-v103-first-install-',
    );
    addTearDown(() => directory.delete(recursive: true));
    final sqliteFile = File('${directory.path}/device-only.sqlite');

    final first = AppDatabase(NativeDatabase(sqliteFile));
    await first.into(first.logEntries).insert(
      LogEntriesCompanion.insert(
        createdAt: DateTime.utc(2026, 10, 12, 9),
        bloodSugar: 123.0,
        clientUuid: 'synthetic-first-install-log-001',
      ),
    );
    expect(await first.countLogs(), 1);
    await first.close();

    expect(await sqliteFile.exists(), isTrue);
    final reopened = AppDatabase(NativeDatabase(sqliteFile));
    addTearDown(reopened.close);
    final entries = await reopened.select(reopened.logEntries).get();
    expect(entries, hasLength(1));
    expect(entries.single.bloodSugar, 123.0);
    expect(entries.single.clientUuid, 'synthetic-first-install-log-001');
    expect(entries.single.syncStatus, 'pending');
  });

  test('pre-existing verified receipt cannot undo local AI refusal after reopen',
      () async {
    final device = <String, String>{};
    final storage = _deviceStorage(device);
    final evidence = ConsentEvidenceStore(storage: storage);
    final database = AppDatabase(NativeDatabase.memory());
    addTearDown(database.close);

    await database.into(database.patientProfiles).insert(
      PatientProfilesCompanion.insert(
        updatedAt: DateTime.utc(2026, 10, 12),
        userId: const drift.Value(1),
        aiConsentGivenAt: drift.Value(DateTime.utc(2026, 10, 12)),
      ),
    );
    final profile = await database.select(database.patientProfiles).getSingle();

    final initial = ConsentService(hasVerifiedEvidence: true)
      ..seedInitialProfile(profile);
    expect(initial.hasConsent, isTrue);
    initial.declineLocally();
    await evidence.persistLocalDecline();
    expect(initial.hasConsent, isFalse);
    initial.dispose();

    final restartedEvidence = ConsentEvidenceStore(storage: storage);
    final restarted = ConsentService(
      hasVerifiedEvidence: true,
      initiallyDeclinedLocally:
          await restartedEvidence.hasPersistedLocalDecline(),
    )..seedInitialProfile(profile);
    expect(restarted.hasConsent, isFalse);
    expect(restarted.hasDeclinedLocally, isTrue);

    var networkCalls = 0;
    final auth = AuthService(
      storage: storage,
      httpClient: MockClient((_) async {
        networkCalls++;
        throw StateError('Remote auth must remain unused');
      }),
    );
    await auth.initialize();
    final companion = CompanionService(
      authService: auth,
      consentService: restarted,
      httpClient: MockClient((_) async {
        networkCalls++;
        throw StateError('Locally declined AI must never leave device');
      }),
    );

    await expectLater(
      companion.sendChatMessage('SYNTHETIC_FRESH_INSTALL_NO_AI'),
      throwsA(
        isA<ProviderApiException>().having(
          (failure) => failure.code,
          'code',
          'ai_declined_locally',
        ),
      ),
    );
    expect(networkCalls, 0);
    expect(await restartedEvidence.hasPersistedLocalDecline(), isTrue);
    companion.dispose();
    restarted.dispose();
    auth.dispose();
  });
}
