import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('mobile shells declare microphone permission for Companion voice', () {
    final android = File(
      'android/app/src/main/AndroidManifest.xml',
    ).readAsStringSync();
    final ios = File('ios/Runner/Info.plist').readAsStringSync();

    expect(android, contains('android.permission.RECORD_AUDIO'));
    expect(ios, contains('NSMicrophoneUsageDescription'));
    expect(
      ios,
      contains(
        'IAmina utilise le microphone uniquement lorsque vous enregistrez un message vocal.',
      ),
    );
  });
}
