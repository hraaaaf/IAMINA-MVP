from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text()
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected exactly one target in {path}, found {count}")
    p.write_text(text.replace(old, new, 1))


replace_once(
    "docs/ROADMAP.md",
    "> **Last updated:** 2026-08-10 — P1-JOURNAL-6 is closed; P1-JOURNAL-7 Ramadan mode v2 is the active merge unit in PR #75.",
    "> **Last updated:** 2026-08-10 — P1-JOURNAL-7 Ramadan mode v2 is certified pre-merge in PR #75; expected-head merge and post-merge CI/drift remain before closure.",
)
replace_once(
    "docs/ROADMAP.md",
    "| Journal metabolic-event redesign | 78% | 🔵 P1-JOURNAL-7 merge unit | P0-JOURNAL-1/2 + P1-JOURNAL-3/4/5/6 merged; PR #75 Ramadan mode v2; explicit profile period, neutral meal vocabulary, additive Django/Drift persistence; pre-closeout UX 9.3/10; final-head certification + merge/post-merge required |",
    "| Journal metabolic-event redesign | 78% | 🟢 P1-JOURNAL-7 certified pre-merge | P0-JOURNAL-1/2 + P1-JOURNAL-3/4/5/6 merged; PR #75 exact product head `2aacc83` certified: CI #1367 + drift #1179 + PostgreSQL green; exact-head visual run #19; UX 9.3/10; Clinical Safety, Database/Migration and UX reviewers PASS; merge/post-merge remain |",
)
replace_once(
    "docs/ROADMAP.md",
    "| P1-JOURNAL-7 | Ramadan mode v2 | 🔵 PR #75 merge unit | explicit nullable profile period; Suhoor/Iftar/Snack/Other only inside the configured period; no fasting inference or meal preselection; additive Django 0023 + Drift v9; FR/EN/AR + RTL; pre-closeout UX 9.3/10 |",
    "| P1-JOURNAL-7 | Ramadan mode v2 | 🟢 Certified pre-merge | PR #75 product head `2aacc83`; explicit nullable profile period; no fasting inference/meal preselection; update-only local Ramadan persistence prevents fabricated medical defaults; CI #1367 + drift #1179 + PostgreSQL green; exact-head visual run #19; UX 9.3/10; three independent reviewers PASS |",
)
replace_once(
    "docs/ROADMAP.md",
    "**Pre-closeout evidence on product head `f59f74d95bdc5e50186ffc9eab8ca1b315008596`:** CI #1354 SUCCESS; migration drift #1166 SUCCESS; visual audit run `31374280465` SUCCESS with 24/24 FR/AR Profile + Add Log renders across `1440×1000`, `768×1024`, `390×844` and hostile `360×560`; artifact `9057312311`, digest `sha256:58426aa23415d404d689ecf21dbf7c3fb64c1376fce5eb7916a270edec592430`; the first FR `360×560` pass exposed a real 2 px action overflow, which was remediated and protected by a permanent regression test; UX Auditor pre-closeout score **9.3/10 PASS**.\n\nThese canonical documentation changes intentionally make the pre-closeout anchors stale. Exact-final-head CI + migration drift + visual recertification, independent Clinical Safety / Database-Migration / UX review passes, Release Certifier verdict, expected-head merge and post-merge CI/drift remain mandatory before P1-JOURNAL-7 may be declared 100% closed.",
    "**Certified pre-merge evidence on product head `2aacc83cdfb49a42f447172ae73cf1c0ea01303e`:** canonical CI #1367 SUCCESS; migration drift #1179 SUCCESS; PostgreSQL migration validation + full source-of-truth suite SUCCESS; exact-head visual audit run `31376668264` (#19) SUCCESS with 24/24 FR/AR Profile + Add Log renders across `1440×1000`, `768×1024`, `390×844` and hostile `360×560`; artifact `9058221105`, digest `sha256:be00632945a35aaa9f8ed7e84b73d4af76268d31142debefce97574bd9315018`; UX Auditor **9.3/10 PASS**; Clinical Safety Reviewer PASS; Database & Migration Reviewer PASS.\n\nThe independent clinical review found and blocked a fresh-local-profile path that could create a medical profile row with default clinical targets when only Ramadan was being configured. The remediation makes local Ramadan persistence update-only, refuses to manufacture a profile when none exists, preserves existing clinical profile values, reports local/server/degraded/failure save states truthfully in FR/EN/AR, and is protected by permanent regressions. Temporary remediation/audit scaffolding is absent from the PR net diff.\n\nP1-JOURNAL-7 is **certified pre-merge, not closed**. Release Certifier verdict, expected-head merge and post-merge CI + migration drift remain mandatory before it may be declared 100% closed.",
)

replace_once(
    "docs/SPECS.md",
    "- Django persistence adds nullable profile dates through migration `0023`; Drift v8→v9 adds the same nullable local profile dates without rewriting existing Journal rows or their `client_uuid` values;",
    "- Django persistence adds nullable profile dates through migration `0023`; Drift v8→v9 adds the same nullable local profile dates without rewriting existing Journal rows or their `client_uuid` values;\n- local Ramadan persistence is update-only: if no local medical profile exists, configuring Ramadan must not create one or materialize default diabetes type, treatment, unit or glucose-target values; existing clinical profile fields must remain unchanged when the Ramadan period is updated;\n- save feedback distinguishes local+server success, local-only persistence, server-only persistence and total failure instead of claiming a storage state that did not occur;",
)

replace_once(
    "docs/MEDICAL_DATA_PLAN.md",
    "Ramadan context must not trigger diagnosis, medication or insulin-dose calculation, treatment optimization, causal inference or autonomous advice. The Django and Drift schema changes are additive and nullable; historical logs and stable `client_uuid` values are preserved, and the legacy per-log `ramadan_mode` field is not retrospectively rewritten or reinterpreted as authoritative fasting evidence.",
    "Ramadan context must not trigger diagnosis, medication or insulin-dose calculation, treatment optimization, causal inference or autonomous advice. The Django and Drift schema changes are additive and nullable; historical logs and stable `client_uuid` values are preserved, and the legacy per-log `ramadan_mode` field is not retrospectively rewritten or reinterpreted as authoritative fasting evidence. Local Ramadan persistence must fail closed when no local medical profile exists rather than creating a profile that materializes default clinical values; when a profile does exist, changing the Ramadan period must preserve its diabetes type, treatment, unit and target values. Patient-facing save feedback must reflect whether persistence succeeded locally, on the server, on only one side, or nowhere.",
)
