import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('Profile presentation stays free of persistence and account orchestration', () {
    final state = File(
      'lib/features/profile/profile_screen.dart',
    ).readAsStringSync();
    final presentation = File(
      'lib/features/profile/profile_screen_presentation.dart',
    ).readAsStringSync();

    expect(state, contains("part 'profile_screen_presentation.dart';"));
    expect(state, contains('class _ProfileScreenState'));
    expect(state, contains('context.read<AppDatabase>()'));
    expect(state, contains('context.read<ApiClient>()'));
    expect(state, contains('context.read<AuthService>()'));
    expect(state, contains('context.read<ConsentService>()'));
    expect(state, contains('patchProfile('));
    expect(state, contains('withdrawConsent()'));
    expect(state, contains('insertOnConflictUpdate('));
    expect(state, contains('Widget build(BuildContext context) => _buildPresentation(context);'));
    expect(state, isNot(contains('Widget _buildMedicalSection(')));
    expect(state, isNot(contains('Widget _buildAccountSection(')));
    expect(state, isNot(contains('Widget _buildProfileSection(')));

    expect(
      presentation,
      contains('extension _ProfileScreenPresentation on _ProfileScreenState'),
    );
    expect(presentation, contains('Widget _buildPresentation('));
    expect(presentation, contains('Widget _buildMedicalSection('));
    expect(presentation, contains('Widget _buildRamadanSection('));
    expect(presentation, contains('Widget _buildAccountSection('));
    expect(presentation, contains('Widget _buildProfileSection('));
    expect(presentation, isNot(contains('context.read<AppDatabase>()')));
    expect(presentation, isNot(contains('context.read<ApiClient>()')));
    expect(presentation, isNot(contains('context.read<AuthService>()')));
    expect(presentation, isNot(contains('context.read<ConsentService>()')));
    expect(presentation, isNot(contains('patchProfile(')));
    expect(presentation, isNot(contains('withdrawConsent()')));
    expect(presentation, isNot(contains('insertOnConflictUpdate(')));
    expect(presentation, isNot(contains("import 'package:")));
  });
}
