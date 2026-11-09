import 'dart:io';

import 'package:amina/core/data/ramadan_context.dart' as d21;
import 'package:amina/features/profile/profile_screen.dart'
    show shouldShowRamadanProfileSection;
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('D21 defaults OFF on Web, leaves native behavior intact', () {
    expect(d21.kWebRamadanUiEnabled, isFalse);
    expect(shouldShowRamadanProfileSection(isWeb: true), isFalse);
    expect(shouldShowRamadanProfileSection(isWeb: false), isTrue);
    expect(d21.shouldApplyRamadanProfileContext(isWeb: true), isFalse);
    expect(d21.shouldApplyRamadanProfileContext(isWeb: false), isTrue);
  });

  test('D21 preserves legacy periods but not Web Ramadan meal choices', () {
    final day = DateTime(2026, 3, 5);
    final start = DateTime(2026, 2, 18);
    final end = DateTime(2026, 3, 20);
    expect(d21.isRamadanProfileDate(day, start, end), isTrue);
    expect(d21.mealTypesForProfileDate(day, start, end),
        d21.ramadanMealTypes);
    expect(d21.mealTypesForSurfaceDate(day, start, end, isWeb: true),
        d21.regularMealTypes);
    expect(d21.mealTypesForSurfaceDate(day, start, end, isWeb: false),
        d21.ramadanMealTypes);
  });

  test('D21 guards the complete Profile section including date actions', () {
    final source = File('lib/features/profile/profile_screen_presentation.dart')
        .readAsStringSync();
    const gate = 'if (shouldShowRamadanProfileSection(isWeb: kIsWeb)) ...[';
    final gateAt = source.indexOf(gate);
    expect(gateAt, greaterThanOrEqualTo(0));
    expect(source.indexOf('_buildRamadanSection(l10n)', gateAt),
        inInclusiveRange(gateAt, gateAt + 180));
    expect(source, contains("Key('ramadan-save-period')"));
    expect(source, contains("Key('ramadan-start-date')"));
    expect(source, contains("Key('ramadan-end-date')"));
  });

  test('D21 guards initial and changed dates in the live add-log sheet', () {
    final source = File('lib/features/dashboard/widgets/add_log_sheet.dart')
        .readAsStringSync();
    expect(source, contains('shouldApplyRamadanProfileContext(isWeb: kIsWeb)'));
    expect(source.split('mealTypesForSurfaceDate(').length - 1, 2);
    expect(source.split('isWeb: kIsWeb,').length - 1, greaterThanOrEqualTo(2));
  });

  test('D21 Vercel build script never opts into unreviewed Ramadan UI', () {
    final source = File('vercel_build.sh').readAsStringSync();
    expect(source, isNot(contains('IAMINA_WEB_RAMADAN_UI=true')));
  });
}
