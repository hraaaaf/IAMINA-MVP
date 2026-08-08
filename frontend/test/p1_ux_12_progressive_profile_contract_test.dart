import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

String _read(String path) => File(path).readAsStringSync();

void main() {
  test(
    'profile uses progressive thematic sections with truthful medical summary',
    () {
      final source = _read('lib/features/profile/profile_screen.dart');
      expect(source, contains("ValueKey('profile-medical-section')"));
      expect(source, contains("ValueKey('profile-iamina-section')"));
      expect(source, contains("ValueKey('profile-account-section')"));
      expect(source, contains('ExpansionTile('));
      expect(source, contains('maintainState: true'));
      expect(source, contains('subtitle: _medicalSummary(l10n)'));
      expect(source, isNot(contains('_ProfileCompletionHeader')));
    },
  );

  test(
    'all sections start collapsed while medical summary remains truthful',
    () {
      final source = _read('lib/features/profile/profile_screen.dart');
      final medical = source.indexOf('Widget _buildMedicalSection');
      final account = source.indexOf('Widget _buildAccountSection');
      final section = source.indexOf('Widget _buildProfileSection');
      expect(medical, greaterThan(0));
      expect(account, greaterThan(medical));
      expect(section, greaterThan(account));
      final medicalBlock = source.substring(medical, account);
      expect(medicalBlock, contains('initiallyExpanded: false'));
      expect(source, isNot(contains('initiallyExpanded: true')));
      expect(source, contains('_hasPersistedProfile'));
      expect(source, contains('profileMedicalSectionHint'));
      expect(source, contains('if (!_hasPersistedProfile)'));
      expect(medicalBlock, contains('saveProfile'));
    },
  );

  test('sensitive actions stay grouped in a distinct account section', () {
    final source = _read('lib/features/profile/profile_screen.dart');
    final account = source.indexOf('Widget _buildAccountSection');
    final generic = source.indexOf('Widget _buildProfileSection');
    final block = source.substring(account, generic);
    expect(block, contains('dangerZone'));
    expect(block, contains('_confirmSignOut'));
    expect(block, contains('_confirmWithdrawConsent'));
    expect(block, contains('Size.fromHeight(48)'));
  });

  test('FR EN AR own all progressive-profile section labels', () {
    for (final locale in <String>['fr', 'en', 'ar']) {
      final arb = _read('lib/l10n/app_$locale.arb');
      for (final key in <String>[
        'profileMedicalSection',
        'profileMedicalSectionHint',
        'profileIaminaSection',
        'profileIaminaSectionHint',
        'profileAccountSection',
        'profileAccountSectionHint',
      ]) {
        expect(arb, contains('"$key"'));
      }
    }
  });
}
