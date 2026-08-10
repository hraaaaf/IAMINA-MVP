from pathlib import Path

path = Path('docs/ROADMAP.md')
text = path.read_text()

replacements = {
    '> **Last updated:** 2026-08-10 — fresh exact-main UX evidence reopened one narrow surface: UX-2 rebalances the Summary load-error desktop state from 8.1/10 to 9.3/10 and is in final exact-head certification before merge.':
    '> **Last updated:** 2026-08-10 — UX visual rebase is closed: UX-2 fixed the freshly observed Summary load-error desktop composition from 8.1/10 to 9.3/10 with exact-head and post-merge certification.',
    '| UX visual rebase | 95% | 🟡 UX-2 final certification | UX-0/1 remain closed; fresh exact-main density audit opened only Summary error-state desktop; baseline **8.1/10** → remediated **9.3/10** on PR #86 |':
    '| UX visual rebase | 100% | ✅ Closed | UX-0/1 remain closed; UX-2 PR #86 fixed the fresh Summary error-state finding **8.1/10 → 9.3/10**; post-merge CI #1464 + drift #1276 green |',
    '# UX visual rebase — ACTIVE':
    '# UX visual rebase — CLOSED',
    '| UX-2 | Summary load-error desktop composition | 90% | Fresh exact-main baseline run `31413385769` isolated Summary desktop at **8.1/10** while Profile/Importer stayed >=9; product head `97df55865a13916c9bdf7f01796a60ba2d827ee2` remediated to **9.3/10**, CI #1458 + drift #1270 + visual run `31414604776` green; final docs-head recertification, Certifier, merge and post-merge gates pending | 🟡 |':
    '| UX-2 | Summary load-error desktop composition | 100% | PR #86 merged as `7a7e3be0553d44d1879b0f898ad4d7682838521e`; exact final head `92a0378c746eba2232b3ca0b4c2efbf2e566955f`, CI #1463 + drift #1275 + final visual run `31415470505`, UX **9.3/10**; post-merge CI #1464 + drift #1276 green | ✅ Closed |',
    '- UX-2 remains open until the final documentation head is revalidated, Release Certifier authorizes expected-head merge, PR #86 merges and post-merge CI/drift pass.':
    '- Exact final head `92a0378c746eba2232b3ca0b4c2efbf2e566955f` passed CI #1463 and migration drift #1275. Final exact-head visual run `31415470505`, artifact `9073307734`, digest `sha256:2bc8c9a7887e8fd6ebefd6e238f19f3087e7e6da1ce8ff517cfdd46105319a36` rendered 8/8 FR/AR Summary views with one Flutter view each and zero page errors. UX Auditor FINAL PASS **9.3/10** and Release Certifier CERTIFIED. PR #86 merged with expected-head locking as `7a7e3be0553d44d1879b0f898ad4d7682838521e`; post-merge CI #1464 and drift #1276 passed. **UX-2 is 100% closed.**',
}

for old, new in replacements.items():
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'expected exactly one match, got {count}: {old[:100]}')
    text = text.replace(old, new, 1)

path.write_text(text)
