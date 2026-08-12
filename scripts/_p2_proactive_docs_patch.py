from pathlib import Path


def replace_exact(path: str, old: str, new: str) -> None:
    file = Path(path)
    text = file.read_text()
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected exactly one match, found {count}: {old[:100]!r}")
    file.write_text(text.replace(old, new))


replace_exact(
    "docs/ROADMAP.md",
    "> **Last updated:** 2026-08-12 — P2-CLINICAL-TWIN is merged and post-merge green. P2-PROACTIVE is the next executable clinical-intelligence LOT. UX visual rebase remains closed through UX-11 at 9.8/10.",
    "> **Last updated:** 2026-08-12 — P2-CLINICAL-TWIN is merged and post-merge green. P2-PROACTIVE is the active certification unit in PR #138. UX visual rebase remains closed through UX-11 at 9.8/10.",
)
replace_exact(
    "docs/ROADMAP.md",
    "| Clinical intelligence / proactivity | P0 audit + semantics + skills foundation + evidence registry + clinical twin closed | 🟢 P2-PROACTIVE ready | PR #135 merge `00292e44…`; post-merge CI #1805 + drift #1617 green |",
    "| Clinical intelligence / proactivity | P0 audit + semantics + skills foundation + evidence registry + clinical twin closed; deterministic attention active | 🟡 P2-PROACTIVE certification | PR #138 — Deterministic Attention & Insight Lifecycle |",
)
replace_exact(
    "docs/ROADMAP.md",
    "**Closure:** PR #135 head `1058ee4a…` passed CI #1804 + drift #1616, Clinical Safety Reviewer and Release Certifier; merge `00292e44…` then passed post-merge `main` CI #1805 + drift #1617.\n\n## Ordered execution",
    "**Closure:** PR #135 head `1058ee4a…` passed CI #1804 + drift #1616, Clinical Safety Reviewer and Release Certifier; merge `00292e44…` then passed post-merge `main` CI #1805 + drift #1617.\n\n## P2-PROACTIVE — Deterministic Attention & Insight Lifecycle — PR #138 CERTIFICATION\n\nThe candidate adds a diabetes-owned attention-state layer over certified `ClinicalObservationState` rows. It is not patient truth and does not deliver notifications. It requires explicit deterministic emergency clearance before any proactive write, requires the source evidence rule to remain governed/current before refreshing P2, exposes a field-by-field `PriorityVector` instead of a scalar risk/confidence score, selects at most one materially changed candidate, preserves pending candidates, and suppresses unchanged repeats. V1 lifecycle is `NEW / MONITORING / PERSISTING / IMPROVING / RESOLVED`; `ESCALATED` is structurally unavailable until a separately governed criterion exists. `IMPROVING` means only movement toward the recorded personal baseline; `RESOLVED` means the descriptive observation has been absent across a full eligible evidence horizon, never that disease/treatment is resolved. V1 next steps are limited to `MONITOR` and `COLLECT_MISSING_DATA`. No patient-facing message/API, scheduler or notification transport is added.\n\n**Certification gate:** exact-head CI + PostgreSQL + migration drift, Clinical Safety Reviewer, Release Certifier, expected-head locked merge, then post-merge `main` CI + drift before closure.\n\n## Ordered execution",
)
replace_exact(
    "docs/ROADMAP.md",
    "| **P2-PROACTIVE** | **Prioritization + Insight Lifecycle** | ▶️ **NEXT** | Clinical relevance, persistence, actionability, evidence density and interruption cost govern what surfaces and when |",
    "| **P2-PROACTIVE** | **Prioritization + Insight Lifecycle** | 🟡 **CERTIFICATION — PR #138** | Explicit deterministic priority vector + material-change lifecycle + max-one attention budget; specialist/release review + merge/post-merge required |",
)

personal_response_tail = """- no pattern detector may produce treatment optimization, insulin-dose advice, diagnosis or autonomous clinical recommendation;\n- the Journal shows one strongest pattern by default and makes secondary patterns explicitly expandable so longitudinal context does not crowd out the primary history task.\n\n\n### Post-save experience contract"""
proactive_section = """- no pattern detector may produce treatment optimization, insulin-dose advice, diagnosis or autonomous clinical recommendation;\n- the Journal shows one strongest pattern by default and makes secondary patterns explicitly expandable so longitudinal context does not crowd out the primary history task.\n\n### Deterministic proactive-attention contract\n\n- proactive attention is diabetes-owned product state derived only from the certified deterministic `ClinicalObservationState`; it is not a patient fact, diagnosis/problem list, emergency state or companion/deep-memory state;\n- deterministic emergency handling is an upstream prerequisite: without explicit `CLEAR` clearance the proactive engine performs no clinical-twin refresh, creates no proactive state and surfaces nothing; an active emergency suppresses proactive attention rather than competing for the attention budget;\n- the `personal_response` evidence rule must remain `GOVERNED_RULE` and `current` before the proactive engine may refresh its source observation memory; superseded or non-governed evidence fails closed before source mutation;\n- clinical priority is an explicit field-by-field vector (time-sensitivity class, governed relevance, persistence, absolute descriptive baseline distance, evidence strength/maturity, actionability, interruption cost, observation/day density, recurrence and recency); no scalar risk/confidence/urgency score or companion `concern_level` is clinical authority;\n- the attention budget returns at most one candidate per decision call and suppresses an unchanged decision after it has been selected; materially changed unselected candidates retain pending reason codes until their turn;\n- lifecycle transitions are material-source driven rather than API-read-frequency driven: first selected insight is `NEW`, unchanged follow-up is `MONITORING`, recurrence may become `PERSISTING`, and movement toward the recorded personal baseline may become `IMPROVING`;\n- `IMPROVING` is descriptive only and must not be presented as treatment effect, causality or clinical recovery;\n- `RESOLVED` means only that a previously observed descriptive pattern is inactive and has had no supporting sighting across a full eligible evidence horizon; sparse/missing data cannot resolve it and this state must never be described as disease/problem resolution;\n- `ESCALATED` is not reachable in v1 and is blocked by a database constraint until a separately governed safety/handoff criterion is approved;\n- v1 allowed next steps are only `MONITOR` and `COLLECT_MISSING_DATA`; database constraints reject stronger unapproved actions, unapproved source producer/evidence, non-deterministic provenance and direct ORM escalation;\n- selection records that an item was chosen by the internal attention budget; it does **not** mean a patient notification was delivered; no patient-facing proactive API/message, background scheduler, push/local notification or clinician transport is enabled by this contract.\n\n\n### Post-save experience contract"""
replace_exact("docs/SPECS.md", personal_response_tail, proactive_section)
