import 'dart:io';

import 'package:amina/features/profile/profile_screen.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('W03 D21 Ramadan is hidden on Web by default, not removed from native', () {
    expect(kWebRamadanUiEnabled, isFalse);
    expect(shouldShowRamadanProfileSection(isWeb: true), isFalse);
    expect(shouldShowRamadanProfileSection(isWeb: false), isTrue);
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
    expect(harness, contains('if stage == "after" and ramadan:'));
    expect(harness, contains('if stage == "before" and not ramadan:'));
  });
}
