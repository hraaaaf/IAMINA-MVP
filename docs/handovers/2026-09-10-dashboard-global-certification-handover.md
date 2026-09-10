# IAMINA Dashboard global certification — handover 2026-09-10

## Canonical forward tracker

`docs/ROADMAP.md`

This file is a handover snapshot only. The roadmap remains the single forward tracker. Historical detail belongs in git, assessments and this handover.

## Goal

Close the Dashboard global certification with one canonical Dashboard authority, truthful bounded clinical KPI semantics, real Django + isolated PostgreSQL engineering proof, and nine genuinely distinct responsive captures at 390×844, 768×1024 and 1280×900.

Success requires all of the following:

- canonical route resolves through `DashboardCompanionEntryScreen` → `DashboardPremiumScreen`;
- no legacy `DashboardConvergentScreen` runtime/test authority;
- Django backend + ephemeral PostgreSQL 16 with synthetic non-patient data;
- governed CGM metrics remain fail-closed without verified CGM coverage/provenance;
- no browser page error, no backend 5xx during visual certification;
- mobile/tablet/desktop each produce distinct `top`, `mid`, `lower` captures proven at decoded-pixel level;
- all nine captures are manually reviewed before assigning a final visual score;
- corrective PR is merged to `main`, then post-merge HEAD/CI is verified.

## Retained verified work

Original Dashboard engineering work is already merged through PR #547, merge `32e04d3de707257a1a08ff28bf6978c4a0e92bfd`.

Retained evidence:

- canonical Dashboard authority established;
- legacy `dashboard_convergent_screen.dart` removed;
- sidebar large-screen Firebase dependency corrected to use injected `AuthService` authority;
- dashboard trend changed to discrete recorded points instead of inferred continuous trajectory;
- governed CGM promotion tests retained on PostgreSQL;
- prior global certification run `34481354921` was SUCCESS and retains backend/clinical/build proof for that exact head;
- no Supabase is used for this certification;
- no real-patient data is used;
- no Vercel deployment is authorized or performed.

## Visual-proof history and why earlier greens are not accepted

- `34463040563`: workflow SUCCESS, but tablet and desktop `top/mid/lower` decoded to identical pixels. Not accepted as final visual proof.
- `34474871142`: strict pixel gate correctly FAILED because captures were identical.
- `34480403704`: CDP/touch strategy also FAILED the pixel gate.
- `34481354919`: deterministic PrimaryScrollController strategy still FAILED to produce distinct positions.
- `34526781524`: did not actually test the intended explicit-scroll product commit because the run checked out an earlier SHA.
- a concurrent branch write then overwrote the branch ref, so the explicit-scroll commit had to be reconciled manually.
- `34529968045`: exact-head run included explicit `ScrollController` wiring and 13/13 responsive/truthfulness tests, backend and build all green, but `top/mid/lower` remained pixel-identical because `initialScrollOffset` was applied before the full asynchronous Dashboard content established its final scroll extent.

## Current technical state

Testing branch: `audit/dashboard-global-cert-20260909`

Latest technical HEAD at handover: `479daae86c9b0c568445390a5530a848d2549b14`

Important commits immediately before it:

- `2244f4fcb180ede5ad6f53914a060f7135ade8cb` — certification entrypoint changed to re-apply the target offset after layout using `ScrollController.hasClients`, `position.maxScrollExtent` and `jumpTo()`.
- `479daae86c9b0c568445390a5530a848d2549b14` — responsive contract updated to match that post-layout jump strategy.

Latest visual run at handover:

- run `34534206725`
- workflow `Dashboard responsive visual certification`
- head `479daae86c9b0c568445390a5530a848d2549b14`
- state at handover: `IN_PROGRESS`

The immediately previous exact-head run pair on `2244f4fc...` failed before visual capture because one static contract still expected the obsolete source string `initialScrollOffset: _certScrollOffsetFromUri()`. That was a test-contract mismatch, not a product/backend failure. Backend probes and governed CGM steps were green before that contract failure.

## Clean closeout branch

Do NOT merge the long-lived audit branch directly. It diverged heavily from `main` because the main Dashboard work had already been merged elsewhere.

Clean corrective branch created from current `main`:

`fix/dashboard-visual-cert-evidence-20260910`

Current known HEAD before this handover commit:

`b67d292cd34c6b27c278a56598b09918f0e8b0b6`

It already contains the correction that withdraws the premature 9.3/10 visual claim in:

`docs/assessments/2026-09-10-dashboard-global-certification-closeout.md`

The technical delta proven on the audit branch must be ported/cherry-picked or recreated cleanly onto this corrective branch only after the strict visual run is actually green and the nine images are manually reviewed.

## Current visual implementation under test

Production-safe wiring:

- `DashboardPremiumScreen` accepts optional `ScrollController?`;
- `DashboardCompanionEntryScreen` forwards optional `ScrollController?`;
- normal production route constructs `const DashboardCompanionEntryScreen()` and therefore keeps `controller == null`;
- certification-only entrypoint creates the controller and passes it explicitly;
- certification URL accepts `?scroll=<offset>`;
- current entrypoint re-applies the requested offset after content layout using `jumpTo()` once a sufficient `maxScrollExtent` exists;
- pixel guard uses Pillow `ImageChops.difference(...).getbbox()` and fails if any pair of `top/mid/lower` is identical.

Target offsets generated by `tools/dashboard_capture.js`:

- top = 0;
- mid ≈ 0.55 × viewport height;
- lower ≈ 1.10 × viewport height.

## Mandatory visual closeout cycle

BEFORE evidence already exists from meaningful Dashboard captures, but final AFTER is not certified yet.

For the final pass:

1. Check run `34534206725` once.
2. If FAILURE, inspect exact failing step/log; do not assume product failure.
3. If SUCCESS, fetch artifact `iamina-dashboard-responsive-visual-cert`.
4. Inspect `browser-report.json`.
5. Confirm 9 PNGs exist for 390×844, 768×1024 and 1280×900.
6. Confirm `top/mid/lower` are pixel-distinct for each viewport.
7. Manually inspect all nine captures.
8. Compare TARGET ↔ AFTER on the same viewports.
9. Give an expert UX/UI review and score only from observed proof.
10. Do not restore 9.3/10 or any >=9 score unless the nine-image evidence supports it.

## Expert-reference requirement

For significant Dashboard passages, include an expert-level review without pretending a real human expert was consulted, plus at least two serious external references.

Current primary Flutter references:

- https://api.flutter.dev/flutter/widgets/CustomScrollView-class.html
- https://api.flutter.dev/flutter/widgets/ScrollController-class.html
- https://api.flutter.dev/flutter/widgets/ScrollController/jumpTo.html
- https://docs.flutter.dev/ui/adaptive-responsive/large-screens
- https://docs.flutter.dev/ui/adaptive-responsive/general

Clinical primary references used for CGM semantics:

- ADA Standards of Care 2026, Section 6: https://diabetesjournals.org/care/article/49/Supplement_1/S132/163927/6-Glycemic-Goals-Hypoglycemia-and-Hyperglycemic
- International Consensus on Time in Range: https://diabetesjournals.org/care/article/42/8/1593/36184/Clinical-Targets-for-Continuous-Glucose-Monitoring

## Known clinical truth boundary

IAMINA currently keeps ordinary recorded episodic data separate from normative continuous-CGM metrics. TIR/TAR/TBR/CV are promoted only when governed CGM coverage is verified. GMI/GRI remain fail-closed under the current evidence registry. This Dashboard certification is synthetic engineering evidence, not clinical-human approval or real-patient authorization.

## Exact next action

Check visual run `34534206725` once.

If green: artifact → decoded-pixel 9/9 verification → manual nine-image review → expert score → port only the proven technical delta onto `fix/dashboard-visual-cert-evidence-20260910` → update assessment/roadmap truthfully → PR → CI → merge → post-merge verification.

If red: inspect the exact failure and fix only that cause; no further wheel/touch/PrimaryScrollController experiments unless new evidence specifically warrants them.

## Remaining sequence

`visual run → artifact → 9/9 pixel proof → manual review → expert score → clean corrective branch → docs/ROADMAP.md + assessment consistency → PR → CI → merge → post-merge HEAD/CI → close Dashboard global certification`

## Current progress statement

Dashboard engineering/backend/clinical certification is substantially retained, but the global Dashboard certification remains OPEN because final responsive visual proof has not yet been demonstrated. Do not assign a final completion percentage from this handover alone.
