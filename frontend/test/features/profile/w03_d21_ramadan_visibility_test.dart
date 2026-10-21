import 'dart:io';

import 'package:amina/features/profile/profile_screen.dart';
import 'package:amina/core/data/ramadan_context.dart' as context_policy;
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('W03 D21 Ramadan is hidden on Web by default, not removed from native', () {
    expect(kWebRamadanUiEnabled, isFalse);
    expect(shouldShowRamadanProfileSection(isWeb: true), isFalse);
    expect(shouldShowRamadanProfileSection(isWeb: false), isTrue);
    expect(context_policy.shouldApplyRamadanProfileContext(isWeb: true), isFalse);
    expect(context_policy.shouldApplyRamadanProfileContext(isWeb: false), isTrue);
  });

  test('W03 D21 historical period changes native meal vocabulary but not Web', () {
    final date = DateTime(2026, 3, 5);
    final start = DateTime(2026, 2, 18);
    final end = DateTime(2026, 3, 20);
    expect(context_policy.mealTypesForSurfaceDate(date, start, end, isWeb: true),
        context_policy.regularMealTypes);
    expect(context_policy.mealTypesForSurfaceDate(date, start, end, isWeb: false),
        context_policy.ramadanMealTypes);
    expect(context_policy.isRamadanProfileDate(date, start, end), isTrue);
  });

  test('W03 D21 meal picker suppresses stale season on Web at open/date change', () {
    final source = File('lib/features/dashboard/widgets/add_log_sheet.dart').readAsStringSync();
    expect(source, contains('shouldApplyRamadanProfileContext(isWeb: kIsWeb)'));
    expect(source, contains('mealTypesForSurfaceDate('));
    expect(source.split('mealTypesForSurfaceDate(').length - 1, 2);
  });

  test('W03 D21 Web presentation gates section and calendar controls together', () {
    final presentation = File(
      'lib/features/profile/profile_screen_presentation.dart',
    ).readAsStringSync();
    final gate = presentation.indexOf(
      'if (shouldShowRamadanProfileSection(isWeb: kIsWeb)) ...[',
    );
    final section = presentation.indexOf('_buildRamadanSection(l10n)', gate);

    expect(gate, greaterThanOrEqualTo(0));
    expect(section, greaterThan(gate));
    expect(section - gate, lessThan(180));
    // The original implementation survives for a separately reviewed
    // reactivation; the Web user cannot trigger its save action while hidden.
    expect(presentation, contains("ValueKey('profile-ramadan-section')"));
    expect(presentation, contains("Key('ramadan-save-period')"));
    expect(presentation, contains("Key('ramadan-start-date')"));
    expect(presentation, contains("Key('ramadan-end-date')"));
  });

  test('W03 D21 Vercel Web build does not opt into seasonal feature', () {
    final build = File('vercel_build.sh').readAsStringSync();
    expect(build, isNot(contains('IAMINA_WEB_RAMADAN_UI=true')));
  });
  test('W03 D21 synthetic browser audit honors AR without changing patient entrypoint', () {
    final audit = File('lib/ui_browser_audit_main.dart').readAsStringSync();
    final harness = File('tool/w03_d21_web_profile_browser.py').readAsStringSync();
    expect(audit, contains("Uri.base.queryParameters['locale'] == 'ar'"));
    expect(audit, contains('SemanticsBinding.instance.ensureSemantics()'));
    expect(harness, contains('keyboard_focus_trace'));
    expect(harness, contains('keyboard_navigation_verdict'));
    expect(harness, contains('received_dom_keys'));
    expect(harness, contains('reverse_first_return_step'));
    expect(harness, contains('range(28)'));
    expect(harness, contains('Shift keydown was not observed by document'));
    expect(harness, contains('report["problems"] = problems'));
    expect(harness, contains('trace = keyboard_focus_trace(cdp)'));
    expect(harness, contains('reverse_to_earlier_target'));
    expect(harness, contains('Shift+Tab did not return to a previously focused Profile target'));
    expect(harness, contains('if stage == "after" and ramadan:'));
    expect(harness, contains('if stage == "before" and not ramadan:'));
  });
}
