// D22 F05 isolated actual ReportsScreen Web fixture.
// One synthetic local patient vault, legacy unverified 70/180 bounds.
// No actual patient, remote API, consent inference, CGM or exports.
import 'package:amina/data/drift/database.dart';
import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:amina/features/journal/reports_screen.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:drift/drift.dart' as drift;
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final language = Uri.base.queryParameters['lang'] == 'ar' ? 'ar' : 'fr';
  final db = AppDatabase.forPatientVault(PatientVaultScope.deviceLocal(
    'd22f0500-1a2b-4c3d-8e9f-010203040506',
  ));
  await db.customSelect('SELECT 1').getSingle();
  if ((await db.select(db.logEntries).get()).isNotEmpty ||
      (await db.select(db.patientProfiles).get()).isNotEmpty) {
    throw StateError('F05 isolated synthetic vault unexpectedly non-empty');
  }
  await db.into(db.patientProfiles).insert(
    PatientProfilesCompanion.insert(
      userId: drift.Value(db.activeProfileRowId),
      updatedAt: DateTime.utc(2026, 11, 3),
      unitPreference: const drift.Value('mmol/L'),
      // Deliberately legacy/unapproved. These values have NO clinical authority.
      targetRangeLow: const drift.Value(70),
      targetRangeHigh: const drift.Value(180),
    ),
  );
  await db.into(db.logEntries).insert(LogEntriesCompanion.insert(
    createdAt: DateTime.now().subtract(const Duration(minutes: 45)),
    bloodSugar: 103.25,
    // ReportsScreen uses loggedAt for the period query.
    loggedAt: drift.Value(DateTime.now().subtract(const Duration(minutes: 45))),
    clientUuid: 'd22-f05-reports-browser-synthetic',
  ));
  runApp(
    Provider<AppDatabase>.value(
      value: db,
      child: MaterialApp(
        debugShowCheckedModeBanner: false,
        locale: Locale(language),
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        supportedLocales: AppLocalizations.supportedLocales,
        home: const ReportsScreen(),
      ),
    ),
  );
}
