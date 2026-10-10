import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('meal photo uses consent-aware shared network client, not a new client', () {
    final source = File('lib/features/journal/widgets/meal_capture_panel.dart')
        .readAsStringSync();
    expect(
      source,
      contains('context.read<ApiClient>().analyzeMealImage(bytes, mimeType: mime)'),
    );
    expect(source, isNot(contains('ApiClient().analyzeMealImage(')));
    expect(source, contains('if (!widget.canUsePhotoRecognition)'));
  });
  test('add-log voice dictation reuses the consent-aware shared client', () {
    final source = File('lib/features/dashboard/widgets/add_log_sheet.dart')
        .readAsStringSync();
    expect(
      source,
      contains('context.read<ApiClient>().transcribeAudio(audioBytes, mimeType)'),
    );
    expect(source, isNot(contains('ApiClient().transcribeAudio(')));
  });

}
