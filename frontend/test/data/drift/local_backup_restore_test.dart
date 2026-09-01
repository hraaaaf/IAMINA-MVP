import 'dart:convert';

import 'package:amina/data/drift/database.dart';
import 'package:amina/data/drift/local_backup.dart';
import 'package:drift/drift.dart';
import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  late AppDatabase db;

  setUp(() {
    db = AppDatabase(NativeDatabase.memory());
  });

  tearDown(() async {
    await db.close();
  });

  Future<void> seedSyntheticFixture() async {
    final loggedAt = DateTime.utc(2026, 8, 31, 12, 30);

    await db.into(db.patientProfiles).insert(
      PatientProfilesCompanion.insert(
        userId: const Value(7),
        preferredLanguage: const Value('fr'),
        updatedAt: loggedAt,
        diabetesType: const Value('type2'),
        targetRangeLow: const Value(82),
        targetRangeHigh: const Value(155),
        unitPreference: const Value('mg/dL'),
        treatment: const Value('tablets'),
        aiConsentGivenAt: Value(DateTime.utc(2026, 8, 1)),
      ),
    );

    await db.into(db.logEntries).insert(
      LogEntriesCompanion.insert(
        id: const Value(11),
        createdAt: loggedAt,
        bloodSugar: 143,
        insulinUnits: const Value(4),
        glycemicContext: const Value('post_meal'),
        mealType: const Value('dinner'),
        mealDescription: const Value('synthetic fixture dinner'),
        source: const Value('manual'),
        syncStatus: const Value('pending'),
        clientUuid: 'p5-backup-log-0001',
        loggedAt: Value(loggedAt),
        syncAttempts: const Value(2),
      ),
    );

    await db.into(db.chatMessages).insert(
      ChatMessagesCompanion.insert(
        conversationId: 'p5-backup-fixture',
        role: 'user',
        message: 'synthetic non-patient fixture',
        createdAt: loggedAt,
      ),
    );

    await db.addMedicationEvent(
      label: 'synthetic metformin fixture',
      dose: 500,
      unit: 'mg',
      takenAt: loggedAt,
    );
    await db.addReminder(
      title: 'synthetic reminder fixture',
      dueAt: loggedAt.add(const Duration(hours: 6)),
    );
  }

  test('P5-5 local backup restores all Drift-owned pilot tables', () async {
    await seedSyntheticFixture();
    final backup = await LocalBackup.exportJson(db);

    final payload = Map<String, dynamic>.from(jsonDecode(backup) as Map);
    expect(payload['formatVersion'], LocalBackup.formatVersion);
    expect(payload['schemaVersion'], db.schemaVersion);
    expect(payload['logEntries'], hasLength(1));
    expect(payload['patientProfiles'], hasLength(1));
    expect(payload['chatMessages'], hasLength(1));
    expect(payload['medicationEvents'], hasLength(1));
    expect(payload['reminders'], hasLength(1));

    await db.delete(db.logEntries).go();
    await db.delete(db.patientProfiles).go();
    await db.delete(db.chatMessages).go();
    await db.delete(db.medicationEvents).go();
    await db.delete(db.reminders).go();

    await LocalBackup.restoreJson(db, backup);

    final log = await db.select(db.logEntries).getSingle();
    expect(log.id, 11);
    expect(log.bloodSugar, 143);
    expect(log.glycemicContext, 'post_meal');
    expect(log.mealDescription, 'synthetic fixture dinner');
    expect(log.clientUuid, 'p5-backup-log-0001');
    expect(log.syncAttempts, 2);

    final profile = await db.select(db.patientProfiles).getSingle();
    expect(profile.userId, 7);
    expect(profile.diabetesType, 'type2');
    expect(profile.targetRangeLow, 82);
    expect(profile.targetRangeHigh, 155);
    expect(profile.treatment, 'tablets');
    expect(profile.aiConsentGivenAt, DateTime.utc(2026, 8, 1));

    final chat = await db.select(db.chatMessages).getSingle();
    expect(chat.conversationId, 'p5-backup-fixture');
    expect(chat.message, 'synthetic non-patient fixture');

    final medication = await db.select(db.medicationEvents).getSingle();
    expect(medication.label, 'synthetic metformin fixture');
    expect(medication.dose, 500);
    expect(medication.unit, 'mg');

    final reminder = await db.select(db.reminders).getSingle();
    expect(reminder.title, 'synthetic reminder fixture');
    expect(reminder.enabled, isTrue);
  });

  test('P5-5 failed restore rolls back instead of clearing local data', () async {
    await seedSyntheticFixture();
    final originalBackup = await LocalBackup.exportJson(db);
    final payload = Map<String, dynamic>.from(jsonDecode(originalBackup) as Map);
    final logs = (payload['logEntries'] as List).cast<dynamic>();
    final duplicate = Map<String, dynamic>.from(logs.single as Map);
    duplicate['id'] = 999;
    logs.add(duplicate);

    await expectLater(
      LocalBackup.restoreJson(db, jsonEncode(payload)),
      throwsA(anything),
    );

    final retainedLogs = await db.select(db.logEntries).get();
    expect(retainedLogs, hasLength(1));
    expect(retainedLogs.single.id, 11);
    expect(retainedLogs.single.clientUuid, 'p5-backup-log-0001');

    expect(await db.select(db.patientProfiles).get(), hasLength(1));
    expect(await db.select(db.chatMessages).get(), hasLength(1));
    expect(await db.select(db.medicationEvents).get(), hasLength(1));
    expect(await db.select(db.reminders).get(), hasLength(1));
  });
}
