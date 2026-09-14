# IAmina — Technical Debt

This register contains **unresolved technical debt only**.

Rules:

- Do not keep resolved items “for history”; git is the history.
- Do not duplicate normal roadmap features here.
- A roadmap blocker appears here only when it represents a persistent technical compromise in the current system.
- Provider-brand migration wishes are not technical debt unless they reflect a concrete current defect.

## TD-001 — Structured text egress is governed, but free-form/raw-media de-identification is not universal

- **Area:** Privacy / AI architecture
- **Priority:** Critical before any real-patient path relies on external processing of unstructured patient documents
- **Resolved foundation:** P0-B/P0-MENA-1 established one central provider-agnostic authorization/minimization boundary. PR #481 adds patient-aware last-mile text DLP for the scoped patient's known Django identity (name, email, username and profile DOB), retains generic CIN/email/phone/account-ID detection, and makes patient `document_ingest` images fail closed before raw cloud OCR. Purpose/modality consent, payload allowlists, provider policy, anti-bypass CI and secret/SAST gates remain enforced.
- **Current compromise:** deterministic matching cannot prove removal of every free-form identifier that is neither represented in the patient identity model nor syntactically recognizable. In particular, IAMINA has no canonical patient-address field to exact-match an unlabeled address embedded in arbitrary text. Patient medical-document cloud OCR therefore remains intentionally unavailable until a qualified local OCR/de-identification lane exists.
- **Risk:** uncommon or unlabeled free-form identifiers could survive a text-only redaction pass if they evade the generic DLP, while raw document pixels may contain identity before OCR.
- **Resolution:** keep patient-document cloud OCR fail closed; qualify a local OCR/de-identification lane and evaluate a multilingual PHI corpus for false negatives/false positives before widening egress. If IAMINA later stores additional direct identifiers such as address, add them to the authoritative patient-identity redaction source rather than relying on heuristic guessing.

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

## TD-012 — Large Flutter surfaces and silent catches reduce maintainability

- **Area:** Frontend maintainability
- **Priority:** Medium after pilot-critical work
- **Current compromise:** some large widgets/services and broad/silent error catches remain from rapid iteration.
- **Risk:** hidden failures and expensive regression surface.
- **Resolution:** refactor opportunistically in focused PRs; typed/logged error handling first, cosmetic decomposition second.

## TD-013 — Authentication endpoints lack retained deterministic abuse protection

- **Area:** Security / authentication
- **Priority:** High before any real-patient release
- **Tracker:** #622
- **Resolved foundation:** native Django registration/login/password reset enforce password validation, account-enumeration resistance on recovery, signed/expiring bearer tokens and explicit token revocation. Production transport is HTTPS/HSTS/secure-cookie hardened.
- **Current compromise:** repository and project audit found no retained proof of endpoint-specific throttling or lockout for login, registration or password-reset requests. Generic platform firewall/DDoS protection is not equivalent evidence. The previously proven runtime also reported `cache=unavailable`, so a Redis-only limiter would not satisfy this gap.
- **Risk:** credential stuffing, brute-force login attempts, account creation abuse and password-reset flooding can consume resources or increase account-compromise risk.
- **Resolution:** implement explicit, testable auth abuse limits that remain effective without Redis; preserve account-enumeration resistance; return a typed 429 contract; test repeated bad login, recovery flooding, distinct-account isolation and recovery-window reset. A Vercel WAF rule may provide a defense-in-depth edge layer, but it must not be the only retained control unless its exact production configuration is captured and verified.

## Documentation closeout rule

After every merged task/phase:

1. update `docs/ROADMAP.md`;
2. update architecture/spec/domain docs only where merged truth changed;
3. **remove** debt that was fully paid;
4. rewrite partially paid debt so it describes only the remaining compromise.

Do not leave a debt entry worded as “not implemented” after the foundation has actually shipped.

## Removed obsolete debt

The old **“migrate Gemini → Kimi”** item is intentionally deleted. It conflicts with the current provider-agnostic MENA strategy. Provider selection now happens per modality only after the privacy/quality benchmark in `docs/ROADMAP.md`.

The former PostgreSQL clinical-analytics parity debt was removed after P0-C established normative formula correction, permanent PostgreSQL source-of-truth CI and migration-drift gates.
