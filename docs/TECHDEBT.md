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

## TD-002 — Firebase migration-only dependencies remain installed

- **Area:** Auth / sovereignty cleanup
- **Priority:** Medium before final target-architecture cleanup; not a current native-auth blocker while the migration bridge remains disabled by default
- **Resolved foundation:** Django `User` is authoritative. Native registration/login/password recovery do not depend on Firebase. Firebase is accepted only as a temporary migration credential, and `ENABLE_FIREBASE_MIGRATION` defaults to disabled. The Flutter app still declares `firebase_auth` / `firebase_core`, and backend migration support remains present for controlled legacy-account migration.
- **Current compromise:** Firebase client/backend dependencies and migration-specific verification code remain shipped even though they are no longer the canonical identity path.
- **Risk:** unnecessary dependency/supply-chain and maintenance surface persists, and an operator can intentionally re-enable the migration bridge for a controlled migration window.
- **Resolution:** after legacy-account reconciliation is no longer needed, remove the Flutter Firebase dependencies, backend Firebase migration/verification surface, related configuration and migration-only tests. Keep Django-native auth as the sole identity path, then remove TD-002.

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
