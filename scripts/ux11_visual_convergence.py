from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / 'frontend'


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f'missing {label}: {old!r}')
    return text.replace(old, new, 1)


dash_path = FRONTEND / 'lib/features/dashboard/dashboard_convergent_screen.dart'
s = dash_path.read_text()

for old, new, label in [
    ("padding: const EdgeInsetsDirectional.fromSTEB(18, 8, 18, 96),", "padding: const EdgeInsetsDirectional.fromSTEB(18, 12, 18, 108),", 'dashboard outer padding'),
    ("const SizedBox(height: 18),\n                  Row(", "const SizedBox(height: 22),\n                  Row(", 'brand greeting gap'),
    ("fontSize: 25,", "fontSize: 28,", 'greeting size'),
    ("fontSize: 12.5,\n                                color: AminaTheme.textSecondary(context),", "fontSize: 14,\n                                color: AminaTheme.textSecondary(context),", 'greeting subtitle size'),
    ("const SizedBox(height: 11),\n                  _GlucoseHero(", "const SizedBox(height: 15),\n                  _GlucoseHero(", 'greeting hero gap'),
    ("const SizedBox(height: 10),\n                  _TrendsPanel(", "const SizedBox(height: 14),\n                  _TrendsPanel(", 'hero trends gap'),
    ("const SizedBox(height: 14),\n                  Text(", "const SizedBox(height: 18),\n                  Text(", 'trends actions gap'),
    ("fontSize: 15,\n                      fontWeight: FontWeight.w800,", "fontSize: 16,\n                      fontWeight: FontWeight.w800,", 'quick actions title size'),
    ("const SizedBox(height: 7),\n                  const _QuickActionsRow(),", "const SizedBox(height: 10),\n                  const _QuickActionsRow(),", 'actions title gap'),
    ("width: 40,\n          height: 40,\n          child: CustomPaint(painter: _SealPainter()),", "width: 46,\n          height: 46,\n          child: CustomPaint(painter: _SealPainter()),", 'brand mark size'),
    ("fontSize: 24,", "fontSize: 28,", 'brand name size'),
    ("fontSize: 10.5,", "fontSize: 12,", 'brand tagline size'),
    ("height: 38,", "height: 42,", 'date/range pill height'),
    ("padding: const EdgeInsetsDirectional.fromSTEB(11, 0, 9, 0),", "padding: const EdgeInsetsDirectional.fromSTEB(14, 0, 11, 0),", 'date/range pill padding'),
    ("padding: const EdgeInsets.fromLTRB(16, 12, 16, 10),", "padding: const EdgeInsets.fromLTRB(18, 18, 18, 14),", 'hero padding'),
    ("width: 34,\n                height: 34,", "width: 40,\n                height: 40,", 'hero icon size'),
    ("fontSize: 12.5,\n                        fontWeight: FontWeight.w800,", "fontSize: 14.5,\n                        fontWeight: FontWeight.w800,", 'hero title size'),
    ("fontSize: 10.5,", "fontSize: 11.5,", 'hero subtitle size'),
    ("const SizedBox(height: 8),\n          Row(", "const SizedBox(height: 14),\n          Row(", 'hero body gap'),
    ("fontSize: 44,", "fontSize: 50,", 'hero number size'),
    ("height: 80,", "height: 108,", 'hero chart height'),
    ("padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),", "padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),", 'hero observation padding'),
    ("padding: const EdgeInsets.fromLTRB(14, 10, 14, 10),", "padding: const EdgeInsets.fromLTRB(16, 14, 16, 14),", 'trends padding'),
    ("width: 30,\n            height: 30,", "width: 36,\n            height: 36,", 'metric icon size'),
    ("fontSize: 20,", "fontSize: 24,", 'metric value size'),
    ("const SizedBox(height: 8),\n          InkWell(", "const SizedBox(height: 12),\n          InkWell(", 'trends observation gap'),
    ("padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),", "padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),", 'trends observation padding'),
    ("width: 34,\n                    height: 34,", "width: 40,\n                    height: 40,", 'trends observation icon size'),
    ("width: 46,\n                    height: 46,", "width: 58,\n                    height: 58,", 'quick action icon size'),
    ("fontSize: 8.5,", "fontSize: 10,", 'quick action label size'),
    ("icon: Icons.restaurant_outlined,", "icon: Icons.apple_rounded,", 'food icon'),
    ("icon: Icons.notifications_none_rounded,\n        label: _t(context, 'Rappels'", "icon: Icons.favorite_rounded,\n        label: _t(context, 'Rappels'", 'reminder icon'),
]:
    s = replace_once(s, old, new, label)

old_bell = """            child: SizedBox(
              width: 42,
              height: 42,
              child: Stack(
                clipBehavior: Clip.none,
                children: [
                  const Center(
                    child: Icon(
                      Icons.notifications_none_rounded,
                      size: 21,
                      color: Color(0xFF064E52),
                    ),
                  ),
                  PositionedDirectional(
                    top: 7,
                    end: 7,
                    child: Container(
                      width: 7,
                      height: 7,
                      decoration: const BoxDecoration(
                        color: Color(0xFF35C78A),
                        shape: BoxShape.circle,
                      ),
                    ),
                  ),
                ],
              ),
            ),"""
new_bell = """            child: const SizedBox(
              width: 46,
              height: 46,
              child: Center(
                child: Icon(
                  Icons.notifications_none_rounded,
                  size: 24,
                  color: Color(0xFF064E52),
                ),
              ),
            ),"""
s = replace_once(s, old_bell, new_bell, 'truthful reminder bell')
dash_path.write_text(s)

nav_path = FRONTEND / 'lib/features/navigation/main_shell.dart'
s = nav_path.read_text()
for old, new, label in [
    ("height: 72,", "height: 82,", 'nav overall height'),
    ("top: 12,", "top: 14,", 'nav bar top'),
    ("width: 48,", "width: 54,", 'add width'),
    ("height: 48,", "height: 54,", 'add height'),
    ("size: 28,", "size: 30,", 'add icon'),
    ("fontSize: 8.8,", "fontSize: 9.6,", 'nav label size'),
]:
    s = replace_once(s, old, new, label)
nav_path.write_text(s)
