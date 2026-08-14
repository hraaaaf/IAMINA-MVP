# English baseline completeness certification — 2026-08-14

## Decision

**PASS — technical English baseline complete for the active production application surface.**

This certification is a technical localization/product-surface result. It does **not** replace the restricted native-speaker, clinical, safety-owner, privacy, CNDP, processor, deployment or pilot approvals that remain open elsewhere in the MENA roadmap.

## Certified denominator

The active application denominator is **16 patient-facing surfaces**:

- 15 explicit routed surfaces from the app router + diabetes module;
- the shared `MainShell` navigation/container surface.

All 16 have a verified English rendering path after the English-baseline remediation sequence.

**Active-surface English coverage: 16/16 = 100%.**

## What was remediated

The English-baseline sequence closed the previously verified gaps in:

- Login / signup;
- Reset Password;
- Journal date formatting;
- Import status and stale-data copy;
- Document Import errors, preview, laboratory labels, confirmation, result and loading states;
- Dashboard companion context and debug copy;
- AI Summary static UI copy while preserving backend-returned clinical content verbatim;
- global Flutter rendering-error fallback;
- iOS camera/photo permission prompts and bundle localization declarations.

A subsequent concurrent Login visual-certification merge changed the Login architecture to a FR-certified wrapper plus a MENA implementation. The MENA implementation retains the localized `AppLocalizations`/supplemental-copy path used for English and Arabic, so English coverage remains intact after that merge.

## Selection and persistence

English is explicitly selectable in onboarding. The selection flows through `LocalePreferenceService.setExperience`, is stored using the explicit locale preference keys, and is restored deterministically with explicit-user-selection precedence.

## Translation-resource parity

`frontend/test/english_language_selection_contract_test.dart` enforces identical runtime ARB key sets across:

- `app_fr.arb`;
- `app_en.arb`;
- `app_ar.arb`.

Metadata keys beginning with `@` are excluded from the runtime-key denominator.

## Regression gates

Dedicated regression contracts now protect:

- Auth English localization;
- Journal locale-aware date rendering;
- Import localization;
- Document Import localization;
- Dashboard companion-context localization;
- AI Summary static-copy localization;
- app-shell/iOS localization;
- explicit English selection, persistence and FR/EN/AR ARB parity.

## CI evidence

### English selection/parity closeout PR

- PR: **#226**
- exact pre-merge head: `cd69cfb980e9c5f07e5e188d7f7ac94b602d2734`
- pre-merge CI: **#2230 — SUCCESS**
- pre-merge migration drift: **#2042 — SUCCESS**
- diff at certification: **1 test file, +44/-0, 0 runtime**
- merge commit: `876cfacafc2374cd1e658197a3c9e03d02ebc108`

The post-merge CI/drift run on `876cfaca…` must remain green for final administrative closeout.

## Scope boundary

This PASS means:

- English is technically available across all currently active patient-facing application surfaces;
- the user can explicitly select English;
- the explicit choice is persistable/restorable;
- FR/EN/AR runtime translation-resource keys are parity-gated;
- known hardcoded-French gaps identified during the audit were remediated.

This PASS does **not** mean:

- every historical or unreachable file is translated;
- dialect-native review is complete;
- Darija safety approval is complete;
- human safety-parity approval is complete;
- real-patient pilot authorization is granted.

## Roadmap accounting

The English baseline was added as a **technical gate inside P0-MENA-2**, not as a new numbered MENA task. Closing it therefore does **not** change the explicit MENA numerator.

- MENA critical path remains **32/41 ≈ 78%**.
- P0-MENA-2 remains constrained by the three restricted human linguistic/parity approvals.

## Final technical result

**English implementation coverage: 100% (16/16 active surfaces).**

Final administrative status becomes CLOSED only after post-merge CI/drift are green and the canonical roadmap/README are synchronized to this assessment.
