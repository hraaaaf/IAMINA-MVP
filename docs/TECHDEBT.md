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

## TD-012 — Oversized Flutter surfaces remain

- **Area:** Frontend maintainability
- **Priority:** Medium; functional error-boundary debt is paid before cosmetic decomposition
- **Resolved foundation:** pilot-critical journal synchronization preserves explicit failure state and sanitized observability; malformed local meal JSON uses typed fallbacks; journal `ApiClient` synchronization distinguishes ordinary server non-confirmation from technical/parsing failures through a typed, payload-minimized error contract. `AuthService` initialization, Firebase-instance fallback, native-token validation and remote logout catches emit sanitized operation/error-type observability while preserving fail-closed/local-cleanup behavior. Companion overview, proactive-preview and next-action read exceptions also emit sanitized observability while preserving their existing `null` fallback contract; the chat path keeps its typed provider failures. The Dashboard trend hotspot is split into orchestration/state (`dashboard_trend_section.dart`) and presentation/interaction (`dashboard_trend_view.dart`) while retaining the existing painter, queries, calculations, copy and visual geometry. The Add Log hotspot is split into domain/state/persistence orchestration (`add_log_sheet.dart`) and presentation (`add_log_view.dart`) while preserving glucose thresholds and mmol/L conversion, Ramadan/meal admissibility, Drift persistence wiring, navigation, copy and responsive geometry.
- **Current compromise:** other large Flutter widgets/services remain from rapid iteration; TD-012 therefore stays open after the Dashboard trend and Add Log splits.
- **Risk:** oversized remaining surfaces increase regression cost and make isolated maintenance harder.
- **Resolution:** continue decomposing oversized Flutter widgets/services in separate focused, behavior-preserving PRs with targeted regression tests and visual evidence where UI surfaces are touched.

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
