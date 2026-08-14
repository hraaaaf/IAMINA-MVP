import 'package:flutter/material.dart';

import 'app_theme.dart';

/// Canonical patient-facing visual language derived from the certified LOGIN
/// surface. This layer is presentation-only and deliberately carries no
/// clinical, persistence, routing or authorization behavior.
class AminaVisualLanguage {
  const AminaVisualLanguage._();

  static const Color forest = Color(0xFF073D31);
  static const Color forestDeep = Color(0xFF034536);
  static const Color actionGreen = Color(0xFF0B735F);
  static const Color secondaryText = Color(0xFF566B68);
  static const Color fieldBorder = Color(0xFFC5CECC);
  static const Color mintSurface = Color(0xFFE4F7F2);
  static const Color mintBorder = Color(0xFFB8E9DE);
  static const Color mintWaveLight = Color(0xFFDDF8F3);
  static const Color mintWaveStrong = Color(0xFFA8E9DE);

  static const double cardRadius = 24;
  static const double controlRadius = 12;
  static const double fieldRadius = 10;

  /// Matches the LOGIN CTA: darker edges with a restrained illuminated core.
  static const Gradient primaryGradient = LinearGradient(
    colors: [Color(0xFF064D3D), Color(0xFF08765D), Color(0xFF034536)],
    stops: [0, .5, 1],
    begin: AlignmentDirectional.centerStart,
    end: AlignmentDirectional.centerEnd,
  );

  static const List<BoxShadow> cardShadowLight = [
    BoxShadow(
      color: Color(0x1B11423A),
      blurRadius: 32,
      spreadRadius: -8,
      offset: Offset(0, 15),
    ),
    BoxShadow(
      color: Color(0x0D0D1A17),
      blurRadius: 12,
      spreadRadius: -4,
      offset: Offset(0, 5),
    ),
  ];

  static const List<BoxShadow> controlShadowLight = [
    BoxShadow(
      color: Color(0x2A034A39),
      blurRadius: 18,
      spreadRadius: -7,
      offset: Offset(0, 8),
    ),
  ];

  static Color primaryText(BuildContext context) =>
      AminaTheme.isDark(context) ? AminaTheme.dark100 : forest;

  static Color secondary(BuildContext context) =>
      AminaTheme.isDark(context) ? AminaTheme.dark300 : secondaryText;

  static Color cardSurface(BuildContext context) =>
      AminaTheme.isDark(context)
          ? AminaTheme.darkCard
          : Colors.white.withValues(alpha: .975);

  static Color controlSurface(BuildContext context) =>
      AminaTheme.isDark(context)
          ? AminaTheme.darkCardElevated
          : Colors.white.withValues(alpha: .92);

  static Color border(BuildContext context) =>
      AminaTheme.isDark(context)
          ? AminaTheme.dark600.withValues(alpha: .55)
          : Colors.white.withValues(alpha: .9);

  static Color controlBorder(BuildContext context) =>
      AminaTheme.isDark(context)
          ? AminaTheme.dark500.withValues(alpha: .7)
          : fieldBorder;

  static List<BoxShadow> cardShadow(BuildContext context) =>
      AminaTheme.isDark(context) ? AminaTheme.shadowDark : cardShadowLight;

  static BoxDecoration cardDecoration(
    BuildContext context, {
    double radius = cardRadius,
    Color? color,
    Border? borderOverride,
  }) {
    return BoxDecoration(
      color: color ?? cardSurface(context),
      borderRadius: BorderRadius.circular(radius),
      border: borderOverride ?? Border.all(color: border(context)),
      boxShadow: cardShadow(context),
    );
  }

  static BoxDecoration mintIconDecoration(BuildContext context) {
    final dark = AminaTheme.isDark(context);
    return BoxDecoration(
      color: mintSurface.withValues(alpha: dark ? .1 : .92),
      shape: BoxShape.circle,
      border: Border.all(
        color: mintBorder.withValues(alpha: dark ? .38 : .78),
      ),
    );
  }

  /// Applies LOGIN-derived styling to native Material controls used by legacy
  /// and feature-specific screens. The input ThemeData remains the authority
  /// for typography, localization direction and dark/light mode.
  static ThemeData harmonize(ThemeData base) {
    final dark = base.brightness == Brightness.dark;
    final surface = dark ? AminaTheme.darkCard : Colors.white;
    final elevated = dark ? AminaTheme.darkCardElevated : Colors.white;
    final borderColor = dark
        ? AminaTheme.dark500.withValues(alpha: .7)
        : fieldBorder;
    final primary = dark ? AminaTheme.teal400 : actionGreen;
    final primaryTextColor = dark ? AminaTheme.dark100 : forest;
    final secondaryColor = dark ? AminaTheme.dark300 : secondaryText;

    final primaryButtonShape = RoundedRectangleBorder(
      borderRadius: BorderRadius.circular(controlRadius),
    );

    return base.copyWith(
      scaffoldBackgroundColor: dark ? AminaTheme.darkPaper : AminaTheme.paper,
      cardTheme: CardThemeData(
        elevation: 0,
        color: surface,
        surfaceTintColor: Colors.transparent,
        shadowColor: dark
            ? Colors.black.withValues(alpha: .28)
            : forest.withValues(alpha: .10),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(cardRadius),
          side: BorderSide(
            color: dark
                ? AminaTheme.dark600.withValues(alpha: .55)
                : Colors.white.withValues(alpha: .9),
          ),
        ),
      ),
      appBarTheme: base.appBarTheme.copyWith(
        backgroundColor: dark ? AminaTheme.darkPaper : AminaTheme.paper,
        foregroundColor: primaryTextColor,
        surfaceTintColor: Colors.transparent,
        elevation: 0,
        centerTitle: false,
        titleTextStyle: base.textTheme.titleLarge?.copyWith(
          color: primaryTextColor,
          fontWeight: FontWeight.w800,
          letterSpacing: -.35,
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: elevated,
        hintStyle: TextStyle(color: secondaryColor, fontSize: 13.5),
        labelStyle: TextStyle(
          color: primary,
          fontSize: 13,
          fontWeight: FontWeight.w600,
        ),
        contentPadding: const EdgeInsetsDirectional.fromSTEB(12, 10, 12, 10),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(fieldRadius),
          borderSide: BorderSide(color: borderColor, width: 1.1),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(fieldRadius),
          borderSide: BorderSide(color: borderColor, width: 1.1),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(fieldRadius),
          borderSide: BorderSide(color: primary, width: 1.4),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(fieldRadius),
          borderSide: const BorderSide(color: AminaTheme.dangerFg, width: 1.2),
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          foregroundColor: Colors.white,
          backgroundColor: forestDeep,
          disabledForegroundColor: dark ? AminaTheme.dark400 : AminaTheme.ink500,
          disabledBackgroundColor: dark ? AminaTheme.dark600 : AminaTheme.ink200,
          minimumSize: const Size(44, 44),
          padding: const EdgeInsets.symmetric(horizontal: 20),
          elevation: 0,
          shadowColor: Colors.transparent,
          surfaceTintColor: Colors.transparent,
          shape: primaryButtonShape,
          textStyle: const TextStyle(
            fontSize: 14.5,
            fontWeight: FontWeight.w700,
          ),
        ),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          foregroundColor: Colors.white,
          backgroundColor: forestDeep,
          disabledBackgroundColor: dark ? AminaTheme.dark600 : AminaTheme.ink300,
          minimumSize: const Size(44, 44),
          padding: const EdgeInsets.symmetric(horizontal: 20),
          shape: primaryButtonShape,
          textStyle: const TextStyle(
            fontSize: 14.5,
            fontWeight: FontWeight.w700,
          ),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: primary,
          backgroundColor: surface,
          minimumSize: const Size(44, 42),
          padding: const EdgeInsets.symmetric(horizontal: 20),
          side: BorderSide(color: primary, width: 1.15),
          shape: primaryButtonShape,
          textStyle: const TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w700,
          ),
        ),
      ),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          foregroundColor: primary,
          shape: primaryButtonShape,
          textStyle: const TextStyle(fontWeight: FontWeight.w600),
        ),
      ),
      floatingActionButtonTheme: FloatingActionButtonThemeData(
        backgroundColor: forestDeep,
        foregroundColor: Colors.white,
        elevation: 2,
        focusElevation: 3,
        hoverElevation: 3,
        shape: const CircleBorder(),
      ),
      dialogTheme: DialogThemeData(
        backgroundColor: surface,
        surfaceTintColor: Colors.transparent,
        elevation: 6,
        shadowColor: Colors.black.withValues(alpha: dark ? .30 : .12),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(cardRadius),
        ),
        titleTextStyle: base.textTheme.titleLarge?.copyWith(
          color: primaryTextColor,
          fontWeight: FontWeight.w800,
        ),
        contentTextStyle: base.textTheme.bodyMedium?.copyWith(
          color: secondaryColor,
          height: 1.45,
        ),
      ),
      bottomSheetTheme: BottomSheetThemeData(
        backgroundColor: surface,
        surfaceTintColor: Colors.transparent,
        modalBackgroundColor: surface,
        modalBarrierColor: Colors.black.withValues(alpha: .34),
        elevation: 4,
        modalElevation: 6,
        shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(cardRadius)),
        ),
      ),
      chipTheme: base.chipTheme.copyWith(
        backgroundColor: dark
            ? AminaTheme.darkCardElevated
            : mintSurface.withValues(alpha: .65),
        selectedColor: dark
            ? AminaTheme.teal700.withValues(alpha: .28)
            : mintSurface,
        side: BorderSide(color: borderColor.withValues(alpha: .72)),
        labelStyle: TextStyle(
          color: primaryTextColor,
          fontSize: 12,
          fontWeight: FontWeight.w600,
        ),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(controlRadius),
        ),
      ),
      listTileTheme: ListTileThemeData(
        iconColor: primary,
        textColor: primaryTextColor,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(controlRadius),
        ),
        contentPadding: const EdgeInsetsDirectional.symmetric(horizontal: 12),
        minTileHeight: 44,
      ),
      switchTheme: SwitchThemeData(
        thumbColor: WidgetStateProperty.resolveWith((states) {
          return states.contains(WidgetState.selected) ? Colors.white : null;
        }),
        trackColor: WidgetStateProperty.resolveWith((states) {
          return states.contains(WidgetState.selected)
              ? primary
              : borderColor.withValues(alpha: .8);
        }),
        trackOutlineColor: WidgetStateProperty.all(Colors.transparent),
      ),
      snackBarTheme: SnackBarThemeData(
        backgroundColor: dark ? AminaTheme.darkCardElevated : forestDeep,
        contentTextStyle: const TextStyle(
          color: Colors.white,
          fontSize: 13,
          fontWeight: FontWeight.w600,
        ),
        behavior: SnackBarBehavior.floating,
        elevation: 4,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(controlRadius),
        ),
      ),
      dividerTheme: DividerThemeData(
        color: dark
            ? AminaTheme.dark600.withValues(alpha: .48)
            : fieldBorder.withValues(alpha: .52),
        space: 1,
        thickness: 1,
      ),
      navigationBarTheme: base.navigationBarTheme.copyWith(
        backgroundColor: surface,
        indicatorColor: dark
            ? AminaTheme.teal700.withValues(alpha: .24)
            : mintSurface,
        labelTextStyle: WidgetStateProperty.resolveWith((states) {
          final selected = states.contains(WidgetState.selected);
          return TextStyle(
            fontSize: 11,
            fontWeight: selected ? FontWeight.w700 : FontWeight.w600,
            color: selected ? primary : secondaryColor,
          );
        }),
      ),
      popupMenuTheme: PopupMenuThemeData(
        color: elevated,
        surfaceTintColor: Colors.transparent,
        elevation: 4,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
        ),
        textStyle: TextStyle(
          color: primaryTextColor,
          fontSize: 13,
          fontWeight: FontWeight.w600,
        ),
      ),
      textTheme: base.textTheme.copyWith(
        titleLarge: base.textTheme.titleLarge?.copyWith(
          color: primaryTextColor,
          fontWeight: FontWeight.w700,
        ),
        titleMedium: base.textTheme.titleMedium?.copyWith(
          color: primaryTextColor,
          fontWeight: FontWeight.w600,
        ),
        bodyMedium: base.textTheme.bodyMedium?.copyWith(color: secondaryColor),
      ),
    );
  }
}
