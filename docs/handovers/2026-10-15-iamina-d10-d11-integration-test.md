# D10 × D11 — synthetic-only cross-branch integration proof

**Status: TEST CANDIDATE ONLY / DO NOT MERGE.** This document is an executable test plan, not an approval of D10-B or of D11 clinical release.

**Goal**: combine the latest verified D10 storage changes already on main with D11's latest zero-demo protections **without touching the draft D11 branch or deploying**. Source baseline: `main@73876eea9baca45806918d46258f813b45636fc9`, D11 snapshot: `#1021@60de80ec070157f912cb62c80a7ded1e9bde75a6`. All eleven D11 changed files are copied **byte-identical by Git blob SHA** into this isolated integration branch, retaining Android and iOS D10 protection from main.

**Observable success:** full standard GitHub PR CI (Django/PgSQL/Flutter/PWA) and independent D10/D11 Flutter selected-test workflow GREEN **on integration HEAD**. Source-level tripwires verify D11 patient/fixture restrictions and D10 lock, egress and backup controls remain present. P5 PWA browser persistence/offline/update proofs are triggered by Web/bootstrap and Drift changes. All tests use synthetic data.

**Explicit boundaries:** green source/test CI is not proof of iCloud/Android OEM restoration, encryption of browser medical vault, browser A→logout→B→A by authenticated patients or production release. D11 remains **DRAFT / UNMERGED** even if integration CI green. Never merge this integration PR into main; when D11 receives separate authorization, the owning PR must be updated to main and tested on its own final SHA, with physical and privacy gates stated honestly. No new Vercel deployment.

**D11 source snapshot:** [PR #1021](https://github.com/hraaaaf/IAMINA-MVP/pull/1021) (do not confuse its earlier Vercel lab release `9d24cff` with this newer `60de80ec`). Android D10 #1046 and iOS #1053 already merged on main; simulator incident #1057 and Web #1054 remain OPEN.

**Next:** inspect exact workflows and artifacts; if any fail, diagnose and correct *only this isolated test branch* without affecting D11 source unless coordination explicitly changes the owned D11 PR. Reconcile contradictions into D10 handover after CI evidence. P5 global remains historical 50%.
