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
    ("padding: const EdgeInsetsDirectional.fromSTEB(18, 12, 18, 108),", "padding: const EdgeInsetsDirectional.fromSTEB(18, 10, 18, 100),", 'dashboard outer padding'),
    ("const SizedBox(height: 22),\n                  Row(", "const SizedBox(height: 18),\n                  Row(", 'brand greeting gap'),
    ("fontSize: 28,\n                                height: 1.05,", "fontSize: 27,\n                                height: 1.05,", 'greeting size'),
    ("fontSize: 14,\n                                color: AminaTheme.textSecondary(context),", "fontSize: 13,\n                                color: AminaTheme.textSecondary(context),", 'greeting subtitle size'),
    ("const SizedBox(height: 15),\n                  _GlucoseHero(", "const SizedBox(height: 12),\n                  _GlucoseHero(", 'greeting hero gap'),
    ("const SizedBox(height: 14),\n                  _TrendsPanel(", "const SizedBox(height: 11),\n                  _TrendsPanel(", 'hero trends gap'),
    ("const SizedBox(height: 18),\n                  Text(", "const SizedBox(height: 14),\n                  Text(", 'trends actions gap'),
    ("fontSize: 16,\n                      fontWeight: FontWeight.w800,", "fontSize: 15.5,\n                      fontWeight: FontWeight.w800,", 'quick actions title size'),
    ("const SizedBox(height: 10),\n                  const _QuickActionsRow(),", "const SizedBox(height: 8),\n                  const _QuickActionsRow(),", 'actions title gap'),
    ("height: 42,", "height: 40,", 'range pill height'),
    ("padding: const EdgeInsetsDirectional.fromSTEB(14, 0, 11, 0),", "padding: const EdgeInsetsDirectional.fromSTEB(12, 0, 10, 0),", 'range pill padding'),
    ("padding: const EdgeInsets.fromLTRB(18, 18, 18, 14),", "padding: const EdgeInsets.fromLTRB(16, 14, 16, 12),", 'hero padding'),
    ("width: 40,\n                height: 40,", "width: 36,\n                height: 36,", 'hero icon size'),
    ("fontSize: 14.5,\n                        fontWeight: FontWeight.w800,", "fontSize: 13.5,\n                        fontWeight: FontWeight.w800,", 'hero title size'),
    ("fontSize: 11.5,", "fontSize: 11,", 'hero subtitle size'),
    ("const SizedBox(height: 14),\n          Row(", "const SizedBox(height: 10),\n          Row(", 'hero body gap'),
    ("fontSize: 50,", "fontSize: 47,", 'hero number size'),
    ("height: 108,", "height: 92,", 'hero chart height'),
    ("padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),", "padding: const EdgeInsets.symmetric(horizontal: 13, vertical: 10),", 'hero observation padding'),
    ("padding: const EdgeInsets.fromLTRB(16, 14, 16, 14),", "padding: const EdgeInsets.fromLTRB(15, 11, 15, 11),", 'trends padding'),
    ("width: 36,\n            height: 36,", "width: 32,\n            height: 32,", 'metric icon size'),
    ("fontSize: 24,", "fontSize: 22,", 'metric value size'),
    ("const SizedBox(height: 12),\n          InkWell(", "const SizedBox(height: 9),\n          InkWell(", 'trends observation gap'),
    ("padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),", "padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 11),", 'trends observation padding'),
    ("width: 40,\n                    height: 40,", "width: 36,\n                    height: 36,", 'trends observation icon size'),
    ("width: 58,\n                    height: 58,", "width: 54,\n                    height: 54,", 'quick action icon size'),
    ("fontSize: 10,", "fontSize: 9.4,", 'quick action label size'),
]:
    s = replace_once(s, old, new, label)

dash_path.write_text(s)

nav_path = FRONTEND / 'lib/features/navigation/main_shell.dart'
s = nav_path.read_text()
for old, new, label in [
    ("height: 82,", "height: 76,", 'nav overall height'),
    ("top: 14,", "top: 12,", 'nav bar top'),
    ("width: 54,", "width: 52,", 'add width'),
    ("height: 54,", "height: 52,", 'add height'),
    ("size: 30,", "size: 29,", 'add icon'),
    ("fontSize: 9.6,", "fontSize: 9.2,", 'nav label size'),
]:
    s = replace_once(s, old, new, label)
nav_path.write_text(s)
