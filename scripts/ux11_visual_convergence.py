from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DASH = ROOT / 'frontend/lib/features/dashboard/dashboard_convergent_screen.dart'


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f'missing {label}: {old!r}')
    return text.replace(old, new, 1)


s = DASH.read_text()

# Width-normalized mockup comparison shows the action row is ~65 px too high.
# Restore that vertical rhythm inside the two information cards without adding
# fabricated data or claims.
for old, new, label in [
    ("padding: const EdgeInsets.fromLTRB(16, 10, 16, 10),", "padding: const EdgeInsets.fromLTRB(16, 14, 16, 12),", 'hero card padding'),
    ("width: 34,\n                height: 34,", "width: 36,\n                height: 36,", 'hero icon size'),
    ("const SizedBox(height: 6),\n          Row(", "const SizedBox(height: 10),\n          Row(", 'hero body gap'),
    ("height: 76,", "height: 92,", 'hero chart height'),
    ("const SizedBox(height: 10),\n          InkWell(", "const SizedBox(height: 12),\n          InkWell(", 'hero observation gap'),
    ("padding: const EdgeInsets.symmetric(horizontal: 13, vertical: 8),", "padding: const EdgeInsets.symmetric(horizontal: 13, vertical: 9),", 'hero observation padding'),
    ("padding: const EdgeInsets.fromLTRB(15, 8, 15, 8),", "padding: const EdgeInsets.fromLTRB(15, 12, 15, 12),", 'trends card padding'),
    ("width: 28,\n            height: 28,", "width: 34,\n            height: 34,", 'metric icon size'),
    ("const SizedBox(height: 5),", "const SizedBox(height: 7),", 'metric label gap'),
    ("fontSize: 21,\n                      fontWeight: FontWeight.w800,", "fontSize: 23,\n                      fontWeight: FontWeight.w800,", 'metric value size'),
    ("const SizedBox(height: 6),\n          InkWell(", "const SizedBox(height: 10),\n          InkWell(", 'trends observation gap'),
    ("padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),", "padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),", 'trends observation padding'),
    ("width: 32,\n                    height: 32,", "width: 38,\n                    height: 38,", 'trends observation icon size'),
]:
    s = replace_once(s, old, new, label)

DASH.write_text(s)
