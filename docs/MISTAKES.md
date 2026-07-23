# IAmina — Mistakes and Durable Lessons

Read this before high-risk work. This file contains **reusable lessons only** — not current status, backlog, provider preferences, or resolved sprint history.

## 1. Documentation can become a production bug

Stale docs previously described old branches, old provider plans, old framework versions, and contradictory product strategy as if they were current.

**Rule:** every doc must have one purpose. Use:

- ROADMAP = forward work;
- ARCHITECTURE = current boundaries;
- SPECS = current capability;
- TECHDEBT = unresolved compromises;
- ADR/timeline = history.

Do not duplicate status across files.

## 2. Never commit secrets in local agent/tool configuration

Local permission/config files can contain literal API keys inside allowed shell commands.

**Rule:** `.env` is not the only secret risk. Audit `.claude/`, IDE launch configs, shell scripts, fixtures, notebooks, CI examples, and docs. If a key is committed, treat it as compromised and rotate/revoke it.

## 3. One edit target at a time when the editing tool is path-sensitive

Multi-file mutation through a tool that expects one file can put content in the wrong target.

**Rule:** use atomic per-file writes unless the tool explicitly supports a multi-file transaction.

## 4. Generated code/imports must be cleaned

Generated or refactored files can keep stale imports and configuration that silently pollute lint or dependency behavior.

**Rule:** run formatter/analyzer after generation/refactor and remove unused generated artifacts immediately.

## 5. Django test transactions do not reset external cache state

Database rollback does not imply Redis/Django cache rollback.

**Rule:** tests that use cache must isolate/clear relevant keys and use unique identities where necessary.

## 6. Never seed demo data into real patient UX by accident

Unconditional demo seeding can display fake clinical information to a real user.

**Rule:** demo data is opt-in/debug-only and must be impossible to confuse with real patient data.

## 7. Demo dates must be relative or resettable

Fixed seed dates eventually fall outside analysis windows and create silent “no data” degradation.

**Rule:** generate demo timelines relative to now or provide an explicit idempotent reset path.

## 8. Never use process-local dictionaries for cross-request workflow state

A module-level dict can appear to work in single-process development and fail immediately with multiple workers.

**Rule:** use a shared bounded-TTL store (for example Redis/Django cache) for cross-request state and define consume-once/idempotency behavior.

## 9. Flutter navigation objects must not be recreated in `build`

Recreating routing/stateful infrastructure during rebuilds resets state and causes hard-to-debug navigation behavior.

**Rule:** initialize long-lived navigation/state infrastructure at the proper lifecycle/application level.

## 10. Provider state must be registered before `watch/read`

Flutter Provider lookups fail at runtime when types are not registered at the correct ancestor.

**Rule:** every dependency accessed through context must have an explicit provider registration path and test coverage for the screen entry point.

## 11. Avoid unbounded layout combinations

`Expanded` inside an unconstrained scroll context can produce blank/broken layouts.

**Rule:** reason explicitly about constraints when mixing flex and scrolling widgets.

## 12. Do not reintroduce integer-index navigation coupling

Historical navigation used duplicated integer→route mappings that drifted.

**Rule:** keep navigation generated from one route/module configuration source. Do not re-create parallel index switch tables.

## 13. Flutter web is not a normal DOM application

Canvas-rendered Flutter surfaces cannot be reliably tested with ordinary text/CSS selectors as if they were HTML widgets.

**Rule:** use Flutter widget/integration testing for product UI behavior; browser automation may still be useful for shell/network/smoke concerns where selectors actually exist.

## 14. Never trust model output shape without validation

Models can ignore requested JSON schemas, add fences, rename keys, or return prose.

**Rule:** strict parser/validator + bounded aliases only when justified + deterministic fallback. A prompt is not a schema guarantee.

## 15. Streaming output and persisted transcript may differ

Filtering/throttling can operate on streamed content before or after persistence.

**Rule:** document which state is authoritative for safety/audit claims; never assume the stored chat row is byte-identical to what the patient saw.

## 16. Language punctuation/tokenization rules are not universal

Sentence splitting and safety matching designed around French/English punctuation can behave differently in Arabic-script or mixed-language text.

**Rule:** treat tokenizer/sentence-boundary behavior as locale-sensitive and test native examples; do not “fix” punctuation globally without false-positive analysis.

## 17. Treatment-context wording must never imply autonomous treatment change

Generic clinical alerts can accidentally contain treatment-specific wording that is irrelevant or unsafe for other patient profiles.

**Rule:** keep patient-facing guidance within the companion boundary and avoid dose/treatment-change instructions. Treatment-context-specific wording requires explicit safe gating and clinical review.

## 18. A deterministic safety gate is only useful if every interactive path reaches it

Adding a new endpoint or modality can accidentally bypass the established safety chain.

**Rule:** endpoint/provider expansion must include route registration and tests proving safety interception occurs before generative processing.

## 19. “PHI stripped” is not a blanket proof of safe model egress

Media, raw context, identifiers embedded in text, or alternate direct call paths can still disclose sensitive information.

**Rule:** privacy must be enforced at one outbound boundary with default-deny payload/media policy; do not rely on one pseudonymizer call as a global claim.

## 20. Location is not language, consent, or emergency jurisdiction logic

Automatically inferring all locale behavior from country/IP creates wrong and potentially unsafe assumptions.

**Rule:** location may suggest. The user confirms language/dialect; emergency resources and consent rules are explicit jurisdictional configuration.

## 21. Do not call IAmina a POC — but do not falsely claim deployment either

The previous wording swung between “POC/demo” and “production app used by real patients.” Both can be misleading.

**Rule:** describe the actual stage precisely: **real product under development / pre-pilot or closed-pilot status as recorded in ROADMAP**. Never lower engineering rigor by calling it a toy, and never claim real-patient/GA status before it is true.

## 22. Historical architecture is not current instruction

Old platform plans and accepted-then-superseded directions remain useful evidence but can mislead agents.

**Rule:** active work comes from ROADMAP + current ARCHITECTURE. Historical docs must be labeled and must not carry “next step” authority.
