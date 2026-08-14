import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

String _read(String path) => File(path).readAsStringSync();

void main() {
  test('global rendering fallback follows the active locale', () {
    final main = _read('lib/main.dart');
    final copy = _read('lib/core/localization/app_shell_localized_copy.dart');

    expect(main, contains('app_shell_localized_copy.dart'));
    expect(main, contains('AppLocalizations.of(context)!.renderError'));
    expect(main, isNot(contains("'Une erreur de rendu est survenue'")));

    expect(copy, contains("en: 'A rendering error occurred'"));
    expect(copy, contains("fr: 'Une erreur de rendu est survenue'"));
    expect(copy, contains("ar: 'حدث خطأ أثناء عرض الواجهة'"));
  });

  test('iOS privacy prompts are bundled in EN FR AR', () {
    final info = _read('../ios/Runner/Info.plist');
    final project = _read('../ios/Runner.xcodeproj/project.pbxproj');
    final en = _read('../ios/Runner/en.lproj/InfoPlist.strings');
    final fr = _read('../ios/Runner/fr.lproj/InfoPlist.strings');
    final ar = _read('../ios/Runner/ar.lproj/InfoPlist.strings');

    expect(info, contains('<key>CFBundleLocalizations</key>'));
    for (final locale in <String>['en', 'fr', 'ar']) {
      expect(info, contains('<string>$locale</string>'));
      expect(project, contains('\t\t\t\t$locale,'));
      expect(project, contains('$locale.lproj/InfoPlist.strings'));
    }
    expect(project, contains('InfoPlist.strings in Resources'));
    expect(project, contains('isa = PBXVariantGroup'));

    for (final localized in <String>[en, fr, ar]) {
      expect(localized, contains('"NSCameraUsageDescription"'));
      expect(localized, contains('"NSPhotoLibraryUsageDescription"'));
    }
    expect(en, contains('IAmina uses the camera'));
    expect(fr, contains('IAmina utilise la caméra'));
    expect(ar, contains('يستخدم IAmina الكاميرا'));
  });
}
