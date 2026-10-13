# IAMINA V1 #6 — Stable user-facing identity

**BEFORE**: issue #958 contains the written Goal and reference before implementation; real Chrome ready screenshots 390x844, 768x1024, 1280x900 are preserved in workflow 38320834577 artifact 11779217453. Tone question and chips appear, progress is 6/6.

**Target**: remove user tone choices in initial onboarding AND preferences screen, progress becomes five steps, keep language, country, diabetes type, treatment and unit, preserve sticky CTA. Maintain FR/EN/AR/RTL. In the profile shortcut copy remove tone. On finish the legacy preference storage accepts fixed neutral for compatibility. This does not change clinical tone adaptation in backend/companion/tone.py; no new treatment/LLM rule or patient provider access.

**Dependency**: this branch starts from unmerged #956 exact HEAD 0b2625a09f8211ab8e6f0a8ed300774de2854756, which has the required independent language-only country fix. A PR to main includes the #5 commit stack until #5 merges; do not merge this PR before #5 is reviewed/merged/rebased and exact-HEAD CI rechecked. Decision #6 stays OPEN until explicit merge and post-merge.

**Proof still needed**: 3 viewport AFTER Chrome captures vs BEFORE same sizes, sticky CTA 390/768/1280, locale tests FR/EN/AR and Flutter suite, no overflow/JavaScript errors. No Vercel.
