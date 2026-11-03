import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:amina/core/theme/amina_visual_language.dart';
import 'package:amina/core/theme/app_theme.dart';

/// D22 F07: offline Flutter Web must not lose locally vendored Arabic glyphs
/// when visual harmonization overrides the base Material control themes.
void main() {
  for (final dark in [false, true]) {
    test('Web Arabic fallback is retained on ${dark ? "dark" : "light"} controls', () {
      final theme = AminaVisualLanguage.harmonize(
        dark ? AminaTheme.dark : AminaTheme.light,
      );
      const arabic = 'NotoSansArabic';
      final states = <WidgetState>{};
      expect(theme.elevatedButtonTheme.style?.textStyle?.resolve(states)?.fontFamilyFallback,
          contains(arabic));
      expect(theme.filledButtonTheme.style?.textStyle?.resolve(states)?.fontFamilyFallback,
          contains(arabic));
      expect(theme.outlinedButtonTheme.style?.textStyle?.resolve(states)?.fontFamilyFallback,
          contains(arabic));
      expect(theme.textButtonTheme.style?.textStyle?.resolve(states)?.fontFamilyFallback,
          contains(arabic));
      expect(theme.chipTheme.labelStyle?.fontFamilyFallback, contains(arabic));
      expect(theme.navigationBarTheme.labelTextStyle?.resolve(states)?.fontFamilyFallback,
          contains(arabic));
      expect(theme.snackBarTheme.contentTextStyle?.fontFamilyFallback,
          contains(arabic));
      expect(theme.popupMenuTheme.textStyle?.fontFamilyFallback,
          contains(arabic));
    });
  }
}
