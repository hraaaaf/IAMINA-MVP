# HANDOVER — IAMINA P5-4A AUTH LOCAL-FIRST + TD-014 STRONG LOCAL APP-LOCK

Date: 2026-09-16
Repository: `hraaaaf/IAMINA-MVP`
Purpose: canonical resume point for a new conversation. Read this file first, then re-verify live GitHub state before changing anything.

## 1. Operating constraints

- Patient/clinical runtime is local-first.
- Vercel / Django / Neon are DEV/integration/certification infrastructure, not required patient runtime dependencies.
- No Vercel deployment without explicit owner authorization.
- No merge without explicit owner authorization.
- Real-patient release remains `NOT_RELEASE_AUTHORIZED`.
- Firebase migration remains disabled by default.
- Remote account features are optional and must never be required for ordinary local reopen/use.
- `docs/QUALITY_SCORING_POLICY.md` is mandatory.

Quality scoring rules:
- every material step gets `EXECUTION_SCORE /10` and `ADVERSARIAL_SCORE /10`;
- retained score = lower score, never average;
- gap > 0.5 requires investigation;
- 10/10 exceptional;
- 9.5+ requires real independent review;
- same agent doing execution + adversarial review => retained score capped at 9.4/10;
- required red test or missing required proof => max 7.9/10;
- observed regression => max 6.9/10;
- security/privacy/data/clinical-claim blocker => max 5.9/10 + `BLOCKED`;
- UI without real Target <-> Render comparison => visual fidelity max 7.5/10;
- no critical bad dimension may be hidden by averaging;
- lot can be `VERIFIED` only if retained score >= 9.0 and every binary gate is green;
- after >=9.2, mandatory final Perfection Pass still applies.

## 2. Current main

Latest verified `main` at handover creation:

`c9f1046689af1f8e7173929e93f1f6025e205b1d`

Latest main change:

`TD-012 follow-up: decompose Add Log surface (#652)`

Parent was `fc9259e87120226344d441c04a13797bfc5b9d25`.

Important consequence: P5-4A PR #639 was recertified green on a prior main snapshot, but `main` advanced again afterward. Never treat its old exact-head proof as sufficient for merge without reconciling #652 and rerunning exact-head proof.

## 3. P5-4A — PR #639

PR: `#639` — `fix(auth): restore local-first offline reopen boundary`
Branch: `fix/auth-local-first-boundary-20260915`
Current handover head: `d30338dd68b7106ca57f771fc6c050cb376e701e`
PR state at last verification: OPEN, DRAFT, mergeable at that moment.

Purpose:
- first local enrollment without required network;
- reopen without `/api/v1/auth/me` boot dependency;
- local enrollment marker separate from remote bearer;
- remote bearer revocation/expiry must not erase local enrollment;
- remote account registration disabled by default;
- Firebase migration disabled by default;
- secure persistence must succeed before authenticated in-memory state becomes visible;
- TD-012 safe fallback observability retained without reintroducing boot network.

Files/scope on the recertified candidate were 12 files.

### Exact-head proof already obtained on `d30338dd...`

All these workflows were SUCCESS:
- CI `#4378`
- Auth local-first visual certification `#19`
- P5-5 End-to-End Pilot Rehearsal `#208`
- CGM onboarding browser certification `#120`
- UI global missing routes certification `#104`
- UI browser screenshot certification `#791`
- Pilot mobile packaging `#113`
- Pilot iOS packaging `#91`

These proofs are real but historical after `main` advanced to `c9f10466...`.

### Current required action for #639

1. Re-read current `main@c9f10466...` and compare against `d30338dd...`.
2. Rebase/reconstruct #639 on exact current main while preserving #652 Add Log decomposition and all current-main governance/TD-012 work.
3. Do not reintroduce `/auth/me` at boot.
4. Preserve TD-012 safe failure observability.
5. Verify compare is `behind=0` and scope contains only intended P5-4A deltas over current main.
6. Rerun exact-head CI + auth visual + relevant pilot/browser gates.
7. Apply scoring policy + Perfection Pass.
8. Only after all gates green and retained score >=9.0 may #639 be called VERIFIED.
9. Merge only after explicit owner approval.

## 4. TD-014 — PR #649

Tracker: `#647`
PR: `#649` — `feat(auth): add strong local WebAuthn app-lock`
Branch: `fix/td014-local-app-lock-20260916`
Current handover head: `f6f15ce90248666e4999815fb40d80f919ba17ba`
Current PR is intentionally stacked on #639 and remains DRAFT.

### Security architecture implemented

- Web/PWA strong local re-authentication uses WebAuthn platform authenticator.
- `userVerification: required`.
- No IAMINA-owned weak PIN/password patient fallback.
- No biometric material enters IAMINA.
- Enrollment stores opaque credential ID, public SPKI, RP/origin binding and signature counter.
- Assertions validate locally: challenge, exact origin, RP-ID hash, UP/UV flags, credential ID, ES256 signature, counter rollback.
- Cold boot locks after configuration.
- 60-second background grace, then automatic relock; detached locks immediately.
- Explicit auth sign-out locks app-lock in-process.
- Unsupported/insecure strong auth has no patient bypass.
- App-lock path does not require Vercel/Django/Neon/Firebase/SMTP.

### Rollback hardening added during Perfection Pass

A real weakness was identified and fixed:
- if app-lock secure keys disappear while protected local state remains, IAMINA must NOT treat the device as a fresh installation;
- existing local enrollment or local clinical data => missing app-lock keys routes to fail-closed recovery;
- protected-state probe failure also routes fail-closed to recovery;
- no new DB table/migration was needed;
- wiring checks cover the relevant local clinical tables.

### Exact-head proof already obtained on `f6f15ce...`

SUCCESS:
- TD-014 local app-lock certification `#9`
- UI geometry golden audit `#756`
- UI global missing routes `#103`
- CGM onboarding browser `#119`
- UI browser screenshot `#788`

The dedicated TD-014 workflow proves the strong local AppLock path, including browser WebAuthn/offline behavior and visual evidence for its then-current stacked base.

### Important limitation / non-claim

TD-014 protects application access. It does NOT prove application-layer encryption of the Drift clinical DB at rest. Current Drift persistence was previously observed without explicit application-layer DB encryption. Keep that as a separate security/data-at-rest concern; do not falsely close it through TD-014.

Recovery is intentionally fail-closed. Operational recovery UX/process may still require a separate future lot; never add a weak bypass to make recovery convenient.

## 5. TD-014 rebase state at handover

Rebase/reconstruction onto the latest clean #639 candidate was STARTED but NOT COMPLETED before this handover.

Verified clean TD-014 delta from historical P5-4A base `f151702a...` to `f6f15ce...` = 22 files.

Important discovery:
- `frontend/lib/services/auth_service.dart` is NOT a functional TD-014 delta that should be overlaid during the rebase;
- keep the #639/current-main AuthService entirely, including TD-012 observability and zero-network boot behavior;
- do not let old TD-014 ancestry reintroduce an obsolete AuthService.

The 22-file TD-014-specific delta includes the dedicated workflow, app-lock service/authenticator/web bridge, setup/unlock UI, routing/main wiring, tests, docs and visual/browser cert tooling.

The old PR #649 ancestry is divergent and must not be used as-is for final certification.

## 6. Required continuation sequence

Critical path:

A. Reconcile #639 on current main `c9f10466...`.
B. Verify `behind=0`, intended diff only.
C. Rerun all required #639 exact-head gates.
D. Security/adversarial review + scoring + Perfection Pass.
E. If VERIFIED, STOP at human gate and request explicit merge approval for #639.
F. After owner says merge: merge with expected-head lock, verify main contains merge, check post-merge CI once and perform closeout work while CI runs.
G. Rebase/reconstruct #649 TD-014 onto the merged/current main, applying ONLY the TD-014-specific delta and preserving the final #639 AuthService.
H. Verify `behind=0`, no ancestry pollution, no TD-012 regression.
I. Rerun TD-014 dedicated workflow + relevant full-main CI/browser/mobile gates on exact final HEAD.
J. Inspect actual visual artifact Target <-> Render at 390x844 / 768x1024 / 1280x900; no visual score >7.5 without this proof.
K. Final Security review, EXECUTION_SCORE, ADVERSARIAL_SCORE, retained score, Perfection Pass.
L. If VERIFIED, STOP at human gate and request explicit merge approval for #649.
M. Merge/post-merge closeout only after explicit approval.
N. No Vercel deploy unless separately explicitly authorized.

## 7. Scoring status at handover

Do NOT inherit a final VERIFIED score into the new conversation.

Reason:
- #639 has strong green proof on `d30338dd...`, but `main` advanced afterward;
- #649 has strong green proof on `f6f15ce...`, but final rebase onto the eventual #639/current-main result is not complete.

Therefore both lots require new exact-head retained scoring after their final reconciled HEADs exist.

## 8. Canon / roadmap caution

`docs/ROADMAP.md` remains the canonical forward tracker, but always re-read it from current main because parallel TD-012 work is advancing it.

Do not overwrite newer roadmap/techdebt updates with stale branch copies during reconstruction.

Global progress must only be changed from the value actually present and justified on current main. Do not invent or infer a new percentage from old conversation state.

## 9. New-conversation initiation prompt

Paste this as the first message in the new conversation:

> IAMINA — reprise P5-4A + TD-014.\n>\n> Lis d'abord `docs/handovers/2026-09-16-p5-4a-td014-resume-handover.md` depuis la branche `docs/handover-p5-4a-td014-20260916`. Ensuite vérifie LIVE, dans cet ordre : `main`, PR #639, PR #649, HEADs, compare ahead/behind, CI/workflows et `docs/ROADMAP.md`. Ne considère aucun SHA/CI du handover comme encore actuel sans vérification.\n>\n> Goal immédiat : remettre #639 sur le `main` courant sans perdre les derniers travaux TD-012/gouvernance, conserver zéro réseau au boot et l'observabilité sûre, puis recertifier exact-head. Ensuite seulement rebaser/reconstruire TD-014 #649 avec son delta propre, en conservant intégralement l'AuthService final de #639, puis recertifier WebAuthn/offline/rollback/visuel.\n>\n> Applique strictement `docs/QUALITY_SCORING_POLICY.md` : EXECUTION_SCORE + ADVERSARIAL_SCORE, score retenu=min, caps, VERIFIED >=9.0 avec tous gates verts, Perfection Pass obligatoire.\n>\n> N'effectue aucun merge sans mon accord explicite. Aucun déploiement Vercel sans mon accord explicite. Ne t'arrête pas sur une CI en cours s'il reste du travail indépendant.\n>\n> Continue de façon autonome jusqu'au prochain vrai human gate. Format de suivi : Résultat -> preuve -> prochaine action + REPÈRES.

## 10. Resume invariant

The first action in the next conversation is NOT to code. It is to verify current truth against GitHub because `main` is moving in parallel.

Only then continue the critical path above.
