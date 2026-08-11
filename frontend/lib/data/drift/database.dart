import 'dart:math' as math;
import 'package:drift/drift.dart';
import 'package:drift_flutter/drift_flutter.dart';
import 'package:uuid/uuid.dart';

part 'database.g.dart';

// ============================================================================
// Database Tables
// ============================================================================

@DataClassName('LogEntryData')
class LogEntries extends Table {
  IntColumn get id => integer().autoIncrement()();
  DateTimeColumn get createdAt => dateTime()();
  RealColumn get bloodSugar => real()();
  RealColumn get insulinUnits => real().nullable()();
  TextColumn get glycemicContext => text().nullable()();
  TextColumn get mealType => text().nullable()();
  TextColumn get mealDescription => text().nullable()();
  TextColumn get mealItemsJson => text().nullable()();
  TextColumn get mealPortionsJson => text().nullable()();
  TextColumn get source => text().withDefault(const Constant('manual'))();
  TextColumn get syncStatus => text().withDefault(const Constant('pending'))();
  TextColumn get clientUuid => text().unique()();
  DateTimeColumn get loggedAt => dateTime().nullable()();
  IntColumn get fatigueLevel => integer().nullable()();
  BoolColumn get isSick => boolean().withDefault(const Constant(false))();
  BoolColumn get isStressed => boolean().withDefault(const Constant(false))();
  BoolColumn get isTired => boolean().withDefault(const Constant(false))();
  BoolColumn get isActive => boolean().withDefault(const Constant(false))();
  BoolColumn get ramadanMode => boolean().withDefault(const Constant(false))();
  TextColumn get sleepQuality => text().nullable()();
  IntColumn get syncAttempts => integer().withDefault(const Constant(0))();
  BoolColumn get errorSync => boolean().withDefault(const Constant(false))();
}

@DataClassName('MedicationEventData')
class MedicationEvents extends Table {
  IntColumn get id => integer().autoIncrement()();
  TextColumn get label => text()();
  RealColumn get dose => real().nullable()();
  TextColumn get unit => text().nullable()();
  DateTimeColumn get takenAt => dateTime()();
  DateTimeColumn get createdAt => dateTime()();
}

@DataClassName('ReminderData')
class Reminders extends Table {
  IntColumn get id => integer().autoIncrement()();
  TextColumn get title => text()();
  DateTimeColumn get dueAt => dateTime()();
  BoolColumn get enabled => boolean().withDefault(const Constant(true))();
  DateTimeColumn get createdAt => dateTime()();
}

@DataClassName('PatientProfileData')
class PatientProfiles extends Table {
  IntColumn get userId => integer()();
  @override
  Set<Column> get primaryKey => {userId};
  TextColumn get preferredLanguage =>
      text().withDefault(const Constant('fr'))();
  DateTimeColumn get updatedAt => dateTime()();
  TextColumn get diabetesType => text().nullable()();
  RealColumn get targetRangeLow => real().withDefault(const Constant(70.0))();
  RealColumn get targetRangeHigh => real().withDefault(const Constant(180.0))();
  TextColumn get unitPreference =>
      text().withDefault(const Constant('mg/dL'))();

  /// Treatment modality: 'insulin' | 'tablets' | 'lifestyle'
  TextColumn get treatment => text().nullable()();

  DateTimeColumn get ramadanStartDate => dateTime().nullable()();
  DateTimeColumn get ramadanEndDate => dateTime().nullable()();

  /// RGPD Art. 7 — explicit AI processing consent timestamp.
  /// null = no consent given or withdrawn.
  DateTimeColumn get aiConsentGivenAt => dateTime().nullable()();
}

@DataClassName('ChatMessageData')
class ChatMessages extends Table {
  IntColumn get id => integer().autoIncrement()();
  TextColumn get conversationId => text()();
  TextColumn get role => text()();
  TextColumn get message => text()();
  DateTimeColumn get createdAt => dateTime()();
}

// ============================================================================
// Database
// ============================================================================

@DriftDatabase(
  tables: [
    LogEntries,
    PatientProfiles,
    ChatMessages,
    MedicationEvents,
    Reminders,
  ],
)
class AppDatabase extends _$AppDatabase {
  // Constructor for custom openers (useful for tests)
  AppDatabase(super.e);

  // Default constructor using drift_flutter's recommended setup
  AppDatabase.defaults()
    : super(
        driftDatabase(
          name: 'amina',
          web: DriftWebOptions(
            sqlite3Wasm: Uri.parse('sqlite3.wasm'),
            driftWorker: Uri.parse('drift_worker.js'),
          ),
        ),
      );

  @override
  int get schemaVersion => 10;

  @override
  MigrationStrategy get migration => MigrationStrategy(
    onCreate: (Migrator m) async {
      await m.createAll();
    },
    onUpgrade: (Migrator m, int from, int to) async {
      if (from < 2) {
        await m.addColumn(logEntries, logEntries.loggedAt);
        await m.addColumn(logEntries, logEntries.fatigueLevel);
        await m.addColumn(logEntries, logEntries.isSick);
        await m.addColumn(logEntries, logEntries.isStressed);
        await m.addColumn(logEntries, logEntries.isTired);
        await m.addColumn(logEntries, logEntries.isActive);
        await m.addColumn(logEntries, logEntries.sleepQuality);
        await m.addColumn(logEntries, logEntries.syncAttempts);
        await m.addColumn(logEntries, logEntries.errorSync);
      }
      if (from < 3) {
        await m.addColumn(logEntries, logEntries.ramadanMode);
      }
      if (from < 4) {
        await m.addColumn(patientProfiles, patientProfiles.treatment);
      }
      if (from < 5) {
        await m.addColumn(patientProfiles, patientProfiles.aiConsentGivenAt);
      }
      if (from < 6) {
        await m.addColumn(logEntries, logEntries.glycemicContext);
      }
      if (from < 7) {
        await m.addColumn(logEntries, logEntries.mealItemsJson);
      }
      if (from < 8) {
        await m.addColumn(logEntries, logEntries.mealPortionsJson);
      }
      if (from < 9) {
        await m.addColumn(patientProfiles, patientProfiles.ramadanStartDate);
        await m.addColumn(patientProfiles, patientProfiles.ramadanEndDate);
      }
      if (from < 10) {
        await m.createTable(medicationEvents);
        await m.createTable(reminders);
      }
    },
  );

  Future<bool> setRamadanPeriod({DateTime? start, DateTime? end}) async {
    if ((start == null) != (end == null)) {
      throw ArgumentError('Ramadan period requires both dates or neither');
    }
    if (start != null && end != null && start.isAfter(end)) {
      throw ArgumentError('Ramadan period start must not be after end');
    }
    final existing = await (select(
      patientProfiles,
    )..limit(1)).getSingleOrNull();
    if (existing == null) return false;

    final updated =
        await (update(
          patientProfiles,
        )..where((row) => row.userId.equals(existing.userId))).write(
          PatientProfilesCompanion(
            updatedAt: Value(DateTime.now()),
            ramadanStartDate: Value(start),
            ramadanEndDate: Value(end),
          ),
        );
    return updated == 1;
  }

  // Watchers
  Stream<List<LogEntryData>> watchRecentLogs({int limit = 20}) {
    return (select(logEntries)
          ..orderBy([
            (t) =>
                OrderingTerm(expression: t.loggedAt, mode: OrderingMode.desc),
          ])
          ..limit(limit))
        .watch();
  }

  Future<List<LogEntryData>> getRecentLogs({int limit = 100}) {
    return (select(logEntries)
          ..orderBy([
            (t) =>
                OrderingTerm(expression: t.loggedAt, mode: OrderingMode.desc),
          ])
          ..limit(limit))
        .get();
  }

  Stream<List<LogEntryData>> watchLogsInRange(DateTime start, DateTime end) {
    return (select(logEntries)
          ..where((t) => t.loggedAt.isBetweenValues(start, end))
          ..orderBy([
            (t) =>
                OrderingTerm(expression: t.loggedAt, mode: OrderingMode.desc),
          ]))
        .watch();
  }

  Stream<PatientProfileData?> watchProfile() {
    return (select(patientProfiles)..limit(1)).watchSingleOrNull();
  }

  // Queries
  Future<List<LogEntryData>> getPendingLogs() {
    return (select(logEntries)
          ..where((t) => t.syncStatus.equals('pending'))
          ..where((t) => t.errorSync.equals(false))
          ..where((t) => t.syncAttempts.isSmallerThanValue(3)))
        .get();
  }

  Future<void> markLogAsSynced(int id) {
    return (update(logEntries)..where((t) => t.id.equals(id))).write(
      const LogEntriesCompanion(
        syncStatus: Value('synced'),
        errorSync: Value(false),
      ),
    );
  }

  Future<void> reportSyncFailure(int id, int currentAttempts) {
    return (update(logEntries)..where((t) => t.id.equals(id))).write(
      LogEntriesCompanion(
        syncAttempts: Value(currentAttempts + 1),
        errorSync: Value(currentAttempts + 1 >= 3),
      ),
    );
  }

  Future<int> countLogs() {
    return logEntries.count().getSingle();
  }

  Future<LogEntryData?> getLogById(int id) {
    return (select(
      logEntries,
    )..where((t) => t.id.equals(id))).getSingleOrNull();
  }

  Future<void> updateLog(int id, LogEntriesCompanion data) {
    return (update(logEntries)..where((t) => t.id.equals(id))).write(data);
  }

  Future<void> deleteLog(int id) {
    return (delete(logEntries)..where((t) => t.id.equals(id))).go();
  }

  /// RGPD Art. 7 — record explicit AI consent in the local DB.
  /// [granted] true = consent given, false = consent withdrawn.
  Future<void> setAiConsent({required bool granted}) async {
    final ts = granted ? DateTime.now() : null;
    final existing = await (select(
      patientProfiles,
    )..limit(1)).getSingleOrNull();
    if (existing != null) {
      await (update(patientProfiles)
            ..where((t) => t.userId.equals(existing.userId)))
          .write(PatientProfilesCompanion(aiConsentGivenAt: Value(ts)));
    }
  }

  Stream<List<MedicationEventData>> watchMedicationEvents({int limit = 50}) {
    return (select(medicationEvents)
          ..orderBy([
            (t) => OrderingTerm(expression: t.takenAt, mode: OrderingMode.desc),
          ])
          ..limit(limit))
        .watch();
  }

  Future<int> addMedicationEvent({
    required String label,
    double? dose,
    String? unit,
    required DateTime takenAt,
  }) {
    final cleanedUnit = unit?.trim();
    return into(medicationEvents).insert(
      MedicationEventsCompanion.insert(
        label: label.trim(),
        dose: Value(dose),
        unit: Value(
          cleanedUnit == null || cleanedUnit.isEmpty ? null : cleanedUnit,
        ),
        takenAt: takenAt,
        createdAt: DateTime.now(),
      ),
    );
  }

  Future<void> deleteMedicationEvent(int id) {
    return (delete(medicationEvents)..where((t) => t.id.equals(id))).go();
  }

  Stream<List<ReminderData>> watchReminders() {
    return (select(reminders)..orderBy([
          (t) => OrderingTerm(expression: t.dueAt, mode: OrderingMode.asc),
        ]))
        .watch();
  }

  Future<int> addReminder({required String title, required DateTime dueAt}) {
    return into(reminders).insert(
      RemindersCompanion.insert(
        title: title.trim(),
        dueAt: dueAt,
        createdAt: DateTime.now(),
      ),
    );
  }

  Future<void> setReminderEnabled(int id, bool enabled) {
    return (update(reminders)..where((t) => t.id.equals(id))).write(
      RemindersCompanion(enabled: Value(enabled)),
    );
  }

  Future<void> deleteReminder(int id) {
    return (delete(reminders)..where((t) => t.id.equals(id))).go();
  }

  // Generates 21 days of realistic Type-2 diabetic patient demo data.
  // Always clears existing entries first so data never goes stale (MISTAKES #22).
  Future<void> seedDemoData() async {
    // Delete all existing log entries — demo data must be fresh (relative to now).
    await delete(logEntries).go();

    final rng = math.Random(42);
    const uuid = Uuid();
    final now = DateTime.now();

    final mealSlots = [
      // (hour, minute, glycemicContext, mealType, baseGlucose, insulinBase)
      (7, 15, 'fasting', null, 95.0, 0.0),
      (8, 30, 'pre_meal', 'breakfast', 100.0, 0.0),
      (9, 45, 'post_meal', 'breakfast', 145.0, 0.0),
      (13, 0, 'pre_meal', 'lunch', 110.0, 4.0),
      (14, 30, 'post_meal', 'lunch', 170.0, 0.0),
      (19, 0, 'pre_meal', 'dinner', 105.0, 6.0),
      (20, 30, 'post_meal', 'dinner', 160.0, 0.0),
      (23, 0, 'other', null, 115.0, 0.0),
    ];

    for (int day = 20; day >= 0; day--) {
      final date = now.subtract(Duration(days: day));

      // Use 3-5 slots per day
      final slotCount = 3 + rng.nextInt(3);
      final slots = (mealSlots.toList()..shuffle(rng)).take(slotCount).toList();

      for (final slot in slots) {
        final (hour, minute, glycemicContext, mealType, base, insulinBase) =
            slot;

        // Add realistic noise: ±25 mg/dL normal, occasional spikes
        double noise = (rng.nextDouble() - 0.5) * 50;
        // 10% chance of a notable event
        if (rng.nextDouble() < 0.10) noise += rng.nextBool() ? 60 : -40;

        final glucose = (base + noise).clamp(55.0, 300.0);
        final insulin = insulinBase > 0
            ? insulinBase + rng.nextInt(3).toDouble()
            : 0.0;

        final loggedAt = DateTime(
          date.year,
          date.month,
          date.day,
          hour,
          minute + rng.nextInt(15),
        );

        await into(logEntries).insert(
          LogEntriesCompanion.insert(
            createdAt: loggedAt,
            bloodSugar: glucose,
            insulinUnits: Value(insulin > 0 ? insulin : null),
            glycemicContext: Value(glycemicContext),
            mealType: Value(mealType),
            clientUuid: uuid.v4(),
            loggedAt: Value(loggedAt),
            syncStatus: const Value('synced'),
          ),
        );
      }
    }

    // Entrée "EN DIRECT" — il y a 2 min — active le Hero Live dans la démo
    final liveEntry = now.subtract(const Duration(minutes: 2));
    await into(logEntries).insert(
      LogEntriesCompanion.insert(
        createdAt: liveEntry,
        bloodSugar: 142.0,
        insulinUnits: const Value(null),
        glycemicContext: const Value('post_meal'),
        mealType: const Value('dinner'),
        clientUuid: uuid.v4(),
        loggedAt: Value(liveEntry),
        syncStatus: const Value('synced'),
      ),
    );

    // Ensure profile exists
    final existing = await (select(
      patientProfiles,
    )..limit(1)).getSingleOrNull();
    if (existing == null) {
      await into(patientProfiles).insert(
        PatientProfilesCompanion.insert(
          userId: const Value(1),
          updatedAt: now,
          diabetesType: const Value('type2'),
          targetRangeLow: const Value(70.0),
          targetRangeHigh: const Value(180.0),
          unitPreference: const Value('mg/dL'),
        ),
      );
    }
  }
}
