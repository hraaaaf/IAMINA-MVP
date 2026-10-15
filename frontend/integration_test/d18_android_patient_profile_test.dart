// D18 Android + iOS simulator integration; installed native app, synthetic test patients.
// Uses actual drift_flutter on-device, disk-backed patient vaults. All synthetic.
// The AppLock here is deliberately simulated; it proves UI gating, NOT platform
// biometric strength, physical device hardware or encryption.
import 'dart:convert';

import 'package:amina/core/theme/amina_visual_language.dart';
import 'package:amina/core/theme/app_theme.dart';
import 'package:amina/data/drift/database.dart';
import 'package:amina/data/drift/local_backup.dart';
import 'package:amina/data/drift/patient_progressive_demographics_store.dart';
import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:amina/data/drift/patient_weight_history_store.dart';
import 'package:amina/features/profile/profile_screen.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:amina/services/api_client.dart';
import 'package:amina/services/app_lock_service.dart';
import 'package:amina/services/app_lock_authenticator.dart';
import 'package:amina/services/app_lock_authenticator_factory.dart';
import 'package:amina/services/app_lock_authenticator_native.dart' show NativeAppLockAuthenticator;
import 'package:flutter/services.dart';
import 'package:amina/services/auth_service.dart';
import 'package:amina/services/consent_service.dart';
import 'package:amina/services/sync_service.dart';
import 'package:drift/drift.dart' as drift;
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:provider/provider.dart';

const idA = 994734;
const idB = 994812;
const weightA = '51ff0000-1111-4111-8111-000000000734';
const weightB = '51ff0000-1111-4111-8111-000000000812';

class _AppLockFixture extends AppLockService {
  bool unlocked = true;
  @override
  bool get isUnlocked => unlocked;
  void setUnlocked(bool v) {
    unlocked = v;
    notifyListeners();
  }
}

Future<AppDatabase> openPatient(int id) async {
  final db = AppDatabase.forPatientVault(PatientVaultScope.nativeDjango(id));
  await db.customSelect('SELECT 1').getSingle();
  return db;
}

Future<void> insertProfile(AppDatabase db, int id, String diabetes) async {
  await db.into(db.patientProfiles).insert(
    PatientProfilesCompanion.insert(
      userId: drift.Value(id),
      preferredLanguage: const drift.Value('fr'),
      diabetesType: drift.Value(diabetes),
      updatedAt: DateTime.now().toUtc(),
    ),
  );
}

Future<void> runNativeD18DiskIsolation() async {
  final now = DateTime.now().toUtc().subtract(const Duration(days: 2));
  final a = await openPatient(idA);
  try {
    expect(await PatientProgressiveDemographicsStore(a).read(), isNull);
    expect(await PatientWeightHistoryStore(a).recent(), isEmpty);
    await insertProfile(a, idA, 'type1');
    await PatientProgressiveDemographicsStore(a).update(
      updateBirthYear: true, birthYear: 1994,
      updateGenderIdentity: true, genderIdentity: 'non_binary',
    );
    await PatientWeightHistoryStore(a).append(
      clientUuid: weightA, value: '71.20', unit: 'kg',
      measuredAtUtc: now,
    );
    await PatientWeightHistoryStore(a).append(
      clientUuid: '51ff0000-2222-4222-8222-000000000734',
      value: '155.00', unit: 'lb',
      measuredAtUtc: now.add(const Duration(hours: 1)),
    );
    final backupA = jsonDecode(await LocalBackup.exportVaultJson(a))
        as Map<String, dynamic>;
    expect(backupA['weightObservations'], hasLength(2));
    expect(backupA['demographicDeclarations'], hasLength(1));
  } finally {
    await a.close();
  }

  final b = await openPatient(idB);
  try {
    // Separate physical sandbox files, no implicit A data migration.
    expect(await b.getProfileForLocalUserId(idB), isNull);
    expect(await PatientWeightHistoryStore(b).recent(), isEmpty);
    expect(await PatientProgressiveDemographicsStore(b).read(), isNull);
    await insertProfile(b, idB, 'type2');
    await PatientProgressiveDemographicsStore(b).update(
      updateBirthYear: true, birthYear: 2001,
      updateGenderIdentity: true, genderIdentity: 'prefer_not_to_say',
    );
    await PatientWeightHistoryStore(b).append(
      clientUuid: weightB, value: '62.00', unit: 'kg',
      measuredAtUtc: now,
    );
    // A backup cannot restore into B's actual Android-local vault.
    final aAgain = await openPatient(idA);
    try {
      final aBackup = await LocalBackup.exportVaultJson(aAgain);
      await expectLater(LocalBackup.restoreVaultJson(b, aBackup),
          throwsFormatException);
      expect((await PatientWeightHistoryStore(b).recent()).single.clientUuid,
          weightB);
    } finally {
      await aAgain.close();
    }
  } finally {
    await b.close();
  }

  final aFinal = await openPatient(idA);
  try {
    final details = await PatientProgressiveDemographicsStore(aFinal).read();
    final rows = await PatientWeightHistoryStore(aFinal).recent();
    expect(details?.birthYear, 1994);
    expect(details?.genderIdentity, 'non_binary');
    expect(details?.provenance, 'patient_declared');
    expect(rows, hasLength(2));
    expect(rows.first.unit, 'lb');
    expect(rows.last.unit, 'kg');
    expect(rows.last.clientUuid, weightA);
    expect((await aFinal.getProfileForLocalUserId(idA))?.diabetesType, 'type1');
    // The local Drift PatientProfile does not have a weight snapshot column.
    // D18 readings must live only in their explicitly dated history store.
    expect(await aFinal.getProfileForLocalUserId(idB), isNull);
    await PatientProgressiveDemographicsStore(aFinal).update(
      updateBirthYear: true, birthYear: null,
      updateGenderIdentity: true, genderIdentity: null,
    );
    final cleared = await PatientProgressiveDemographicsStore(aFinal).read();
    expect(cleared?.birthYear, isNull);
    expect(cleared?.genderIdentity, isNull);
    expect((await PatientWeightHistoryStore(aFinal).recent()), hasLength(2));
    expect((await aFinal.getProfileForLocalUserId(idA))?.diabetesType, 'type1');
  } finally {
    await aFinal.close();
  }
}

Future<void> checkNativeD18AccessReleaseGate() async {
  // No biometric is enrolled on this disposable CI emulator. Verify the
  // channel ITSELF exists, not merely Dart's fail-closed MissingPlugin fallback.
  final wire = await const MethodChannel(
    NativeAppLockAuthenticator.channelName).invokeMapMethod<String, dynamic>(
      'capability');
  expect(wire, isNotNull);
  expect(wire!['capability'], 'unavailable');
  final authenticator = createPlatformAppLockAuthenticator();
  expect(await authenticator.capability(), AppLockCapability.unavailable);
  await expectLater(authenticator.enroll(),
      throwsA(isA<AppLockException>().having(
        (e) => e.code, 'code', 'strong_auth_unavailable')));
  debugPrint('D18_NATIVE_BRIDGE=CONNECTED '
      'STRONG_BIOMETRY=UNAVAILABLE_UNENROLLED_SIMULATOR');
}

Future<void> checkRealNativeProfileScreen(WidgetTester tester) async {
  final db = await openPatient(idA);
  final auth = AuthService();
  final api = ApiClient(authService: auth);
  final lock = _AppLockFixture();
  final consent = ConsentService();
  final sync = SyncService(db, api);
  final profile = await db.getProfileForLocalUserId(idA);
  consent.seedInitialProfile(profile);
  consent.attachStream(db.watchProfile());
  addTearDown(() async {
    await db.close();
    auth.dispose();
    lock.dispose();
    consent.dispose();
  });
  await tester.pumpWidget(MultiProvider(
    providers: [
      Provider<AppDatabase>.value(value: db),
      ChangeNotifierProvider<AppLockService>.value(value: lock),
      ChangeNotifierProvider<AuthService>.value(value: auth),
      Provider<ApiClient>.value(value: api),
      Provider<SyncService>.value(value: sync),
      ChangeNotifierProvider<ConsentService>.value(value: consent),
      ChangeNotifierProvider<TweaksNotifier>(create: (_) => TweaksNotifier()),
      StreamProvider<PatientProfileData?>(
        create: (_) => db.watchProfile(), initialData: profile),
    ],
    child: MaterialApp(
      debugShowCheckedModeBanner: false,
      theme: AminaVisualLanguage.harmonize(AminaTheme.light),
      locale: const Locale('fr'),
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: AppLocalizations.supportedLocales,
      home: const ProfileScreen(),
    ),
  ));
  await tester.pumpAndSettle();
  expect(find.byType(ProfileScreen), findsOneWidget);
  expect(find.byKey(const Key('d18-profile-section')), findsOneWidget);
  lock.setUnlocked(false);
  await tester.pumpAndSettle();
  expect(find.byKey(const Key('d18-profile-section')), findsNothing);
  lock.setUnlocked(true);
  await tester.pumpAndSettle();
  expect(find.byKey(const Key('d18-profile-section')), findsOneWidget);
  await tester.pumpWidget(const SizedBox.shrink());
}

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();
  testWidgets('D18 native disk A B A and actual ProfileScreen gate',
      (tester) async {
    await runNativeD18DiskIsolation();
    await checkNativeD18AccessReleaseGate();
    await checkRealNativeProfileScreen(tester);
    expect(tester.takeException(), isNull);
  });
}
