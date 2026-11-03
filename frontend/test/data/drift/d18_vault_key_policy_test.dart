import 'dart:convert';

import 'package:amina/data/drift/d18_keyed_open_guard.dart';
import 'package:amina/data/drift/d18_pre_cutover_cipher_adapter.dart';
import 'package:drift/native.dart';
import 'package:amina/data/drift/d18_vault_key_policy.dart';
import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:flutter_test/flutter_test.dart';

const _first = 'd18-passphrase-2026-synthetic-strong-ONE';
const _next = 'd18-passphrase-2026-synthetic-strong-TWO';
final _a = PatientVaultScope.deviceLocal('7e0bb410-2c7f-4d3e-9b61-36f092c76210');
final _b = PatientVaultScope.deviceLocal('7e0bb410-2c7f-4d3e-9b61-36f092c76211');

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('A: passphrase unlock binds the key to exactly one patient scope', () async {
    final created = await D18VaultKeyPolicy.createForEmptyVault(
      scope: _a, passphrase: _first,
    );
    addTearDown(created.session.lock);
    final dataKey = await created.session.requireUnlockedKey().extractBytes();
    expect(dataKey.length, 32);
    expect(created.publicEnvelopeJson, isNot(contains(_first)));
    expect(created.publicEnvelopeJson, isNot(contains(created.offlineRecoveryCode)));
    expect(created.publicEnvelopeJson, isNot(contains(_a.databaseName)));
    final envelope = jsonDecode(created.publicEnvelopeJson) as Map<String,dynamic>;
    expect(envelope['iterations'], 600000);
    expect(envelope['cipher'], 'aes-256-gcm');

    final reopened = await D18VaultKeyPolicy.unlockWithPassphrase(
      scope: _a, publicEnvelopeJson: created.publicEnvelopeJson,
      passphrase: _first,
    );
    expect(await reopened.requireUnlockedKey().extractBytes(), dataKey);
    reopened.lock();
    expect(reopened.isLocked, isTrue);
    expect(() => reopened.requireUnlockedKey(), throwsStateError);

    await expectLater(
      D18VaultKeyPolicy.unlockWithPassphrase(
        scope: _a, publicEnvelopeJson: created.publicEnvelopeJson,
        passphrase: _next,
      ), throwsA(isA<Exception>()),
    );
    await expectLater(
      D18VaultKeyPolicy.unlockWithPassphrase(
        scope: _b, publicEnvelopeJson: created.publicEnvelopeJson,
        passphrase: _first,
      ), throwsA(isA<Exception>()),
    );
    expect(created.session.isLocked, isFalse);
  });

  test('offline code independently restores data key and resets passphrase',
      () async {
    final created = await D18VaultKeyPolicy.createForEmptyVault(
      scope: _a, passphrase: _first,
    );
    addTearDown(created.session.lock);
    final dataKey = await created.session.requireUnlockedKey().extractBytes();
    final recovered = await D18VaultKeyPolicy.unlockWithOfflineRecovery(
      scope: _a,
      publicEnvelopeJson: created.publicEnvelopeJson,
      offlineRecoveryCode: created.offlineRecoveryCode,
    );
    expect(await recovered.requireUnlockedKey().extractBytes(), dataKey);
    recovered.lock();

    final replacement = await D18VaultKeyPolicy.resetAfterRecovery(
      scope: _a,
      publicEnvelopeJson: created.publicEnvelopeJson,
      offlineRecoveryCode: created.offlineRecoveryCode,
      newPassphrase: _next,
    );
    addTearDown(replacement.session.lock);
    expect(replacement.offlineRecoveryCode, isNot(created.offlineRecoveryCode));
    expect(await replacement.session.requireUnlockedKey().extractBytes(), dataKey);
    final unlocked = await D18VaultKeyPolicy.unlockWithPassphrase(
      scope: _a,
      publicEnvelopeJson: replacement.publicEnvelopeJson,
      passphrase: _next,
    );
    expect(await unlocked.requireUnlockedKey().extractBytes(), dataKey);
    unlocked.lock();

    await expectLater(
      D18VaultKeyPolicy.unlockWithPassphrase(
        scope: _a, publicEnvelopeJson: replacement.publicEnvelopeJson,
        passphrase: _first,
      ), throwsA(isA<Exception>()),
    );
    await expectLater(
      D18VaultKeyPolicy.unlockWithOfflineRecovery(
        scope: _a, publicEnvelopeJson: replacement.publicEnvelopeJson,
        offlineRecoveryCode: created.offlineRecoveryCode,
      ), throwsA(isA<Exception>()),
    );
    final newRecovery = await D18VaultKeyPolicy.unlockWithOfflineRecovery(
      scope: _a, publicEnvelopeJson: replacement.publicEnvelopeJson,
      offlineRecoveryCode: replacement.offlineRecoveryCode,
    );
    expect(await newRecovery.requireUnlockedKey().extractBytes(), dataKey);
    newRecovery.lock();
  });

  test('rejects forged, malformed, cross-vault, audit and unscoped input',
      () async {
    final created = await D18VaultKeyPolicy.createForEmptyVault(
      scope: _a, passphrase: _first,
    );
    addTearDown(created.session.lock);

    final corrupted = jsonDecode(created.publicEnvelopeJson)
        as Map<String, dynamic>;
    final cipher = corrupted['recoveryWrappedKey'] as String;
    final offset = cipher.length ~/ 2;
    corrupted['recoveryWrappedKey'] =
      '${cipher.substring(0,offset)}${cipher[offset]=='A'?'B':'A'}${cipher.substring(offset+1)}';
    await expectLater(
      D18VaultKeyPolicy.unlockWithOfflineRecovery(
        scope: _a, publicEnvelopeJson: jsonEncode(corrupted),
        offlineRecoveryCode: created.offlineRecoveryCode,
      ), throwsA(isA<Exception>()),
    );

    final forged = jsonDecode(created.publicEnvelopeJson)
        as Map<String, dynamic>;
    forged['iterations'] = 2000000000;
    await expectLater(
      D18VaultKeyPolicy.unlockWithPassphrase(
        scope: _a, publicEnvelopeJson: jsonEncode(forged),
        passphrase: _first,
      ), throwsFormatException,
    );
    final extra = jsonDecode(created.publicEnvelopeJson)
        as Map<String, dynamic>;
    extra['plaintextKey'] = 'MUST_NOT_BE_ALLOWED';
    await expectLater(
      D18VaultKeyPolicy.unlockWithPassphrase(
        scope: _a, publicEnvelopeJson: jsonEncode(extra),
        passphrase: _first,
      ), throwsFormatException,
    );
    await expectLater(
      D18VaultKeyPolicy.unlockWithOfflineRecovery(
        scope: _b, publicEnvelopeJson: created.publicEnvelopeJson,
        offlineRecoveryCode: created.offlineRecoveryCode,
      ), throwsA(isA<Exception>()),
    );
    await expectLater(
      D18VaultKeyPolicy.createForEmptyVault(
        scope: PatientVaultScope.auditOnly(), passphrase: _first,
      ), throwsStateError,
    );
    await expectLater(
      D18VaultKeyPolicy.createForEmptyVault(scope: _a, passphrase: 'short'),
      throwsArgumentError,
    );
    expect(() => created.session.lock(), returnsNormally);
  });

  test('pre-cutover keyed opener rejects A/B, stale auth and erases key copy',
      () async {
    final created = await D18VaultKeyPolicy.createForEmptyVault(
      scope: _a, passphrase: _first,
    );
    addTearDown(created.session.lock);
    var epoch = 9;
    PatientVaultScope? verified = _a;
    var opens = 0;
    var discards = 0;
    List<int>? keyCopy;
    final guard = D18KeyedOpenGuard(
      resolveAuthenticatedScope: () async => verified,
      readAuthEpoch: () => epoch,
    );
    Future<String> open(List<int> bytes) async {
      opens++;
      keyCopy = bytes;
      expect(bytes.length, 32);
      return 'synthetic-not-published-executor';
    }
    Future<void> discard(String _) async {discards++;}

    await expectLater(guard.openUnpublished<String>(
      requestedScope: _b, keySession: created.session,
      createUnpublished: open, discardUnpublished: discard,
    ), throwsStateError);
    expect(opens, 0);

    final good = await guard.openUnpublished<String>(
      requestedScope: _a, keySession: created.session,
      createUnpublished: open, discardUnpublished: discard,
    );
    expect(good, 'synthetic-not-published-executor');
    expect(keyCopy, everyElement(0));
    expect(discards, 0);

    await expectLater(guard.openUnpublished<String>(
      requestedScope: _a, keySession: created.session,
      createUnpublished: (bytes) async {
        opens++;
        keyCopy = bytes;
        epoch++; // Log out during an asynchronous keyed SQLite open.
        return 'stale-candidate';
      },
      discardUnpublished: discard,
    ), throwsStateError);
    expect(discards, 1); // Stale candidate must be closed, never published.
    expect(keyCopy, everyElement(0));

    verified = _b; // Auth source switched without an epoch change.
    await expectLater(guard.openUnpublished<String>(
      requestedScope: _a, keySession: created.session,
      createUnpublished: open, discardUnpublished: discard,
    ), throwsStateError);
    expect(opens, 2);

    verified = _a;
    created.session.lock();
    expect(() => created.session.requireUnlockedKeyForScope(_a),
        throwsStateError);
    await expectLater(guard.openUnpublished<String>(
      requestedScope: _a, keySession: created.session,
      createUnpublished: open, discardUnpublished: discard,
    ), throwsStateError);
    expect(opens, 2);
  });


  test('pre-cutover adapter never publishes a plaintext or wrong-scope worker',
      () async {
    final enrollment=await D18VaultKeyPolicy.createForEmptyVault(
      scope:_a, passphrase:_first);
    addTearDown(enrollment.session.lock);
    var epoch=3, opens=0, disposed=0;
    var authenticated=_a;
    var badEngine=false, badDestination=false, staleDuringOpen=false;
    var badSchema=false;
    var physicalState=D18CipherPhysicalState.absent;
    final guard=D18KeyedOpenGuard(
      resolveAuthenticatedScope:() async=>authenticated,
      readAuthEpoch:()=>epoch);
    final adapter=D18PreCutoverCipherAdapter(
      guard:guard,
      openVerifiedWorker:(scope,intent,destination,keyBytes) async {
        opens++;
        expect(keyBytes.length,32);
        expect(destination,D18PreCutoverCipherAdapter.destinationFor(scope));
        expect(intent,anyOf(
          D18CipherVaultOpenIntent.createFresh,
          D18CipherVaultOpenIntent.reopenExisting));
        final executor=NativeDatabase.memory(setup:(raw) {
          // Simulate a corrupted/misleading v12 file: the header claims
          // version 12 but none of the required clinical tables exist.
          if(badSchema) raw.execute('PRAGMA user_version=12');
        });
        if(staleDuringOpen) epoch++;
        return D18KeyedCipherWorkerLease(
          executor:executor,
          authenticatedScopeName:scope.databaseName,
          physicalDatabaseName:badDestination
              ? scope.databaseName
              : D18PreCutoverCipherAdapter.destinationFor(scope),
          cipherEngine:badEngine ? 'sqlite3-stock' : 'sqlite3mc',
          physicalState:physicalState,
          disposeWorker:() async {
            disposed++;
            // The worker-side lease owns cleanup on rejection even before
            // AppDatabase takes ownership of the query executor.
            await executor.close();
          },
        );
      });
    await expectLater(adapter.openUnpublished(
      scope:_b,keySession:enrollment.session,
      intent:D18CipherVaultOpenIntent.createFresh),throwsStateError);
    expect(opens,0);

    badEngine=true;
    await expectLater(adapter.openUnpublished(
      scope:_a,keySession:enrollment.session,
      intent:D18CipherVaultOpenIntent.createFresh),throwsStateError);
    expect(disposed,1);
    badEngine=false;

    badDestination=true;
    await expectLater(adapter.openUnpublished(
      scope:_a,keySession:enrollment.session,
      intent:D18CipherVaultOpenIntent.createFresh),throwsStateError);
    expect(disposed,2);
    badDestination=false;

    // Existing ciphertext must never be overwritten by enrollment.
    physicalState=D18CipherPhysicalState.existingAuthenticated;
    await expectLater(adapter.openUnpublished(
      scope:_a,keySession:enrollment.session,
      intent:D18CipherVaultOpenIntent.createFresh),throwsStateError);
    expect(disposed,3);
    // Missing ciphertext must never be silently replaced during reopen.
    physicalState=D18CipherPhysicalState.absent;
    await expectLater(adapter.openUnpublished(
      scope:_a,keySession:enrollment.session,
      intent:D18CipherVaultOpenIntent.reopenExisting),throwsStateError);
    expect(disposed,4);

    badSchema=true;
    await expectLater(adapter.openUnpublished(
      scope:_a,keySession:enrollment.session,
      intent:D18CipherVaultOpenIntent.createFresh),throwsStateError);
    expect(disposed,5);
    badSchema=false;

    staleDuringOpen=true;
    await expectLater(adapter.openUnpublished(
      scope:_a,keySession:enrollment.session,
      intent:D18CipherVaultOpenIntent.createFresh),throwsStateError);
    expect(disposed,6);
    staleDuringOpen=false;
    // A still controls the simulated authenticated account after the epoch
    // update, so a fresh approved opening must be independently verified.
    final candidate=await adapter.openUnpublished(
      scope:_a,keySession:enrollment.session,
      intent:D18CipherVaultOpenIntent.createFresh);
    final version=await candidate.database.customSelect(
        'PRAGMA user_version').getSingle();
    expect(version.read<int>('user_version'),12);
    // Both callers must await the same close AND worker lock release.
    await Future.wait([candidate.close(), candidate.close()]);
    await candidate.close();
    expect(disposed,7); // Concurrent idempotent close, no orphan worker.
    authenticated=_b;
    await expectLater(adapter.openUnpublished(
      scope:_a,keySession:enrollment.session,
      intent:D18CipherVaultOpenIntent.createFresh),throwsStateError);
    expect(opens,7);
  });

}
