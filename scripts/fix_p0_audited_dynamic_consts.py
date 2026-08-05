#!/usr/bin/env python3
"""Remove const only where localized runtime labels make it invalid."""

from pathlib import Path

root = Path(__file__).resolve().parents[1]
path = root / 'frontend/lib/features/import/import_screen.dart'
source = path.read_text(encoding='utf-8')
old = '''                    const Wrap(
                      spacing: 6,
                      children: [
                        _PulperChip(label: AuditedPageCopy.of(context).labReport),'''
new = '''                    Wrap(
                      spacing: 6,
                      children: [
                        _PulperChip(label: AuditedPageCopy.of(context).labReport),'''
if source.count(old) != 1:
    raise SystemExit(f'localized Pulper const shape changed: {source.count(old)}')
path.write_text(source.replace(old, new, 1), encoding='utf-8')
print('Localized Pulper chips made runtime-safe.')
