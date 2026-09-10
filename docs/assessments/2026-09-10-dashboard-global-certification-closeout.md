# Dashboard global certification closeout — 2026-09-10

## Status

**BRANCH ENGINEERING CERTIFICATION IN PROGRESS.** Backend, isolated-PostgreSQL, canonical-authority and bounded clinical-KPI engineering evidence are retained. Final responsive visual certification remains open until three genuinely pixel-distinct captures are proven for each target viewport. This document records synthetic/non-patient engineering evidence only. It is not a real-patient, clinical-human, regulatory, CNDP or deployment approval.

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

- Audited branch: `audit/dashboard-global-cert-20260909`.
- Backend/clinical/browser baseline head: `a19883da787b8a7439ff3baeef44fcd9df7e67b9`.
- Dashboard responsive visual run `34463040563` — workflow **SUCCESS**, but its byte-level duplicate check was insufficient: decoded-pixel review showed mobile `top/mid/lower` distinct while tablet and desktop `top/mid/lower` were pixel-identical. This run is therefore **not accepted as final responsive visual proof**.
- Corrective visual-cert head: `f6c92c01c09c800374065f21bebbaff04b593d94`.
- Corrective run: `34474871142` — final result pending at this document revision.
- Corrective harness moves wheel input away from the interactive trend-chart region and adds decoded-pixel duplicate rejection with Pillow.
- Runtime proof already retained: Django backend + ephemeral PostgreSQL 16 service; synthetic identity/data only; no Supabase.
- Canonical Dashboard route resolves through `DashboardCompanionEntryScreen` to `DashboardPremiumScreen`.
- `frontend/lib/features/dashboard/dashboard_convergent_screen.dart` removed.
- Dashboard tests cover latest-reading truthfulness, future-date fail-closed behavior, configured-target behavior, recorded-data KPI semantics, CGM coverage gating, trend factuality, responsive composition, action parity and navigation contracts.
- Backend governed-CGM promotion tests protect the advanced-metric authority boundary.

## Clinical truthfulness boundary

The Dashboard distinguishes recorded episodic readings from continuous-CGM metrics. A synthetic episodic dataset may produce ordinary descriptive values such as count/mean, but advanced CGM metrics remain unavailable when governed coverage is not established. This certification therefore proves fail-closed engineering behavior; it does **not** claim that synthetic episodic readings constitute valid TIR/TAR/TBR evidence.

## Visual assessment

Final visual score is **not assigned yet**. The prior 9.3/10 score is withdrawn because tablet and desktop scrolling evidence was not actually distinct at decoded-pixel level. A new score may be recorded only after run `34474871142` or a later corrective run proves three distinct visual positions for all three target viewports and those nine captures are manually inspected.

## Cleanup verification

Legacy/temporary workflow names `dashboard-global-cert.yml` and `dashboard-trend-locale-fix.yml` are absent from the audited branch. The maintained regression gates are `dashboard-global-cert-v2.yml` and `dashboard-responsive-visual-cert.yml`.

## Roadmap arithmetic

This certification is Dashboard engineering maintenance over an already-closed Dashboard workstream. It does **not** add a P5 closed lot and does not change the canonical `32/38` MENA arithmetic or `2/9` Pilot Readiness arithmetic by itself.

## Residual boundaries

- No Vercel deployment is authorized or performed by this closeout.
- No real-patient data was used.
- Real-device, human clinical review, legal/regulatory/CNDP and production authorization remain governed by their own pilot/release gates.

## Closeout condition

This branch-level certification becomes repository closeout only after final responsive visual proof, manual review of all nine captures, PR review/CI, merge to `main`, and post-merge verification of the merged SHA and absence of legacy Dashboard references.
