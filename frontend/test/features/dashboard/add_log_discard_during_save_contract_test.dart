import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('decision #13 refuses leaving during an unfinished measurement write', () {
    final src = File('lib/features/dashboard/widgets/add_log_sheet.dart')
        .readAsStringSync();
    final start = src.indexOf('Future<bool> _confirmLeave(');
    final end = src.indexOf('void _close()', start);
    expect(start, greaterThan(0));
    expect(end, greaterThan(start));
    final guard = src.substring(start, end);
    final pendingWrite = guard.indexOf('if (_saving) return false;');
    final checkDraft = guard.indexOf('if (!_hasUnsavedData) return true;');
    expect(pendingWrite, greaterThanOrEqualTo(0));
    expect(checkDraft, greaterThan(pendingWrite));
    expect(guard, contains('if (_mealVoiceBusy)'));
    expect(guard, contains('showDialog<bool>'));
    expect(guard, contains('l10n.journalContinueEditing'));
    expect(guard, contains('l10n.journalDiscard'));
    expect(guard, contains('return leave == true;'));
  });

  test('decision #13 covers both hardware back and app back action', () {
    final src = File('lib/features/dashboard/widgets/add_log_sheet.dart')
        .readAsStringSync();
    expect(src, contains('return PopScope('));
    expect(src, contains('canPop: false'));
    expect(src, contains('onPopInvokedWithResult:'));
    expect(src, contains('onBack: () async {'));
    expect(
      '_confirmLeave(l10n)'.allMatches(src).length,
      greaterThanOrEqualTo(2),
    );
  });
}
