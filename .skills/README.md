# IAmina Skills

These files are repository-owned execution procedures. They do not replace `AGENTS.md`, `CLAUDE.md`, `docs/CONTRIBUTING.md`, architecture docs, ADRs or the roadmap.

Agents must load the skills required by the assigned LOT through the routing rules in `AGENTS.md` and `.agents/README.md`.

## Available skills
- `lot-execution/SKILL.md` — mandatory for every roadmap LOT.
- `ux-ui-certification/SKILL.md` — UX/UI, responsive, navigation and visual/i18n presentation work.
- `clinical-safety/SKILL.md` — clinical logic, medical wording and safety behavior.
- `migrations-database/SKILL.md` — models, migrations, persistence and PostgreSQL-sensitive work.
- `security-review/SKILL.md` — auth, authorization, privacy, secrets and external egress.
- `release-certification/SKILL.md` — mandatory final certification for every LOT.

## Precedence
If a skill conflicts with a canonical safety/architecture/product document, the canonical document wins. The conflict must be surfaced and the skill corrected; agents must not silently choose the easier instruction.