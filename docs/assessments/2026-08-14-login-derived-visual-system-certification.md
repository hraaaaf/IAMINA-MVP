# LOGIN-derived visual system certification — 2026-08-14

## Scope

Final certification of the LOGIN-derived visual language across the active representative patient-facing mobile surface set, using both deterministic native Flutter capture and real Chrome 390×844 rendering. The final acceptance bar is the stricter 10/10 visual standard established after the initial shared-theme rebase, including removal of visible legacy branding in favor of the certified `assets/images/logo_amina.png` asset.

## Evolution of the implementation

- PR #229 — `UI: certify LOGIN-derived visual system across patient surfaces`: shared visual-language foundation, theme harmonization and reusable UI primitives.
- PR #231 — `UI: drive patient surfaces to global 10/10 parity`: premium Dashboard and Companion surfaces, logo propagation, additional patient-surface polish, and isolated real-browser certification infrastructure.
- PR #233 — `UI: finish premium branding on focused patient tasks`: final Add Log and Document Import visual gaps closed without changing their clinical/data behavior.
- Final production merge commit: `ee7766ef2ac563ac92d12ec831f362701c12c372`.

The certified visual implementation uses `frontend/lib/core/theme/amina_visual_language.dart`, the shared patient-facing primitives, premium active routes, and the canonical `assets/images/logo_amina.png` branding. The former mobile Dashboard legacy seal painter is no longer on the active rendered path.

## Certified mobile surface set

Real Chrome viewport 390×844:

- Dashboard
- Journal
- Summary
- Profile
- Import
- Document Import
- Companion
- Add Log
- Medications
- Reminders

The real Chrome set was inspected page by page after the final Add Log and Document Import polish. No known visual rupture remains in this certified 10-view scope relative to the LOGIN-derived mint / paper / forest visual language.

## Final pre-merge evidence

Exact PR #233 head `fdb945b8f4d3459723a435535341add57aa6916e`:

- CI #2372: PASS
- Django migration drift #2184: PASS
- UI screenshot audit #54: PASS
- UI browser screenshot certification #13: PASS
- Browser artifact ID: `9231164649`
- Browser artifact digest: `sha256:0847cb6460fa9e8efb701b849026260ebe0b857112c44d3fe6473922e172630a`

Visual inspection of the 10 real Chrome 390×844 captures confirmed the final premium treatment, including the corrected Add Log and Document Import surfaces and the certified new logo treatment.

## Final post-merge evidence

Exact `main` merge commit `ee7766ef2ac563ac92d12ec831f362701c12c372`:

- CI #2375: PASS
- Django migration drift #2187: PASS
- UI screenshot audit #55: PASS
- UI browser screenshot certification #14: PASS
- Native artifact ID: `9235057255`
- Native artifact digest: `sha256:eed1b08160cfe4da856074526471aa5ac4aecfcbcd3d78388c857510d9bddeaa`
- Browser artifact ID: `9235423032`
- Browser artifact digest: `sha256:e05a633d8e459b5fcc494e0361046ce706f0ecad01ebd037ed1b6c9fa00931dd`

These post-merge workflows ran on the exact final production merge commit.

## Logo acceptance

Active premium patient surfaces are contractually tied to the certified `assets/images/logo_amina.png` asset where branding is rendered. Dashboard, Companion, the shared mobile header, Add Log and Document Import premium presentation paths are covered by structural contracts so the legacy active branding cannot silently reappear without failing tests.

## Certification infrastructure

Two complementary layers are retained:

1. Native Flutter screenshot audit for deterministic structure, composition and representative responsive surfaces.
2. Isolated real Chrome/CDP 390×844 certification for final typography, image/logo rendering and browser-level visual inspection.

The browser harness is isolated in `frontend/lib/ui_browser_audit_main.dart`; production `frontend/lib/main.dart` does not seed demo data or import the audit harness. The browser workflow fails closed on suspiciously small or insufficiently distinct renders.

## Safety boundary

The final visual lot does not alter backend authority, clinical calculations, thresholds, medication logic, consent rules, authentication semantics or production persistence. The Add Log and Document Import finishing changes are presentation/routing wrappers around the existing functional surfaces.

## Roadmap impact

No MENA critical-path numerator changes. The UX visual lane remains 100% closed, now supported by the stricter final real-browser certification rather than the earlier shared-theme evidence alone.

## Closeout

- PR #229: merged, foundational visual-system certification.
- PR #231: merged, premium global rework and real-browser certification infrastructure.
- PR #233: merged, final focused polish.
- Final production merge: `ee7766ef2ac563ac92d12ec831f362701c12c372`.
- Final result: requested 10/10 visual gate reached for the certified 10-view mobile patient-facing scope, with pre-merge and post-merge CI, migration drift, native screenshot audit and real Chrome certification all passing.
