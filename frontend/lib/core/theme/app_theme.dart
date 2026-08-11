import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter/material.dart';

// ─────────────────────────────────────────────────────────────────────────────
// Tweaks State
// ─────────────────────────────────────────────────────────────────────────────

enum TweaksDirection { clinique, editorial, dense }

enum TweaksAccent { teal, ocean, ambre }

enum TweaksDensity { confort, compact }

class TweaksNotifier extends ChangeNotifier {
  TweaksDirection direction = TweaksDirection.clinique;
  bool isDark = false;
  TweaksDensity density = TweaksDensity.confort;
  TweaksAccent accent = TweaksAccent.teal;

  void setDirection(TweaksDirection v) {
    direction = v;
    notifyListeners();
  }

  void setDark(bool v) {
    isDark = v;
    notifyListeners();
  }

  void setDensity(TweaksDensity v) {
    density = v;
    notifyListeners();
  }

  void setAccent(TweaksAccent v) {
    accent = v;
    notifyListeners();
  }

  Color get primaryColor => switch (accent) {
    TweaksAccent.teal => AminaTheme.teal500,
    TweaksAccent.ocean => AminaTheme.ocean500,
    TweaksAccent.ambre => AminaTheme.ambre500,
  };

  Color get primaryDark => switch (accent) {
    TweaksAccent.teal => AminaTheme.teal700,
    TweaksAccent.ocean => AminaTheme.ocean700,
    TweaksAccent.ambre => AminaTheme.ambre700,
  };

  Color get primaryLight => switch (accent) {
    TweaksAccent.teal => AminaTheme.teal50,
    TweaksAccent.ocean => AminaTheme.ocean50,
    TweaksAccent.ambre => AminaTheme.ambre50,
  };

  Gradient get gradient => switch (accent) {
    TweaksAccent.teal => AminaTheme.heroGradientDeep,
    TweaksAccent.ocean => AminaTheme.oceanGradient,
    TweaksAccent.ambre => AminaTheme.ambreGradient,
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// AminaTheme
// ─────────────────────────────────────────────────────────────────────────────

class AminaTheme {
  // ── Teal palette ────────────────────────────────────────────────────────────
  static const Color teal400 = Color(0xFF3CC3A0);
  static const Color teal500 = Color(0xFF14A984);
  static const Color teal600 = Color(0xFF0E8C6E);
  static const Color teal700 = Color(0xFF0B6E57);
  static const Color teal800 = Color(0xFF0A5544);
  static const Color teal900 = Color(0xFF073B30);
  static const Color teal50 = Color(0xFFECFBF6);
  static const Color teal100 = Color(0xFFD4F5E9);
  static const Color teal200 = Color(0xFFA9EAD3);

  // ── Ocean palette ────────────────────────────────────────────────────────────
  static const Color ocean500 = Color(0xFF0EA5E9);
  static const Color ocean700 = Color(0xFF0369A1);
  static const Color ocean50 = Color(0xFFE0F2FE);
  static const Color ocean400 = Color(0xFF38BDF8);

  // ── Ambre palette ────────────────────────────────────────────────────────────
  static const Color ambre500 = Color(0xFFF59E0B);
  static const Color ambre700 = Color(0xFFB45309);
  static const Color ambre50 = Color(0xFFFEF3C7);
  static const Color ambre400 = Color(0xFFFBBF24);

  // ── Ink palette (light) ──────────────────────────────────────────────────────
  static const Color ink900 = Color(0xFF0D1A17);
  static const Color ink800 = Color(0xFF182622);
  static const Color ink700 = Color(0xFF1F332E);
  static const Color ink600 = Color(0xFF3A4F49);
  static const Color ink500 = Color(0xFF5B716B);
  static const Color ink400 = Color(0xFF869994);
  static const Color ink300 = Color(0xFFB6C4C0);
  static const Color ink200 = Color(0xFFD9E2DF);
  static const Color ink100 = Color(0xFFEAF0EE);
  static const Color ink50 = Color(0xFFF5F8F7);

  // ── Dark palette ─────────────────────────────────────────────────────────────
  static const Color dark900 = Color(0xFF0A0E1A);
  static const Color dark800 = Color(0xFF0F1629);
  static const Color dark700 = Color(0xFF1A2540);
  static const Color dark600 = Color(0xFF243050);
  static const Color dark500 = Color(0xFF3D4F70);
  static const Color dark400 = Color(0xFF6B80A8);
  static const Color dark300 = Color(0xFF9BAAC8);
  static const Color dark200 = Color(0xFFCDD6E8);
  static const Color dark100 = Color(0xFFE8ECF5);

  // ── Surface ──────────────────────────────────────────────────────────────────
  static const Color paper = Color(0xFFFBFCFB);
  static const Color cardBg = Color(0xFFFFFFFF);

  // ── Dark surface ─────────────────────────────────────────────────────────────
  static const Color darkPaper = Color(0xFF0A0E1A);
  static const Color darkCard = Color(0xFF0F1629);
  static const Color darkCardElevated = Color(0xFF1A2540);

  // ── Status ───────────────────────────────────────────────────────────────────
  static const Color warnBg = Color(0xFFFDF4E6);
  static const Color warnFg = Color(0xFF7A5522);
  static const Color dangerBg = Color(0xFFFBECE9);
  static const Color dangerFg = Color(0xFF8A2F22);
  static const Color goodBg = Color(0xFFE7F6EF);
  static const Color goodFg = Color(0xFF0B6E57);

  // ── Semantic aliases ─────────────────────────────────────────────────────────
  static const Color primaryTeal = teal500;
  static const Color primaryLight = teal50;
  static const Color primaryDark = teal700;
  static const Color accentAmber = Color(0xFFF59E0B);
  static const Color accentAmberLight = Color(0xFFFEF3C7);
  static const Color successEmerald = goodFg;
  static const Color dangerRed = Color(0xFFEF4444);
  static const Color warningOrange = Color(0xFFF97316);
  static const Color hyperRed = Color(0xFFB91C1C);
  static const Color surfaceWhite = cardBg;
  static const Color surfaceMuted = ink50;
  static const Color surfaceDark = Color(0xFF0F172A);
  static const Color surfaceDarkCard = Color(0xFF1E293B);
  static const Color textDark = ink900;
  static const Color textMuted = ink500;
  static const Color textLight = ink300;
  static const Color borderLight = ink100;

  // ── Radius tokens ─────────────────────────────────────────────────────────────
  static const double radiusSm = 10.0;
  static const double radiusXL = 14.0;
  static const double radius2XL = 20.0;
  static const double radius3XL = 24.0;

  // ── Shadows light ────────────────────────────────────────────────────────────
  static const List<BoxShadow> shadowClinical = [
    BoxShadow(color: Color(0x0A0D1A17), blurRadius: 2, offset: Offset(0, 1)),
    BoxShadow(color: Color(0x080D1A17), blurRadius: 1, offset: Offset(0, 1)),
  ];
  static const List<BoxShadow> shadowClinicalLg = [
    BoxShadow(color: Color(0x0D0D1A17), blurRadius: 8, offset: Offset(0, 2)),
    BoxShadow(color: Color(0x0A0D1A17), blurRadius: 24, offset: Offset(0, 8)),
  ];

  // ── Hero shadow — teal glow ───────────────────────────────────────────────────
  static List<BoxShadow> get shadowHero => [
    BoxShadow(
      color: const Color(0xFF0B6E57).withValues(alpha: 0.45),
      blurRadius: 60,
      spreadRadius: -20,
      offset: const Offset(0, 24),
    ),
    BoxShadow(
      color: const Color(0xFF0B6E57).withValues(alpha: 0.25),
      blurRadius: 24,
      spreadRadius: -8,
      offset: const Offset(0, 8),
    ),
  ];

  // ── FAB shadow ────────────────────────────────────────────────────────────────
  static List<BoxShadow> get shadowFab => [
    BoxShadow(
      color: teal600.withValues(alpha: 0.45),
      blurRadius: 20,
      spreadRadius: -4,
      offset: const Offset(0, 8),
    ),
    BoxShadow(
      color: teal900.withValues(alpha: 0.20),
      blurRadius: 40,
      spreadRadius: -8,
      offset: const Offset(0, 16),
    ),
  ];

  // ── Shadows dark ─────────────────────────────────────────────────────────────
  static const List<BoxShadow> shadowDark = [
    BoxShadow(color: Color(0x33000000), blurRadius: 8, offset: Offset(0, 2)),
    BoxShadow(color: Color(0x22000000), blurRadius: 24, offset: Offset(0, 8)),
  ];

  // ── Legacy shadows ────────────────────────────────────────────────────────────
  static List<BoxShadow> shadowCard = [
    BoxShadow(
      color: Colors.black.withValues(alpha: 0.06),
      blurRadius: 12,
      offset: const Offset(0, 2),
    ),
  ];
  static List<BoxShadow> shadowCardLG = [
    BoxShadow(
      color: Colors.black.withValues(alpha: 0.10),
      blurRadius: 30,
      offset: const Offset(0, 8),
    ),
  ];
  static List<BoxShadow> shadowPrimary = [
    BoxShadow(
      color: teal500.withValues(alpha: 0.35),
      blurRadius: 14,
      offset: const Offset(0, 4),
    ),
  ];
  static List<BoxShadow> shadowGlass(bool isDark) => [
    BoxShadow(
      color: (isDark ? Colors.black : const Color(0xFF1F2687)).withValues(
        alpha: isDark ? 0.4 : 0.07,
      ),
      blurRadius: 32,
      offset: const Offset(0, 8),
    ),
  ];

  // ── Gradients ─────────────────────────────────────────────────────────────────

  /// Gradient actuel (léger) — conservé pour compatibilité
  static const primaryGradient = LinearGradient(
    colors: [teal700, teal400],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  /// Hero gradient profond — RadialGradient sur mobile, LinearGradient sur web.
  /// Flutter Web rasterise RadialGradient en cercles concentriques sur Chrome —
  /// le LinearGradient est visuellement identique et rend correctement partout.
  static const heroGradientDeep = RadialGradient(
    center: Alignment.topLeft,
    radius: 1.4,
    colors: [
      Color(0xFF14A984),
      Color(0xFF0E8C6E),
      Color(0xFF0B6E57),
      Color(0xFF073B30),
    ],
    stops: [0.0, 0.35, 0.65, 1.0],
  );

  static Gradient get heroGradient => kIsWeb
      ? const LinearGradient(
          colors: [Color(0xFF14A984), Color(0xFF0E8C6E), Color(0xFF0B6E57)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        )
      : heroGradientDeep;

  /// Décoration hero complète avec overlay lumineux radial
  static BoxDecoration heroCardDecoration({BorderRadius? borderRadius}) {
    return BoxDecoration(
      gradient: heroGradient,
      borderRadius: borderRadius ?? BorderRadius.circular(radius3XL),
      boxShadow: shadowHero,
    );
  }

  static const oceanGradient = LinearGradient(
    colors: [ocean700, ocean400],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );
  static const ambreGradient = LinearGradient(
    colors: [ambre700, ambre400],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );
  static const accentGradient = LinearGradient(
    colors: [Color(0xFFF59E0B), Color(0xFFF97316)],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  /// Gradient FAB Ajouter
  static const fabGradient = LinearGradient(
    colors: [teal500, teal700],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  // ── Hero card (legacy) ───────────────────────────────────────────────────────
  static const BoxDecoration heroCard = BoxDecoration(
    gradient: LinearGradient(
      colors: [teal600, teal500, teal400],
      begin: Alignment.topLeft,
      end: Alignment.bottomRight,
    ),
    borderRadius: BorderRadius.all(Radius.circular(radius2XL)),
  );

  // ── Clinical card (light) ────────────────────────────────────────────────────
  static BoxDecoration clinicalCard({double? borderRadius, Border? border}) {
    return BoxDecoration(
      color: cardBg,
      borderRadius: BorderRadius.circular(borderRadius ?? radius2XL),
      border: border ?? Border.all(color: ink100),
      boxShadow: shadowClinical,
    );
  }

  // ── Clinical card (dark) ──────────────────────────────────────────────────────
  static BoxDecoration clinicalCardDark({double? borderRadius}) {
    return BoxDecoration(
      color: darkCard,
      borderRadius: BorderRadius.circular(borderRadius ?? radius2XL),
      border: Border.all(color: dark600.withValues(alpha: 0.5)),
      boxShadow: shadowDark,
    );
  }

  // ── Glassmorphism ─────────────────────────────────────────────────────────────
  static BoxDecoration glassDecoration({
    required bool isDark,
    double opacity = 0.75,
    double? borderRadius,
  }) {
    return BoxDecoration(
      color: (isDark ? const Color(0xFF1E293B) : Colors.white).withValues(
        alpha: opacity,
      ),
      borderRadius: BorderRadius.circular(borderRadius ?? radius2XL),
      border: Border.all(
        color: (isDark ? const Color(0xFF38BDF8) : Colors.white).withValues(
          alpha: isDark ? 0.15 : 0.3,
        ),
      ),
      boxShadow: shadowGlass(isDark),
    );
  }

  // ─────────────────────────────────────────────────────────────────────────────
  // Dark-mode context helpers
  // Usage: AminaTheme.surface(context), AminaTheme.bg(context), etc.
  // ─────────────────────────────────────────────────────────────────────────────

  static bool isDark(BuildContext context) =>
      Theme.of(context).brightness == Brightness.dark;

  /// Card surface: white en clair, darkCard en sombre
  static Color surface(BuildContext context) =>
      isDark(context) ? darkCard : cardBg;

  /// Page background
  static Color bg(BuildContext context) => isDark(context) ? darkPaper : paper;

  /// Elevated card (légèrement plus clair que surface en dark)
  static Color surfaceElevated(BuildContext context) =>
      isDark(context) ? darkCardElevated : cardBg;

  /// Divider / border color
  static Color divider(BuildContext context) =>
      isDark(context) ? dark600.withValues(alpha: 0.45) : ink100;

  /// Primary text
  static Color textPrimary(BuildContext context) =>
      isDark(context) ? dark100 : ink900;

  /// Secondary text
  static Color textSecondary(BuildContext context) =>
      isDark(context) ? dark300 : ink500;

  /// Subtle background (input fields, chips)
  static Color subtleBg(BuildContext context) =>
      isDark(context) ? dark700 : ink50;

  /// Teal accent adapté (plus vif en dark)
  static Color accent(BuildContext context) =>
      isDark(context) ? teal400 : teal500;

  /// Hero overlay color (radial light spot)
  static Color heroOverlay(BuildContext context) => isDark(context)
      ? Colors.white.withValues(alpha: 0.06)
      : Colors.white.withValues(alpha: 0.16);

  // ─────────────────────────────────────────────────────────────────────────────
  // ThemeData — Light
  // ─────────────────────────────────────────────────────────────────────────────

  static ThemeData get light {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.light,
      fontFamily: 'Inter',
      primaryColor: teal500,
      colorScheme: ColorScheme.fromSeed(
        seedColor: teal500,
        primary: teal500,
        secondary: accentAmber,
        surface: paper,
        error: dangerRed,
      ),
      scaffoldBackgroundColor: paper,
      appBarTheme: const AppBarTheme(
        backgroundColor: Colors.transparent,
        elevation: 0,
        centerTitle: false,
        iconTheme: IconThemeData(color: ink700),
        titleTextStyle: TextStyle(
          color: ink900,
          fontSize: 18,
          fontWeight: FontWeight.w600,
          fontFamily: 'Inter',
        ),
      ),
      textTheme: const TextTheme(
        displayLarge: TextStyle(
          fontFamily: 'Inter Tight',
          color: ink900,
          fontWeight: FontWeight.w700,
          fontSize: 32,
          letterSpacing: -0.5,
          fontFeatures: [FontFeature.tabularFigures()],
        ),
        displayMedium: TextStyle(
          fontFamily: 'Inter Tight',
          color: ink900,
          fontWeight: FontWeight.w700,
          fontSize: 28,
          letterSpacing: -0.4,
          fontFeatures: [FontFeature.tabularFigures()],
        ),
        titleLarge: TextStyle(
          color: ink900,
          fontWeight: FontWeight.w600,
          fontSize: 18,
        ),
        titleMedium: TextStyle(
          color: ink800,
          fontWeight: FontWeight.w600,
          fontSize: 15,
        ),
        bodyLarge: TextStyle(color: ink700, fontSize: 14),
        bodyMedium: TextStyle(color: ink700, fontSize: 13),
        bodySmall: TextStyle(color: ink500, fontSize: 12),
        labelSmall: TextStyle(
          color: ink500,
          fontSize: 11,
          fontWeight: FontWeight.w600,
          letterSpacing: 0.08,
        ),
      ),
      cardTheme: CardThemeData(
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(radius2XL),
          side: const BorderSide(color: ink100),
        ),
        color: cardBg,
      ),
      dividerTheme: const DividerThemeData(
        color: ink100,
        space: 1,
        thickness: 1,
      ),
      navigationBarTheme: NavigationBarThemeData(
        backgroundColor: cardBg,
        indicatorColor: teal50,
        labelTextStyle: WidgetStateProperty.all(
          const TextStyle(
            fontSize: 11,
            fontWeight: FontWeight.w600,
            color: ink700,
            fontFamily: 'Inter',
          ),
        ),
        iconTheme: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.selected))
            return const IconThemeData(color: teal600, size: 22);
          return const IconThemeData(color: ink400, size: 22);
        }),
      ),
      sliderTheme: SliderThemeData(
        activeTrackColor: teal500,
        inactiveTrackColor: teal100,
        thumbColor: teal600,
        overlayColor: teal500.withValues(alpha: 0.12),
        trackHeight: 6,
        thumbShape: const RoundSliderThumbShape(enabledThumbRadius: 10),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: teal500,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(99),
          ),
          textStyle: const TextStyle(
            fontWeight: FontWeight.w600,
            fontFamily: 'Inter',
          ),
        ),
      ),
    );
  }

  // ─────────────────────────────────────────────────────────────────────────────
  // ThemeData — Dark
  // ─────────────────────────────────────────────────────────────────────────────

  static ThemeData get dark {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      fontFamily: 'Inter',
      primaryColor: teal500,
      colorScheme: ColorScheme.fromSeed(
        seedColor: teal500,
        brightness: Brightness.dark,
        primary: teal400,
        secondary: ambre400,
        surface: darkCard,
        error: dangerRed,
      ),
      scaffoldBackgroundColor: darkPaper,
      appBarTheme: const AppBarTheme(
        backgroundColor: Colors.transparent,
        elevation: 0,
        centerTitle: false,
        iconTheme: IconThemeData(color: dark200),
        titleTextStyle: TextStyle(
          color: dark100,
          fontSize: 18,
          fontWeight: FontWeight.w600,
          fontFamily: 'Inter',
        ),
      ),
      textTheme: const TextTheme(
        displayLarge: TextStyle(
          fontFamily: 'Inter Tight',
          color: dark100,
          fontWeight: FontWeight.w700,
          fontSize: 32,
          letterSpacing: -0.5,
          fontFeatures: [FontFeature.tabularFigures()],
        ),
        displayMedium: TextStyle(
          fontFamily: 'Inter Tight',
          color: dark100,
          fontWeight: FontWeight.w700,
          fontSize: 28,
          letterSpacing: -0.4,
          fontFeatures: [FontFeature.tabularFigures()],
        ),
        titleLarge: TextStyle(
          color: dark100,
          fontWeight: FontWeight.w600,
          fontSize: 18,
        ),
        titleMedium: TextStyle(
          color: dark200,
          fontWeight: FontWeight.w600,
          fontSize: 15,
        ),
        bodyLarge: TextStyle(color: dark300, fontSize: 14),
        bodyMedium: TextStyle(color: dark300, fontSize: 13),
        bodySmall: TextStyle(color: dark400, fontSize: 12),
        labelSmall: TextStyle(
          color: dark400,
          fontSize: 11,
          fontWeight: FontWeight.w600,
          letterSpacing: 0.08,
        ),
      ),
      cardTheme: CardThemeData(
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(radius2XL),
          side: BorderSide(color: dark600.withValues(alpha: 0.5)),
        ),
        color: darkCard,
      ),
      dividerTheme: DividerThemeData(
        color: dark600.withValues(alpha: 0.4),
        space: 1,
        thickness: 1,
      ),
      navigationBarTheme: NavigationBarThemeData(
        backgroundColor: darkCard,
        indicatorColor: teal700.withValues(alpha: 0.3),
        labelTextStyle: WidgetStateProperty.all(
          const TextStyle(
            fontSize: 11,
            fontWeight: FontWeight.w600,
            color: dark200,
            fontFamily: 'Inter',
          ),
        ),
        iconTheme: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.selected))
            return const IconThemeData(color: teal400, size: 22);
          return const IconThemeData(color: dark400, size: 22);
        }),
      ),
      sliderTheme: SliderThemeData(
        activeTrackColor: teal400,
        inactiveTrackColor: dark600,
        thumbColor: teal400,
        overlayColor: teal400.withValues(alpha: 0.12),
        trackHeight: 6,
        thumbShape: const RoundSliderThumbShape(enabledThumbRadius: 10),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: teal500,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(99),
          ),
          textStyle: const TextStyle(
            fontWeight: FontWeight.w600,
            fontFamily: 'Inter',
          ),
        ),
      ),
    );
  }
}
