import 'dart:io';

import 'package:amina/data/drift/database.dart';
import 'package:amina/services/offline_demo_audit_seed.dart';
import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  for (final condition in const <({bool auditAllowed, bool offlineDemo})>[
    (auditAllowed: false, offlineDemo: false),
    (auditAllowed: false, offlineDemo: true),
    (auditAllowed: true, offlineDemo: false),
  ]) {
    test(
      'decision #11 never seeds actual patient: audit=${condition.auditAllowed} demo=${condition.offlineDemo}',
      () async {
        final db = AppDatabase(NativeDatabase.memory());
        addTearDown(db.close);

        expect(await db.countLogs(), 0);
        expect(await db.select(db.patientProfiles).get(), isEmpty);
        expect(await db.select(db.reminders).get(), isEmpty);

        await seedOfflineDemoAuditData(
          db,
          auditAllowed: condition.auditAllowed,
          offlineDemo: condition.offlineDemo,
        );

        expect(await db.countLogs(), 0);
        expect(await db.select(db.patientProfiles).get(), isEmpty);
        expect(await db.select(db.reminders).get(), isEmpty);
      },
    );
  }

  test('decision #11 audit seed is gated behind BOTH positive flags', () {
    final seedCode = File('lib/services/offline_demo_audit_seed.dart')
        .readAsStringSync();
    final runtime = File('lib/main.dart').readAsStringSync();
    expect(seedCode, contains('if (!auditAllowed || !offlineDemo) return;'));
    expect(runtime, contains('await seedOfflineDemoAuditData('));
    expect(runtime, contains('auditAllowed: auditAllowed'));
    expect(runtime, contains('offlineDemo: kOfflineDemo'));
  });
}
