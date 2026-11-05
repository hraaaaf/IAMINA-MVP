import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

String source(String path) => File(path).readAsStringSync();

void checkPng(String path, int width, int height) {
  final bytes = File(path).readAsBytesSync();
  expect(bytes.length, greaterThan(24), reason: path);
  expect(bytes.take(8), [137, 80, 78, 71, 13, 10, 26, 10], reason: path);
  int dimensionAt(int offset) =>
      (bytes[offset] << 24) |
      (bytes[offset + 1] << 16) |
      (bytes[offset + 2] << 8) |
      bytes[offset + 3];
  expect(dimensionAt(16), width, reason: path);
  expect(dimensionAt(20), height, reason: path);
}

void main() {
  test('only canonical V4 branding assets are referenced in Flutter code', () {
    final dartFiles = Directory('lib')
        .listSync(recursive: true)
        .whereType<File>()
        .where((file) => file.path.endsWith('.dart'));
    for (final file in dartFiles) {
      expect(
        file.readAsStringSync(),
        isNot(contains('logo_amina.png')),
        reason: file.path,
      );
    }
    for (final path in [
      'lib/features/auth/login_screen_fr_certified.dart',
      'lib/features/auth/login_screen_mena.dart',
      'lib/features/auth/app_lock_setup_screen.dart',
      'lib/features/auth/app_lock_unlock_screen.dart',
    ]) {
      expect(source(path), contains('iamina_logo_vertical.png'), reason: path);
    }
    for (final path in [
      'lib/core/widgets/mobile_page_header.dart',
      'lib/core/widgets/premium_task_brand_overlay.dart',
      'lib/features/dashboard/dashboard_premium_screen.dart',
    ]) {
      expect(source(path), contains('iamina_logo_mark.png'), reason: path);
    }
    expect(
      source('lib/features/auth/onboarding_chat_screen.dart'),
      contains('iamina_logo_horizontal.png'),
    );
  });

  test('all Web/PWA icons and in-app images are correctly sized PNGs', () {
    checkPng('assets/images/iamina_logo_vertical.png', 400, 410);
    checkPng('assets/images/iamina_logo_horizontal.png', 580, 116);
    checkPng('assets/images/iamina_logo_mark.png', 320, 320);
    checkPng('web/favicon.png', 64, 64);
    checkPng('web/icons/Icon-192.png', 192, 192);
    checkPng('web/icons/Icon-512.png', 512, 512);
    checkPng('web/icons/Icon-maskable-192.png', 192, 192);
    checkPng('web/icons/Icon-maskable-512.png', 512, 512);
  });

  test('PWA icon manifest and offline cache reference V4 assets', () {
    final m = jsonDecode(source('web/manifest.json')) as Map<String, dynamic>;
    expect(m['theme_color'], '#073D31');
    expect(m['background_color'], '#FBFCFB');
    final icons = (m['icons'] as List).cast<Map<String, dynamic>>();
    for (final icon in icons) {
      final path = 'web/${icon['src']}';
      expect(File(path).existsSync(), true, reason: path);
    }
    final sw = source('web/iamina_service_worker.js');
    expect(sw, contains("IAMINA_CACHE_SCHEMA = '0.1.0+1-logo-v4'"));
    for (final icon in icons) {
      expect(sw, contains("./${icon['src']}"));
    }
    expect(source('web/index.html'), contains('href="favicon.png"'));
  });
}
