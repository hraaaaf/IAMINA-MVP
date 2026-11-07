import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

String source(String path) => File(path).readAsStringSync();

void checkPng(String path, int width, int height) {
  final bytes = File(path).readAsBytesSync();
  expect(bytes.length, greaterThan(24), reason: path);
  expect(bytes.take(8).toList(), [137, 80, 78, 71, 13, 10, 26, 10], reason: path);
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
    ]) {
      expect(source(path), contains('iamina_logo_mark.png'), reason: path);
    }
    for (final path in [
      'lib/features/dashboard/dashboard_premium_screen.dart',
      'lib/features/companion/companion_premium_screen_presentation.dart',
    ]) {
      final rendered = source(path);
      expect(rendered, contains('iamina_logo_horizontal.png'), reason: path);
      expect(rendered, contains("label: 'IAMINA'"), reason: path);
      expect(rendered, isNot(contains("Text(\n                'IAmina'")), reason: path);
    }
    final onboarding = source('lib/features/auth/onboarding_chat_screen.dart');
    expect(onboarding, contains('iamina_logo_horizontal.png'));
    expect(onboarding, contains('colorBlendMode: BlendMode.srcIn'));
    for (final path in [
      'lib/features/auth/login_screen_fr_certified.dart',
      'lib/features/auth/login_screen_mena.dart',
      'lib/features/auth/app_lock_setup_screen.dart',
      'lib/features/auth/app_lock_unlock_screen.dart',
    ]) {
      expect(source(path), contains('colorBlendMode: BlendMode.srcIn'), reason: path);
    }
  });

  test('governed chat reuses V4 mark and lockup without legacy branding', () {
    final chat = source('lib/features/companion/companion_conversation_screen.dart');
    expect(chat, contains('iamina_logo_horizontal.png'));
    final header = chat.split('class _ConversationHeader').last.split('class _EmptyConversation').first;
    final welcome = chat.split('class _EmptyConversation').last.split('class _Composer').first;
    expect(header, isNot(contains('Conversation gouvernée')));
    expect(header, isNot(contains('Governed conversation')));
    expect(header, isNot(contains('محادثة محكومة')));
    expect(welcome, isNot(contains('iamina_logo_mark.png')));
    expect(welcome, isNot(contains('Parler avec IAMINA')));
    expect(welcome, isNot(contains('Talk with IAMINA')));
    expect(welcome, isNot(contains('تحدث مع IAMINA')));
    expect(welcome, contains('Pose une question avec tes mots'));
    expect(welcome, contains('Pour commencer'));
    // The in-conversation typing state can still use the official square mark.
    expect(chat, contains('iamina_logo_mark.png'));
    expect(chat, contains("label: 'IAMINA'"));
    expect(chat, contains("colorBlendMode: BlendMode.srcIn"));
    expect(chat, isNot(contains('Icons.forum_outlined')));
    expect(chat, isNot(contains('IAmina')));
  });

  test('all Web/PWA icons and in-app images are correctly sized PNGs', () {
    checkPng('assets/images/iamina_logo_vertical.png', 400, 410);
    checkPng('assets/images/iamina_logo_horizontal.png', 580, 116);
    checkPng('assets/images/iamina_logo_mark.png', 320, 320);
    // Approved conversational brain+medical icon is only for the dashboard FAB.
    checkPng('assets/images/iamina_chatbrain_diabetes.png', 96, 96);
    // RGBA: the ChatBrain art must have an alpha channel, not an opaque
    // square that replaces the removed Dashboard FAB background.
    expect(
      File('assets/images/iamina_chatbrain_diabetes.png')
          .readAsBytesSync()[25],
      6,
      reason: 'ChatBrain must be an RGBA PNG',
    );
    // Legacy URL is a V4 alias for already-installed Web/PWA clients.
    checkPng('assets/images/logo_amina.png', 320, 320);
    expect(
      File('assets/images/logo_amina.png').readAsBytesSync(),
      File('assets/images/iamina_logo_mark.png').readAsBytesSync(),
    );
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
    final version = source('pubspec.yaml')
        .split('\n')
        .firstWhere((line) => line.startsWith('version: '))
        .split(' ')
        .last;
    expect(sw, contains("IAMINA_CACHE_SCHEMA = '$version'"));
    expect(sw, contains('./assets/assets/images/logo_amina.png'));
    for (final icon in icons) {
      expect(sw, contains('./' + (icon['src'] as String)));
    }
    expect(source('web/index.html'), contains('href="favicon.png"'));
  });
}
