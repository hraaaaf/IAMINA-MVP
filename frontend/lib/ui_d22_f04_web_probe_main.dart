// CI-only D22 F04 browser fixture. Real EditLogScreen + Drift Web patient vault.
// No credentials, real patient data, hosted API, target authority or deployment.
import 'package:amina/data/drift/database.dart';
import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:amina/features/journal/edit_log_screen.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:drift/drift.dart' as drift;
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

const _rawGlucose = 103.25;
const _syntheticUuid = 'd22f04e1-e77d-4a41-a6b8-673e03fa2604';

class _F04Receipt extends StatelessWidget {
  final AppDatabase db;
  final int logId;
  const _F04Receipt(this.db, this.logId);

  @override
  Widget build(BuildContext context) => Scaffold(
    body: Center(
      child: FutureBuilder<LogEntryData?>(
        future: db.getLogById(logId),
        builder: (context, snapshot) {
          if (snapshot.hasError) {
            return const Text('F04_WEB_FAIL_READ');
          }
          if (!snapshot.hasData) {
            return const Text('F04_WEB_CHECKING');
          }
          final row = snapshot.data!;
          final safe = row.bloodSugar == _rawGlucose &&
              row.isStressed &&
              row.syncStatus == 'pending';
          return Text(
            safe
                ? 'F04_WEB_PASS RAW=${row.bloodSugar} STRESS=TRUE'
                : 'F04_WEB_FAIL RAW=${row.bloodSugar} STRESS=${row.isStressed}',
            key: const Key('d22-f04-web-receipt'),
          );
        },
      ),
    ),
  );
}

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final db = AppDatabase.forPatientVault(
    PatientVaultScope.deviceLocal(_syntheticUuid),
  );
  await db.customSelect('SELECT 1').getSingle();
  if ((await db.select(db.logEntries).get()).isNotEmpty ||
      (await db.select(db.patientProfiles).get()).isNotEmpty) {
    throw StateError('F04 synthetic browser vault not empty');
  }
  await db.into(db.patientProfiles).insert(
    PatientProfilesCompanion.insert(
      userId: drift.Value(db.activeProfileRowId),
      updatedAt: DateTime.utc(2026, 11, 3),
      unitPreference: const drift.Value('mmol/L'),
    ),
  );
  final profile = (await db.getProfileForLocalUserId(
    db.activeProfileRowId,
  ))!;
  final logId = await db.into(db.logEntries).insert(
    LogEntriesCompanion.insert(
      createdAt: DateTime.utc(2026, 11, 3, 10),
      bloodSugar: _rawGlucose,
      clientUuid: 'd22-f04-web-synthetic-10325',
    ),
  );

  final router = GoRouter(
    initialLocation: '/edit',
    routes: [
      GoRoute(
        path: '/edit',
        builder: (context, state) => MultiProvider(
          providers: [
            Provider<AppDatabase>.value(value: db),
            Provider<PatientProfileData?>.value(value: profile),
          ],
          child: EditLogScreen(logId: logId),
        ),
      ),
      GoRoute(
        path: '/journal',
        builder: (context, state) => _F04Receipt(db, logId),
      ),
    ],
  );
  runApp(
    MaterialApp.router(
      debugShowCheckedModeBanner: false,
      locale: const Locale('fr'),
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: AppLocalizations.supportedLocales,
      routerConfig: router,
    ),
  );
}
