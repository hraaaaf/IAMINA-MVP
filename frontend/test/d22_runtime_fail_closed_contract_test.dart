import 'dart:io';

import 'package:amina/data/drift/database.dart';
import 'package:amina/features/dashboard/clinical_engine.dart';
import 'package:flutter_test/flutter_test.dart';

/// P0 fail-closed runtime regression: patient target authority remains
/// unknown until a clinical + G7 schema has been approved. These are
/// source-boundary checks, NOT a full Chrome FUE.
void main() {
  final onboarding = File('lib/features/auth/onboarding_chat_screen.dart')
      .readAsStringSync();
  final profile = File('lib/features/profile/profile_screen.dart')
      .readAsStringSync();
  final presentation =
      File('lib/features/profile/profile_screen_presentation.dart')
          .readAsStringSync();
  final dashboard =
      File('lib/features/dashboard/dashboard_screen.dart').readAsStringSync();
  final premium =
      File('lib/features/dashboard/dashboard_premium_screen.dart')
          .readAsStringSync();
  final journal =
      File('lib/features/journal/journal_screen.dart').readAsStringSync();
  final recent =
      File('lib/features/dashboard/widgets/recent_entries.dart')
          .readAsStringSync();

  test('onboarding never explicitly assigns 70/180 to a selected unit', () {
    final finish = onboarding.substring(onboarding.indexOf('Future<void> _finish()'));
    expect(finish, isNot(contains('targetRangeLow: const drift.Value(70)')));
    expect(finish, isNot(contains('targetRangeHigh: const drift.Value(180)')));
  });

  test('changing profile unit does not overwrite original legacy bounds', () {
    final save = profile.substring(profile.indexOf('void _saveProfile()'));
    final writeScope = save.substring(0, save.indexOf('bool remoteMirrorConfirmed'));
    expect(writeScope, isNot(contains('targetRangeLow:')));
    expect(writeScope, isNot(contains('targetRangeHigh:')));
    expect(writeScope, contains('db.update(db.patientProfiles)'));
    expect(presentation, contains("Key('d22-unverified-target-blocked')"));
    expect(presentation, contains('if (!_d22TargetsEditable)'));
  });

  test('premium cannot mark an unverified numeric target as configured', () {
    expect(premium, contains('const double? low = null;'));
    expect(premium, contains('const double? high = null;'));
  });

  test('main dashboard displays explicit no-TIR warning, not legacy TIR cards', () {
    final visible = dashboard.substring(
      dashboard.indexOf('return StreamBuilder<PatientProfileData?>'),
    );
    expect(visible, contains("Key('d22-manual-tir-unavailable')"));
    expect(visible, isNot(contains('_HeroTIR(')));
    expect(visible, isNot(contains('_TIRCard(')));
    expect(visible, isNot(contains('_MetricRow(')));
    expect(visible, isNot(contains('_ChartSection(')));
  });

  test('journal and recent entries cannot color by unknown target', () {
    expect(journal, isNot(contains('profile?.targetRangeLow ?? 70.0')));
    expect(journal, isNot(contains('profile?.targetRangeHigh ?? 180.0')));
    expect(journal, isNot(contains('val < low || val > high')));
    expect(recent, isNot(contains('if (v < low)')));
    expect(recent, isNot(contains('if (v > high)')));
  });

  test('legacy manual-log percent is never reported as CGM time in range', () {
    expect(
      () => ClinicalEngine.calcTIR(<LogEntryData>[], 70, 180),
      throwsUnsupportedError,
    );
  });
}
