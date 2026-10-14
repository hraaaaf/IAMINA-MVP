// Two ACTUAL Android emulator instances on one Ubuntu runner. Test-only data.
// No real authentication, no remote clinical sync, no physical-device claims.
import 'dart:convert';
import 'dart:io';

import 'package:amina/data/drift/database.dart';
import 'package:amina/data/drift/patient_treatment_declaration_store.dart';
import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:amina/routes/app_router.dart';
import 'package:amina/services/consent_service.dart';
import 'package:drift/drift.dart' as drift;
import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:path_provider/path_provider.dart';

const role = String.fromEnvironment('IAMINA_VIRTUAL_DEVICE_ROLE');
bool firstUse(ConsentService c) => shouldApplyOnboardingGate(
  isLoggedIn: true, isAnonymous: false, requiresHostedRemoteLogin: false,
  hasCompletedOnboarding: c.hasCompletedOnboarding,
  hasProfileState: c.isInitialized,
);

Future<Map<String, dynamic>> hub(String method, String path,
    [Map<String, String>? body]) async {
  final client = HttpClient()..connectionTimeout = const Duration(seconds: 5);
  try {
    final request = await client.openUrl(
      method, Uri.parse('http://127.0.0.1:8765' + path),
    );
    if (body != null) {
      request.headers.contentType = ContentType.json;
      request.write(jsonEncode(body));
    }
    final response = await request.close();
    expect(response.statusCode, 200);
    return jsonDecode(await utf8.decoder.bind(response).join())
        as Map<String, dynamic>;
  } finally {
    client.close(force: true);
  }
}
Future<AppDatabase> openVault(File file, int id) async {
  final db = AppDatabase.testPatientVault(
    NativeDatabase(file), PatientVaultScope.nativeDjango(id),
  );
  await db.customSelect('SELECT 1').getSingle();
  return db;
}
Future<void> saveProfile(AppDatabase db, int id, String type) async {
  await db.into(db.patientProfiles).insert(
    PatientProfilesCompanion.insert(
      userId: drift.Value(id),
      updatedAt: DateTime.utc(2026, 10, 14),
      diabetesType: drift.Value(type),
    ),
  );
}
Future<void> onDeviceOne() async {
  final base = (await getApplicationSupportDirectory()).path;
  final fileA = File(base + '/ci_native_734.sqlite');
  final fileB = File(base + '/ci_native_812.sqlite');
  for (final file in [fileA, fileB]) {
    if (await file.exists()) await file.delete();
  }
  final dbA = await openVault(fileA, 734);
  try {
    final before = ConsentService()
      ..seedInitialProfile(await dbA.getProfileForLocalUserId(734));
    expect(firstUse(before), isTrue);
    expect(before.hasConsent, isFalse);
    before.dispose();
    await saveProfile(dbA, 734, 'type1');
    await PatientTreatmentDeclarationStore(dbA).write(
      state: 'declared', codes: ['lifestyle', 'oral_meds'],
    );
    final after = ConsentService()
      ..seedInitialProfile(await dbA.getProfileForLocalUserId(734));
    expect(firstUse(after), isFalse);
    expect(after.hasConsent, isFalse);
    after.dispose();
  } finally {
    await dbA.close();
  }
  // Cold SQLite close/reopen, NOT a physical power cycle.
  final coldA = await openVault(fileA, 734);
  try {
    expect((await coldA.getProfileForLocalUserId(734))?.diabetesType, 'type1');
  } finally {
    await coldA.close();
  }
  final dbB = await openVault(fileB, 812);
  try {
    expect(await dbB.getProfileForLocalUserId(812), isNull);
    expect(await dbB.select(dbB.patientProfiles).get(), isEmpty);
    expect(await PatientTreatmentDeclarationStore(dbB).read(), isNull);
    final c = ConsentService()
      ..seedInitialProfile(await dbB.getProfileForLocalUserId(812));
    expect(firstUse(c), isTrue);
    expect(c.hasConsent, isFalse);
    c.dispose();
    await saveProfile(dbB, 812, 'type2');
    await PatientTreatmentDeclarationStore(dbB).write(
      state: 'declared', codes: ['insulin'],
    );
  } finally {
    await dbB.close();
  }
  final againA = await openVault(fileA, 734);
  try {
    expect(await againA.getProfileForLocalUserId(812), isNull);
    final rows = await againA.select(againA.patientProfiles).get();
    expect(rows, hasLength(1));
    expect(rows.single.userId, 734);
    final treatment = await PatientTreatmentDeclarationStore(againA).read();
    expect(treatment?.codes, ['lifestyle', 'oral_meds']);
    expect(treatment?.syncStatus, 'pending');
    expect(treatment?.codes, isNot(contains('insulin')));
  } finally {
    await againA.close();
  }
}
Future<void> onDeviceTwo() async {
  // Same synthetic account 734; separate emulator Android data sandbox.
  final base = (await getApplicationSupportDirectory()).path;
  final file = File(base + '/ci_native_734.sqlite');
  if (await file.exists()) await file.delete();
  final db = await openVault(file, 734);
  try {
    expect(await db.getProfileForLocalUserId(734), isNull);
    expect(await db.select(db.patientProfiles).get(), isEmpty);
    expect(await PatientTreatmentDeclarationStore(db).read(), isNull);
    final consent = ConsentService()
      ..seedInitialProfile(await db.getProfileForLocalUserId(734));
    expect(firstUse(consent), isTrue);
    expect(consent.hasConsent, isFalse);
    consent.dispose();
  } finally {
    await db.close();
  }
}
void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();
  testWidgets('D7 #7 + D9 #9 two independently sandboxed Android emulators',
      (tester) async {
    expect(role, anyOf('device-one', 'device-two'));
    expect((await hub('GET', '/health'))['hub'],
        'iamina-d7-d9-ubuntu-synthetic');
    if (role == 'device-one') {
      await onDeviceOne();
    } else {
      await onDeviceTwo();
    }
    expect((await hub('POST', '/attest', {
      'role': role,
      'result': 'pass',
      'scenario': role == 'device-one'
          ? 'same-install-a-b-a-cold-restart'
          : 'fresh-install-no-remote-restore',
    }))['accepted'], isTrue);
  });
}
