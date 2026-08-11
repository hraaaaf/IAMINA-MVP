# IAmina — Technical Debt

This register contains **unresolved technical debt only**.

Rules:

- Do not keep resolved items “for history”; git is the history.
- Do not duplicate normal roadmap features here.
- A roadmap blocker appears here only when it represents a persistent technical compromise in the current system.
- Provider-brand migration wishes are not technical debt unless they reflect a concrete current defect.

## TD-001 — AI egress authorization exists, but payload/media governance is not yet complete

- **Area:** Privacy / AI architecture
- **Priority:** Critical before real-patient pilot
- **Resolved foundation:** P0-B introduced one central provider-agnostic authorization boundary for currently wired live external AI/media operations. Patient, purpose, modality, and server-side consent are enforced at real egress time; missing/unknown authorization state fails closed; CI blocks new direct callsites that omit the central authorization assertion.
- **Current compromise:** authorization is stronger than payload governance. Explicit field allowlists, uniformly enforced minimization/redaction, purpose/modality-granular raw-media consent, processor/subprocessor metadata, residency/retention/no-training metadata, and timeout/failure policy are not yet complete as one enforceable contract.
- **Risk:** an authorized call can still be insufficiently minimized or insufficiently described operationally even though it cannot bypass consent/scope authorization.
- **Resolution:** finish P0-MENA-1 by making payload/media eligibility and processor/retention/failure policy explicit and testable at the boundary.

## TD-002 — Firebase remains sovereignty-critical legacy authentication infrastructure

- **Area:** Auth / sovereignty
- **Priority:** Critical before target architecture is achieved
- **Current compromise:** Firebase identity/token dependencies remain in backend/client flows.
- **Risk:** fragmented identity ownership and migration complexity.
- **Resolution:** P0-MENA-3 account-preserving Django-native migration with reconciliation + rollback before dependency removal.

## TD-003 — Provider timeout/circuit-breaker/failure UX is incomplete

- **Area:** Reliability / AI
- **Priority:** High before pilot
- **Current compromise:** provider abstraction/fallback exists in parts of the stack, but explicit per-call timeout and unified failure contracts are not consistently enforced across modalities.
- **Risk:** hanging requests, inconsistent streaming failure, poor patient UX.
- **Resolution:** enforce timeout/failure/fallback policy at the outbound boundary and add frontend typed error UX.

## TD-004 — CI/SAST exclusion paths may contain legacy names

- **Area:** CI / security tooling
- **Priority:** Medium-high
- **Current compromise:** historical Bandit exclusions referenced pre-refactor package names in the previous audit.
- **Risk:** noisy or misleading coverage and accidental scan gaps.
- **Resolution:** verify current CI paths against actual repository layout; remove stale exclusions rather than copying old names forward.

## TD-005 — Locale/safety model is still too coarse for MENA rollout

- **Area:** Internationalization / safety
- **Priority:** Critical before pilot locale enablement
- **Current compromise:** legacy language handling does not yet fully separate country, UI language, response language, dialect, script/transliteration, units, time zone, and emergency jurisdiction.
- **Risk:** unsafe assumptions from geolocation/language coupling and unequal safety coverage across dialects.
- **Resolution:** P0-MENA-2 locale contract + native-reviewed parity corpus + deterministic fallback + validated emergency resources.

## TD-006 — High-severity language-variant coverage has a known gap

- **Area:** Safety
- **Priority:** Critical before real-patient pilot
- **Current compromise:** exact/curated lexical safety matching does not yet cover all common high-severity orthographic variants for the pilot dialect.
- **Risk:** delayed deterministic interception.
- **Resolution:** curated native-reviewed variant corpus with positive/negative tests; do not use overly loose fuzzy matching that creates unsafe false positives.

## TD-007 — Emergency events are not yet proven to reach a monitored operational channel

- **Area:** Safety operations
- **Priority:** Critical before real-patient pilot
- **Current compromise:** detection/logging alone does not guarantee human operational visibility.
- **Risk:** a safety event may be recorded without actionable escalation.
- **Resolution:** implement monitored routing or explicitly approve/document a different operating model before pilot.

## TD-008 — Frontend integration/accessibility coverage is incomplete

- **Area:** Quality / accessibility
- **Priority:** Medium; high before broader release
- **Current compromise:** backend coverage is stronger than end-to-end Flutter critical-flow coverage; accessibility validation is incomplete.
- **Risk:** regressions in onboarding/logging/safety/error flows and poor accessibility for target users.
- **Resolution:** focused Flutter widget/integration tests + semantics/accessibility baseline for pilot-critical flows.

## TD-009 — Staff/professional strong authentication is incomplete

- **Area:** Security
- **Priority:** High before staff/professional scale
- **Current compromise:** strong authentication/MFA requirements for privileged roles are not yet fully implemented.
- **Risk:** elevated impact of credential compromise.
- **Resolution:** include strong-auth requirements in Django-native auth design and enforce for privileged roles.

## TD-010 — Observability data retention policy is incomplete

- **Area:** Privacy / observability
- **Priority:** High before broader production use
- **Current compromise:** retention instrumentation can include patient-linked identifiers/events without a fully documented lifecycle policy.
- **Risk:** over-retention and unclear deletion/export behavior.
- **Resolution:** define retention/deletion schedule and account-deletion interaction for observability data.

## TD-011 — Demo seed data can become stale relative to analysis windows

- **Area:** Dev/demo reliability
- **Priority:** Low-medium
- **Current compromise:** demo data seeded at fixed times may fall outside analysis windows over time.
- **Risk:** misleading “no data” behavior during QA/demo.
- **Resolution:** ensure seed generation is relative/idempotent or reset automatically in explicitly demo-only environments.

## TD-012 — Large Flutter surfaces and silent catches reduce maintainability

- **Area:** Frontend maintainability
- **Priority:** Medium after pilot-critical work
- **Current compromise:** some large widgets/services and broad/silent error catches remain from rapid iteration.
- **Risk:** hidden failures and expensive regression surface.
- **Resolution:** refactor opportunistically in focused PRs; typed/logged error handling first, cosmetic decomposition second.

## TD-013 — Clinical analytics lack complete PostgreSQL source-of-truth certification

- **Area:** Clinical analytics / database parity
- **Priority:** Critical before real-patient pilot
- **Current compromise:** production-authoritative SQL includes PostgreSQL-specific behavior while the historical main CI path has relied heavily on SQLite. At least one GRI implementation issue and one daily-average SQL divergence were identified during the P0 audit.
- **Risk:** a metric can be mathematically wrong or pass SQLite tests while failing/diverging on PostgreSQL.
- **Resolution:** P0-C — normative formula verification, metric eligibility rules, PostgreSQL CI execution, and regression fixtures. Remove this debt only after P0-C is merged and green.

## Documentation closeout rule

After every merged task/phase:

1. update `docs/ROADMAP.md`;
2. update architecture/spec/domain docs only where merged truth changed;
3. **remove** debt that was fully paid;
4. rewrite partially paid debt so it describes only the remaining compromise.

Do not leave a debt entry worded as “not implemented” after the foundation has actually shipped.

## Removed obsolete debt

The old **“migrate Gemini → Kimi”** item is intentionally deleted. It conflicts with the current provider-agnostic MENA strategy. Provider selection now happens per modality only after the privacy/quality benchmark in `docs/ROADMAP.md`.
