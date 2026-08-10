from pathlib import Path

path = Path('docs/ROADMAP.md')
text = path.read_text()

text = text.replace(
    '> **Last updated:** 2026-08-10 — UX visual rebase is closed: UX-0 established the rendered baseline/constitution and UX-1 remediated the populated-Dashboard FR/AR rich-state defect to 9.2/10 with exact-head and post-merge certification.',
    '> **Last updated:** 2026-08-10 — fresh exact-main UX evidence reopened one narrow surface: UX-2 rebalances the Summary load-error desktop state from 8.1/10 to 9.3/10 and is in final exact-head certification before merge.',
)
text = text.replace(
    '| UX visual rebase | 100% | ✅ Closed | UX-0 PR #83 + UX-1 PR #84; populated Dashboard baseline 8.4/10 → final **9.2/10**; post-merge CI #1453 + drift #1265 green |',
    '| UX visual rebase | 95% | 🟡 UX-2 final certification | UX-0/1 remain closed; fresh exact-main density audit opened only Summary error-state desktop; baseline **8.1/10** → remediated **9.3/10** on PR #86 |',
)
text = text.replace(
    '| UX-1 | Populated Dashboard locale parity + hierarchy | 100% | PR #84 merged as `0c2e0ee18da003ccc413ffeffef18334a77c6ad9`; exact-head CI #1452 + drift #1264 + visual run `31409668306` green; UX **9.2/10**; post-merge CI #1453 + drift #1265 green | ✅ Closed |\n',
    '| UX-1 | Populated Dashboard locale parity + hierarchy | 100% | PR #84 merged as `0c2e0ee18da003ccc413ffeffef18334a77c6ad9`; exact-head CI #1452 + drift #1264 + visual run `31409668306` green; UX **9.2/10**; post-merge CI #1453 + drift #1265 green | ✅ Closed |\n'
    '| UX-2 | Summary load-error desktop composition | 90% | Fresh exact-main baseline run `31413385769` isolated Summary desktop at **8.1/10** while Profile/Importer stayed >=9; product head `97df55865a13916c9bdf7f01796a60ba2d827ee2` remediated to **9.3/10**, CI #1458 + drift #1270 + visual run `31414604776` green; final docs-head recertification, Certifier, merge and post-merge gates pending | 🟡 |\n',
)
text = text.replace(
    'UX-1 is intentionally narrower than the historical UX plan: the empty/first-use Dashboard, Journal, Profile, Importer and post-save surfaces remain protected by their existing rendered certifications. Further UX LOTs are created only if new rendered evidence exposes a sub-9 state.',
    'UX-1 was intentionally narrower than the historical UX plan. A fresh exact-main audit later found one new <=9.0 state: Summary load-error desktop composition. UX-2 is limited to that evidence; Dashboard, Journal, Profile, Importer and post-save surfaces stay protected by their existing rendered certifications.',
)
anchor = '- Exact final head `27ee9b00c2326add7642bb0f544f5658ebf4d949` passed CI #1452 and migration drift #1264. Final visual run `31409668306`, artifact `9071144760`, digest `sha256:fb2490f8a4d293206917adbcfb56dbc57c24a49f67a61f27eea3a9db391e088f` rendered 24/24 FR/AR top/mid/lower views with one Flutter view each and zero page errors. UX Auditor FINAL PASS **9.2/10**, Clinical Safety Reviewer FINAL PASS, Release Certifier CERTIFIED. PR #84 merged with expected-head locking as `0c2e0ee18da003ccc413ffeffef18334a77c6ad9`; post-merge CI #1453 and drift #1265 passed. **UX-1 is 100% closed.**\n'
addition = anchor + '''\n### UX-2 pre-closeout evidence\n\n- Fresh exact-main audit source `f65b0d6619b233442c0df6baaf70ad70d74593fa`: valid run `31413385769`, artifact `9072572476`, digest `sha256:f111bd8af928c4ef96a83fd2924782ff3acd85dc9c1efba002aa01cf22ed7aae`; 24/24 Summary/Importer/Profile FR/AR renders across `1440×1000`, `768×1024`, `390×844`, `360×560`, one Flutter view each and zero page errors.\n- Product Design baseline kept Profile (~9.1–9.2) and Importer (~9.0–9.1) closed; only Summary load-error desktop was reopened at **8.1/10** because the horizontal error strip was visually stranded in a large empty canvas.\n- UX-2 changes presentation only: a compact focal error card on wide layouts, preserving localized copy, `_fetchData`, period controls, mobile behavior, clinical/data semantics, persistence, API and egress boundaries.\n- Product head `97df55865a13916c9bdf7f01796a60ba2d827ee2`: canonical PR CI #1458 and migration drift #1270 passed. Exact-product visual run `31414604776`, artifact `9072965994`, digest `sha256:ada98ce81842ce59354a09ba7dd3158f43d5711517d5fce6eab2b3dfe3d66e2a`: 8/8 Summary FR/AR renders, one Flutter view each, zero page errors. UX Auditor / Product Design **PASS — 9.3/10**; no critical/high visual finding; mobile and RTL remain stable.\n- UX-2 remains open until the final documentation head is revalidated, Release Certifier authorizes expected-head merge, PR #86 merges and post-merge CI/drift pass.\n'''
if anchor not in text:
    raise SystemExit('UX-1 closeout anchor missing')
text = text.replace(anchor, addition, 1)

path.write_text(text)
