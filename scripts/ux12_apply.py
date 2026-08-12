from pathlib import Path


def replace(path: str, old: str, new: str, label: str) -> None:
    p = Path(path)
    text = p.read_text()
    if old not in text:
        raise SystemExit(f"missing {label} in {path}")
    p.write_text(text.replace(old, new, 1))


theme = "frontend/lib/core/theme/app_theme.dart"
replace(theme, "static const Color teal700 = Color(0xFF0B6E57);", "static const Color teal700 = Color(0xFF064E52);", "deep teal")
replace(theme, "static const Color ink100 = Color(0xFFEAF0EE);", "static const Color ink100 = Color(0xFFE8E3DB);", "warm border")
replace(theme, "static const Color ink50  = Color(0xFFF5F8F7);", "static const Color ink50  = Color(0xFFF3F0EA);", "warm subtle")
replace(theme, "static const Color paper  = Color(0xFFFBFCFB);", "static const Color paper  = Color(0xFFF8F5EF);", "warm paper")
replace(theme, "static const double radius2XL = 20.0;", "static const double radius2XL = 22.0;", "dashboard radius")

p = Path(theme)
text = p.read_text()
old_light_button = """      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: teal500,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(99)),
          textStyle: const TextStyle(fontWeight: FontWeight.w600, fontFamily: 'Inter'),
        ),
      ),"""
new_light_button = """      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: teal700,
          foregroundColor: Colors.white,
          minimumSize: const Size(0, 48),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          textStyle: const TextStyle(fontWeight: FontWeight.w700, fontFamily: 'Inter'),
        ),
      ),"""
if old_light_button not in text:
    raise SystemExit("missing light filled button")
text = text.replace(old_light_button, new_light_button, 1)

old_dark_button = """      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: teal500,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(99)),
          textStyle: const TextStyle(fontWeight: FontWeight.w600, fontFamily: 'Inter'),
        ),
      ),"""
new_dark_button = """      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: teal500,
          foregroundColor: Colors.white,
          minimumSize: const Size(0, 48),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          textStyle: const TextStyle(fontWeight: FontWeight.w700, fontFamily: 'Inter'),
        ),
      ),"""
if old_dark_button not in text:
    raise SystemExit("missing dark filled button")
text = text.replace(old_dark_button, new_dark_button, 1)
p.write_text(text)

replace(
    "frontend/lib/features/journal/journal_screen.dart",
    ": viewportWidth >= 700\n        ? 28.0\n        : 20.0;",
    ": viewportWidth >= 700\n        ? 28.0\n        : 18.0;",
    "journal mobile gutter",
)
replace(
    "frontend/lib/features/profile/profile_screen.dart",
    "padding: const EdgeInsetsDirectional.fromSTEB(24, 20, 24, 40),",
    "padding: EdgeInsetsDirectional.fromSTEB(isMobile ? 18 : 24, isMobile ? 6 : 20, isMobile ? 18 : 24, isMobile ? 112 : 40),",
    "profile mobile spacing",
)
replace(
    "frontend/lib/features/import/import_screen.dart",
    "backgroundColor: AminaTheme.paper,",
    "backgroundColor: AminaTheme.bg(context),",
    "import background",
)
replace(
    "frontend/lib/features/import/import_screen.dart",
    "padding: const EdgeInsets.all(16),",
    "padding: const EdgeInsetsDirectional.fromSTEB(18, 6, 18, 112),",
    "import mobile rhythm",
)
replace(
    "frontend/lib/features/dashboard/widgets/add_log_sheet.dart",
    "padding: const EdgeInsets.fromLTRB(20, 8, 20, 112),",
    "padding: const EdgeInsetsDirectional.fromSTEB(18, 10, 18, 112),",
    "add-log mobile gutter",
)
replace(
    "frontend/lib/features/dashboard/widgets/add_log_sheet.dart",
    """fontSize: 24,\n                fontWeight: FontWeight.w800,""",
    """fontSize: 26,\n                height: 1.05,\n                fontWeight: FontWeight.w800,\n                letterSpacing: -0.8,""",
    "add-log heading",
)
replace(
    "frontend/lib/features/dashboard/widgets/add_log_sheet.dart",
    "color: isLow ? const Color(0xFFFFF7ED) : AminaTheme.subtleBg(context),\n          borderRadius: BorderRadius.circular(22),",
    "color: isLow ? const Color(0xFFFFF7ED) : AminaTheme.surface(context),\n          borderRadius: BorderRadius.circular(22),",
    "add-log glucose surface",
)
