#!/usr/bin/env python3
"""Patch the scoped migration's two identical connector badges, then execute it."""

from pathlib import Path
import runpy

root = Path(__file__).resolve().parents[1]
script = root / "scripts/apply_p0_audited_arabic_coverage.py"
source = script.read_text(encoding="utf-8")

old_first = '''s = replace_once(s, "                    badge: 'BIENTÔT',", "                    badge: AuditedPageCopy.of(context).soon,", "dexcom soon")\n'''
old_second = '''s = replace_once(s, "                    badge: 'BIENTÔT',", "                    badge: AuditedPageCopy.of(context).soon,", "libre soon")\n'''
replacement = '''badge_token = "                    badge: 'BIENTÔT',"\nif s.count(badge_token) != 2:\n    raise SystemExit(f"connector badges: expected exactly two occurrences, got {s.count(badge_token)}")\ns = s.replace(badge_token, "                    badge: AuditedPageCopy.of(context).soon,", 2)\n'''

if source.count(old_first) != 1 or source.count(old_second) != 1:
    raise SystemExit("connector badge migration shape changed")
source = source.replace(old_first, replacement, 1).replace(old_second, "", 1)
script.write_text(source, encoding="utf-8")
runpy.run_path(str(script), run_name="__main__")
