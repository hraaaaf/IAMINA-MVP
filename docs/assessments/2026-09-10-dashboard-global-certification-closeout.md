# Dashboard global certification closeout — 2026-09-10

## Status

**ENGINEERING CERTIFICATION PARTIALLY RETAINED; FINAL RESPONSIVE VISUAL PROOF OPEN.** Backend, isolated-PostgreSQL, canonical-authority and bounded clinical-KPI evidence remain retained. Final responsive visual certification is open until `top`, `mid` and `lower` are proven pixel-distinct for each target viewport and the nine images are manually reviewed. This document records synthetic/non-patient engineering evidence only. It is not a real-patient, clinical-human, regulatory, CNDP or deployment approval.

## Goal

Converge IAMINA on one canonical Dashboard implementation and certify its responsive UI, backend wiring and bounded clinical KPI semantics without inventing continuous-CGM evidence.

## Success criteria

1. One production Dashboard authority; legacy `DashboardConvergentScreen` absent from runtime/tests.
2. Responsive evidence at 390×844, 768×1024 and 1280×900, with `top`, `mid` and `lower` captures proven pixel-distinct for every viewport.
3. Real Django backend against isolated PostgreSQL 16 with synthetic non-patient data.
4. Dashboard API contracts return successfully during browser certification.
5. Episodic glucose rows cannot be promoted to governed continuous-CGM metrics without verified coverage/provenance.
6. Browser certification has no page error, no console error and no API response >=500.

## Retained proof

- Original engineering PR: #547, merge `32e04d3de707257a1a08ff28bf6978c4a0e92bfd`.
- Dashboard global backend/clinical certification remains retained from the isolated Django + PostgreSQL 16 runs and governed-CGM tests merged in PR #547.
- Responsive visual run `34463040563` reported workflow **SUCCESS**, but decoded-pixel review later showed the tablet and desktop `top/mid/lower` captures were visually identical. File-level differences were therefore insufficient evidence. This run is **not accepted as final responsive visual proof**.
- Hardened run `34474871142` correctly failed because decoded-pixel comparison found `top/mid/lower` identical on all three viewports. Backend, responsive contracts and web build had passed before the capture gate.
- Chromium-touch run `34480403704` also correctly failed the same decoded-pixel gate, showing that synthetic wheel/touch gestures were not a reliable way to drive the Flutter `CustomScrollView` in this harness.
- Current corrective strategy uses a certification-only `PrimaryScrollController` with deterministic initial offsets from the URL; normal production Dashboard construction remains unchanged.
- Current deterministic certification head under test: `e0501cc02c880941dfd757f62d36394cd256c367`.
- Current responsive visual run: `34481354919` — pending at this document revision.
- Runtime proof already retained: Django backend + ephemeral PostgreSQL 16 service; synthetic identity/data only; no Supabase.
- Canonical Dashboard route resolves through `DashboardCompanionEntryScreen` to `DashboardPremiumScreen`.
- `frontend/lib/features/dashboard/dashboard_convergent_screen.dart` is removed.
- Dashboard tests cover latest-reading truthfulness, future-date fail-closed behavior, configured-target behavior, recorded-data KPI semantics, CGM coverage gating, trend factuality, responsive composition, action parity and navigation contracts.
- Backend governed-CGM promotion tests protect the advanced-metric authority boundary.

## Clinical truthfulness boundary

The Dashboard distinguishes recorded episodic readings from continuous-CGM metrics. A synthetic episodic dataset may produce ordinary descriptive values such as count/mean, but advanced CGM metrics remain unavailable when governed coverage is not established. This certification therefore proves fail-closed engineering behavior; it does **not** claim that synthetic episodic readings constitute valid TIR/TAR/TBR evidence.

## Visual assessment

Final visual score is **not assigned yet**. The prior 9.3/10 score is withdrawn because the retained responsive scrolling evidence was not actually distinct at decoded-pixel level. A new score may be recorded only after a corrective run proves three distinct positions for all three target viewports and those nine captures are manually inspected.

## Cleanup verification

Legacy/temporary workflow names `dashboard-global-cert.yml` and `dashboard-trend-locale-fix.yml` are absent from the merged Dashboard work. The maintained regression gates are `dashboard-global-cert-v2.yml` and `dashboard-responsive-visual-cert.yml`.

## Roadmap arithmetic

This certification is Dashboard engineering maintenance over an already-closed Dashboard workstream. It does **not** add a P5 closed lot and does not change the canonical MENA or Pilot Readiness arithmetic by itself.

## Residual boundaries

- No Vercel deployment is authorized or performed by this closeout.
- No real-patient data was used.
- Real-device, human clinical review, legal/regulatory/CNDP and production authorization remain governed by their own pilot/release gates.

## Closeout condition

Repository closeout requires final responsive visual proof, manual review of all nine captures, corrective PR/CI, merge to `main`, and post-merge verification of the merged SHA and absence of legacy Dashboard references.
