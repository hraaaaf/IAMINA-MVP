# IAmina Skills

These files are repository-owned execution procedures. They do not replace `AGENTS.md`, `CLAUDE.md`, `docs/CONTRIBUTING.md`, architecture docs, ADRs or the roadmap.

Agents must load the skills required by the assigned LOT through the routing rules in `AGENTS.md` and `.agents/README.md`.

## Available skills
- `lot-execution/SKILL.md` — mandatory for every roadmap LOT.
- `ux-ui-certification/SKILL.md` — UX/UI, responsive, navigation and visual/i18n presentation work.
- `clinical-safety/SKILL.md` — clinical logic, medical wording and safety behavior.
- `mena-clinical-linguistic-safety/SKILL.md` — AI secondary review of the exact fingerprinted MENA safety corpus across Arabic, French, English, Darija, transliteration, code-switching and voice-transcript parity; never substitutes for required human approval.
- `diabetes-clinical-reasoning/SKILL.md` — diabetologist-grade interpretation discipline for diabetes observations, applicability, uncertainty and allowed next-step classes.
- `diabetes-proactive-intelligence/SKILL.md` — evidence-qualified prioritization, attention budget and longitudinal insight lifecycle without autonomous treatment authority.
- `diabetes-evidence-intelligence/SKILL.md` — source freshness, evidence maturity, supersession and promotion gates for diabetes knowledge; core sources are indexed in `diabetes-evidence-intelligence/CORE_SOURCES.md`.
- `migrations-database/SKILL.md` — models, migrations, persistence and PostgreSQL-sensitive work.
- `security-review/SKILL.md` — auth, authorization, privacy, secrets and external egress.
- `release-certification/SKILL.md` — mandatory final certification for every LOT.

## Diabetes intelligence routing
- Any change to diabetes interpretation, clinical reasoning or clinician/patient semantic meaning loads `clinical-safety`, `diabetes-clinical-reasoning` and `diabetes-evidence-intelligence`.
- Any MENA safety-corpus, Arabic/Darija, transliteration, code-switching or multilingual emergency-parity review additionally loads `mena-clinical-linguistic-safety`.
- Any proactive prioritization, longitudinal insight state, follow-up or notification-semantics change additionally loads `diabetes-proactive-intelligence`.
- A research-horizon item cannot become patient authority from a skill alone; promotion requires the repository clinical-safety and release process.

## Precedence
If a skill conflicts with a canonical safety/architecture/product document, the canonical document wins. If a diabetes-specific skill conflicts with deterministic runtime safety/domain authority, deterministic authority wins. The conflict must be surfaced and the skill corrected; agents must not silently choose the easier instruction.
