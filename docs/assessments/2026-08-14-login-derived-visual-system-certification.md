# LOGIN-derived visual system certification — 2026-08-14

## Scope

Certification of the LOGIN-derived visual language propagated across patient-facing Flutter surfaces through the shared Material theme and reusable UI primitives.

## Certified implementation

- PR: #229 — `UI: certify LOGIN-derived visual system across patient surfaces`
- Merge commit: `c3e0391953dcdee40ea7af04c4cd5ada0b5cb769`
- Shared visual language: `frontend/lib/core/theme/amina_visual_language.dart`
- Root theme harmonization applied in `frontend/lib/main.dart`
- Shared cards, buttons, text fields, first-use states and mobile headers aligned with the certified visual language.
- Mobile IAmina companion entry CTA aligned with the LOGIN control language.

## Pre-merge evidence

Exact head `11e1b4cb88a2c787a60e90f9bbf05f8037ee4d86`:

- CI #2297: PASS
- Django migration drift #2109: PASS
- UI screenshot audit #26: PASS
- 14 deterministic native Flutter screenshots produced from real production widgets using `NativeDatabase.memory()`.

Certified viewport set:

- 390×844: Dashboard, Journal, Summary, Profile, Import, Document Import, Companion, Add Log, Medications, Reminders.
- 1440×1000: Dashboard, Journal, Import, Profile.

## Post-merge evidence

Exact `main` merge commit `c3e0391953dcdee40ea7af04c4cd5ada0b5cb769`:

- CI #2298: PASS
- Django migration drift #2110: PASS
- UI screenshot audit #27: PASS
- 14/14 post-merge screenshots present.
- Every post-merge screenshot SHA-256 matches its pre-merge certified counterpart exactly; no visual drift was introduced by merge.

## Safety boundary

This lot is presentation-only. It does not change authentication, routing semantics, production persistence, clinical calculations, thresholds, medication logic, provider behavior or backend authority.

The visual audit is isolated from production runtime. Golden data is created only inside the dedicated Flutter test path with an in-memory database and the `IAMINA_VISUAL_AUDIT=true` compile-time flag.

## Roadmap impact

No MENA critical-path numerator changes. The canonical roadmap already records the UX visual lane as 100% closed; this certification strengthens and extends its evidence without reopening or incrementing that completed lane.

## Closeout

- PR #229: merged and post-merge certified.
- PR #227: closed as superseded.
- Result: LOGIN-derived visual system globally certified across the representative patient-facing surface set above.
