#!/usr/bin/env python3
"""Correct the compact Profile prompt shape, then run the clean migration."""

from pathlib import Path
import runpy

root = Path(__file__).resolve().parents[1]
script = root / 'scripts/apply_clean_audited_page_localization.py'
source = script.read_text(encoding='utf-8')
old = """s = once(s, \"            const Text(\\n              'Complétez votre profil pour des analyses plus précises.',\\n              style: TextStyle(\", '            Text(\\n              copy.profileCompletionPrompt,\\n              style: const TextStyle(', 'profile prompt')
"""
new = """s = once(
    s,
    \"          const Text(\\n            'Complétez votre profil pour des analyses plus précises.',\\n            style: TextStyle(fontSize: 11, color: AminaTheme.ink500, height: 1.4),\\n          ),\",
    \"          Text(\\n            copy.profileCompletionPrompt,\\n            style: const TextStyle(fontSize: 11, color: AminaTheme.ink500, height: 1.4),\\n          ),\",
    'profile prompt',
)
"""
if source.count(old) != 1:
    raise SystemExit(f'profile prompt migration block changed: {source.count(old)}')
script.write_text(source.replace(old, new, 1), encoding='utf-8')
runpy.run_path(str(script), run_name='__main__')
