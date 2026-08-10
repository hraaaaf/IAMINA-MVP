from pathlib import Path

path = Path('docs/ROADMAP.md')
text = path.read_text()

replacements = {
    '> **Last updated:** 2026-08-10 — UX visual rebase is closed: UX-2 fixed the freshly observed Summary load-error desktop composition from 8.1/10 to 9.3/10 with exact-head and post-merge certification.':
    '> **Last updated:** 2026-08-10 — UX visual rebase remains closed: UX-3 unified the wide-shell brand from a cross-product 8.7/10 inconsistency to a canonical IAmina signature at 9.4/10 with exact-head and post-merge certification.',
    '| UX visual rebase | 100% | ✅ Closed | UX-0/1 remain closed; UX-2 PR #86 fixed the fresh Summary error-state finding **8.1/10 → 9.3/10**; post-merge CI #1464 + drift #1276 green |':
    '| UX visual rebase | 100% | ✅ Closed | UX-0/1/2 remain closed; UX-3 PR #89 unified the desktop shell brand **8.7/10 → 9.4/10**; post-merge CI #1472 + drift #1284 green |',
    '| UX-2 | Summary load-error desktop composition | 100% | PR #86 merged as `7a7e3be0553d44d1879b0f898ad4d7682838521e`; exact final head `92a0378c746eba2232b3ca0b4c2efbf2e566955f`, CI #1463 + drift #1275 + final visual run `31415470505`, UX **9.3/10**; post-merge CI #1464 + drift #1276 green | ✅ Closed |':
    '| UX-2 | Summary load-error desktop composition | 100% | PR #86 merged as `7a7e3be0553d44d1879b0f898ad4d7682838521e`; exact final head `92a0378c746eba2232b3ca0b4c2efbf2e566955f`, CI #1463 + drift #1275 + final visual run `31415470505`, UX **9.3/10**; post-merge CI #1464 + drift #1276 green | ✅ Closed |\n| UX-3 | Canonical IAmina shell brand signature | 100% | PR #89 merged as `03eeefffe81d841e026a62df787705190cd96f46`; exact final head `896f4134e5bc9c26ae0f4ffa43b6d4c5779be73e`, CI #1471 + drift #1283 + final visual run `31418109204`, Product Design **9.4/10**; post-merge CI #1472 + drift #1284 green | ✅ Closed |',
    'UX-1 was intentionally narrower than the historical UX plan. A fresh exact-main audit later found one new <=9.0 state: Summary load-error desktop composition. UX-2 is limited to that evidence; Dashboard, Journal, Profile, Importer and post-save surfaces stay protected by their existing rendered certifications.':
    'UX-1 was intentionally narrower than the historical UX plan. A fresh exact-main audit later found one new <=9.0 state: Summary load-error desktop composition, closed by UX-2. A later exact-main cross-product audit found a separate shell-brand inconsistency at 8.7/10 while individual feature screens stayed >=9; UX-3 is limited to canonical brand presentation and does not reopen the certified clinical feature surfaces.',
}

for old, new in replacements.items():
    if old not in text:
        raise SystemExit(f'missing ROADMAP anchor: {old[:80]}')
    text = text.replace(old, new, 1)

anchor = '- Exact final head `92a0378c746eba2232b3ca0b4c2efbf2e566955f` passed CI #1463 and migration drift #1275. Final exact-head visual run `31415470505`, artifact `9073307734`, digest `sha256:2bc8c9a7887e8fd6ebefd6e238f19f3087e7e6da1ce8ff517cfdd46105319a36` rendered 8/8 FR/AR Summary views with one Flutter view each and zero page errors. UX Auditor FINAL PASS **9.3/10** and Release Certifier CERTIFIED. PR #86 merged with expected-head locking as `7a7e3be0553d44d1879b0f898ad4d7682838521e`; post-merge CI #1464 and drift #1276 passed. **UX-2 is 100% closed.**'
insert = '''\n\n### UX-3 closeout evidence\n\n- Fresh exact-main signature audit source `c681a3bb926aec2f6df1a865266f4240904712ad`: run `31416933901`, artifact `9073879563`, digest `sha256:b4779628e0afac327cbb586bf078fe3ac328fc61130ce461488896cb0980a26d`; 20/20 FR/AR desktop/mobile renders, one Flutter view each and zero page errors. Individual feature screens remained >=9, but the cross-product shell identity scored **8.7/10** because wide desktop exposed `Diabetes Log / IA · AMINA` while navigation/mobile exposed `IAmina`.\n- UX-3 changes shell presentation only: `_BrandHeader` reuses the already-localized canonical `appTitle` + `appSubtitle` keys (`IAmina / Compagnon Diabète`, `IAmina / Diabetes Companion`, `IAmina / رفيق داء السكري`). No new copy, clinical semantics, feature layout, persistence, API, auth, consent or egress behavior was introduced. A permanent Flutter source contract prevents the wide shell from returning to `brandName/brandTagShort`.\n- Exact final product head `896f4134e5bc9c26ae0f4ffa43b6d4c5779be73e` passed CI #1471 and migration drift #1283. Final visual run `31418109204`, artifact `9074309323`, digest `sha256:8d96b6e319adb911274cf498d52b3472dc3f4f1535b5c8b88056872b6d011bae` rendered 14/14 FR/AR views across all five desktop shell destinations plus Dashboard/Profile mobile, one Flutter view each and zero page errors. Product Design FINAL PASS **9.4/10**, UX Reviewer FINAL PASS and Release Certifier GO. PR #89 merged with expected-head locking as `03eeefffe81d841e026a62df787705190cd96f46`; post-merge CI #1472 and drift #1284 passed. **UX-3 is 100% closed.**'''

if insert.strip() in text:
    raise SystemExit('UX-3 closeout already present')
if anchor not in text:
    raise SystemExit('UX-2 closeout anchor missing')
text = text.replace(anchor, anchor + insert, 1)

path.write_text(text)
