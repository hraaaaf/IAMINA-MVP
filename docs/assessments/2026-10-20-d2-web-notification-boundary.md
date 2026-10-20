# IAMINA D2 Web/PWA — safe notification boundaries (candidate)

Date: 2026-10-20
PR: #1135 (DRAFT). Base: main@31380a7f4c8f61a3ec886ec9d2d66d26c2bf222b.
Status: **CONTRACT-ONLY / NO NOTIFICATION DELIVERY / NOT CERTIFIED**.

## Goal, success and proof

- **Goal**: keep reminders, IAmina conversation and governed proactive in-app observations separate. Do not simulate push delivery or allow unsolicited medical notifications.
- **Success for this sublot**: typed, fail-closed preview eligibility decisions; missing consent and patient-scope mismatch deny; browser push always disabled.
- **Proof required**: focused Flutter tests + complete exact-HEAD CI and browser regressions. A green CI does **not** prove a patient notification feature.

## Existing verified state

- `frontend/lib/features/reminders/reminders_screen.dart` stores user-authored reminders with Drift. OS notifications are explicitly unavailable.
- `backend/diabetes/api/v1/proactive.py` provides a read-only GET preview and state-changing POST evaluation. Neither provides browser/OS push.
- `backend/diabetes/services/clinical/proactive_intelligence.py` owns the existing **one non-urgent observation per 24 hours** budget. This is **not** an emergency threshold or a right to contact the patient.
- `frontend/lib/services/consent_service.dart` governs existing AI consent. It is **not** a verified D2 category-specific notification consent.
- Web patient/consent persistence and real-patient W01 Preview are not certified. W01 NO-GO / W02 frozen.

## New candidate technical boundary

`frontend/lib/services/d2_notification_policy.dart` separates:
1. **Reminder** — user-authored and stored locally. Never inferred as push delivery.
2. **In-app notification preview** — only a sourced, non-urgent proactive candidate can pass the dry-run gate.
3. **Companion conversation** — not a system notification or reminder.

Every candidate must have stable patient identity/epoch, unlocked state, explicit proactive opt-in **and** independently confirmed server consent, evidence ID and exact governed source version, nonexpired evidence, no treatment/emergency authority, no duplicate signature and the existing 24-hour attention rule. Missing/unknown inputs fail closed.

**Even a preview-eligible result is not a dispatch authorization.** `browserPushAvailable` is hard-disabled. The engine has **no runtime consumer**, storage schema, OS permission request, service worker, network action, scheduling, inbox state, clinical threshold, or LLM call. Test fixtures simulate consent only to prove reject/accept logic; they **do not** constitute real patient approval.

## Remaining sequence / human gates

1. Obtain W01-compliant authenticated Web identity and patient-scoped persistence with proven A→B→A isolation and revocation.
2. Implement server-authoritative D2 preferences default OFF: category-specific opt-in/out, auditable consent receipt, no cross-patient reads/writes, no PHI on lock-screen notifications.
3. Create a genuine inbox only for authenticated source-bound events; honor metadata retention, deletion, replay/idempotency, offline and stale-data constraints. Do not create a decorative inbox.
4. Produce BEFORE → goal → mockup → AFTER at the same FR/EN/AR and RTL mobile/tablet/desktop viewports, including empty, disabled and opted-out states.
5. Independent UX, clinical safety, privacy/security reviews and exact-HEAD CI. Qualified regulatory/clinical human authorization is a gate for actual medical push.
6. No merge or Vercel deployment without project release gates and explicit deployment authorization.

D1 remains deferred; D3 starts only after the D2 scope is genuinely concluded or transparently blocked.

## Visual D2 CTA correction — BEFORE / Goal / reference (written pre-implementation)

BEFORE: real Chrome artifacts [390×844](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39436913086/artifacts/12271632356), [768×1024](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39436913086/artifacts/12271557631), [1280×900](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39436913086/artifacts/12272382552) from run #39436913086 and source-equivalent `6fc5375c`. Actual mobile + tablet PNGs inspected. The 'Ajouter le rappel' CTA still used `Icons.add_alert_outlined` (bell).
Goal: stop implying OS alert delivery while preserving the real user-authored local save flow.
Reference/mockup: keep existing 48px dark green `FilledButton.icon`, text, accessible layout, timing and handler; replace only bell glyph with `Icons.add_rounded` (simple plus).
AFTER: **not yet visually inspected** on the new HEAD. Require Chrome screenshots at identical 390/768/1280 viewports, compare CTA region, contrast, text, RTL and keyboard behavior before claiming UX certification. Different fixture values and clocks must not be misinterpreted as UI regressions.

## D2 Web consent-only backend sublot (candidate, 20 Oct 2026)

**Goal**: own non-urgent in-app preview preference OFF by default, revocable and patient-scoped, distinct from global AI consent. **NOT permission to notify.**
**Implementation**: `D2PreviewConsentReceipt` append-by-grant evidence, unique active receipt per patient with hashed FR/EN/AR notice, bound to exact valid global AI consent epoch; core migration `0020`; protected `GET/PUT/DELETE /api/v1/account/notification-preview-consent`; global AI withdrawal or renewal revokes D2. Returned `delivery_enabled=false` and `browser_push_enabled=false` always, even if opted_in. No UI, browser push, inbox, messaging producer, dispatch or medication decision.
**Proof targets**: Django tests `backend/core/tests/test_d2_preview_consent.py` cover anonymous deny, missing consent, wrong notice/hash, unknown caller fields, idempotency, A/B isolation, revocation, global reconsent and locale aliases. Exact-head Django SQLite/PostgreSQL/drift/Flutter CI required. Clinical + privacy human gates, W01 session safety and true user-facing rendered notice remain OPEN.


## 2026-10-20 — D2 security: cookie CSRF regression on exact CI HEAD

**Goal** : un patient connecté par cookie Django ne peut pas activer/révoquer le consentement D2 Preview avec une mutation `PUT/DELETE` sans jeton CSRF Django valide ; les requêtes cross-origin et les requêtes mixtes cookie+Bearer doivent échouer sans écrire de reçu. Aucun browser push ni livraison de notification.

**Échec BEFORE reproduit CI exact `7b1fc0b96d0b74f47506a58604cf00738d8b0676` :** workflow CI #39460086330, jobs Backend SQLite `118768168771` (2874 tests PASS, un FAIL) et PostgreSQL `118768168694` (2878 PASS, un FAIL) : `D2PreviewConsentTests.test_cookie_session_mutations_enforce_csrf_token_and_origin`, attendu 403, reçu **200** dès premier `PUT` avec cookie/session valide et **sans CSRF**. **Impact candidat important :** opt-in D2 involontaire possible sur ce parcours tant que les préconditions globales sont réunies ; pas de preuve d'exploitation réelle ni de notification externe. La route Django-Ninja peut ignorer le middleware Django CSRF standard sur ses vues `csrf_exempt`. Ne jamais supprimer le test.

**Correctif code candidat, non certifié :** `backend/core/api/v1/d2_preview_consent.py` appelle explicitement `check_iamina_csrf` avant `PUT` et `DELETE` **pour toute requête contenant des cookies**, en conservant le modèle existing API Bearer-only sans cookies. La combinaison Cookie+Authorization est rejetée avant toute écriture. Test HTTP Django complémentaire : requête avec Bearer forgé + cookie A et jeton CSRF valide ou non → **401/403**, aucun reçu créé ; un cookie normal avec jeton CSRF correct peut consentir ; une révocation avec cookie+Bearer forgé n'efface pas le reçu. Authentification/cookie globales et garde CSRF W01 sont inchangées ; scope de correction réduit à D2 Preview. Aucun contournement de CSRF, aucune concession de politique clinique ni livraison push.

**Autre échec CI même HEAD, indépendant :** workflow `Offline demo UI certification` #39460086709 (job `118756974400`) interrompu sur navigateur mobile `WebAssembly compilation aborted: Network error: Response body loading was aborted`. Il n'est pas démontré que ce problème provienne du code D2; verdict à recontrôler sur CI du nouveau SHA **sans ajouter de retries aveugles**. Les sept autres workflows de `7b1fc0b` ont SUCCESS; ces succès ne prouvent pas le code corrigé.

**Preuve attendue pour nouvelle candidate :** Django SQLite + PostgreSQL tests CSRF passés ; test anti-mixte passé ; 9/9 workflows et browser visual/offline sur SHA final ; aucune notification réelle ; audit indépendance et preuve BEFORE/AFTER réellement comparables sur les trois viewports avant certification UI. **W01 NO-GO, W02 GELÉ**, arbitrages finaux Production repoussés par le propriétaire, aucun changement Neon/Vercel. D2 reste candidat PARTIEL, PR DRAFT. 


## CI corrective vérifiée — 20/10/2026

**HEAD code `7b9434b3438eceaf6f1b0439f5074e2c18eb5eb8` — 9/9 workflows GitHub Actions SUCCESS, 0 rouge, 0 queued/pending/in_progress.** [CI principale #39467921641](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39467921641) tous ses jobs SUCCESS : Backend SQLite/Ruff **2876 PASS / 5 SKIP / 3 XFAIL**, PostgreSQL **2880 PASS / 1 SKIP / 3 XFAIL** (+ 129 subtests), Frontend Flutter analyze/tests/PWA build SUCCESS. Tests `test_cookie_session_mutations_enforce_csrf_token_and_origin` et `test_mixed_cookie_and_bearer_cannot_bypass_d2_consent_csrf` compris dans les suites PASS (aucune désactivation de leurs assertions). [Offline demo UI #39467920318](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39467920318) **SUCCESS** après le défaut transitoire WebAssembly précédent ; [Chrome screenshot #39467920229](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39467920229) **SUCCESS** sur les trois viewports. Migration drift et les autres contrôles SUCCESS.

**Conclusion exacte :** le défaut de consentement D2 par session cookie sans CSRF, reproduit auparavant en SQLite et PostgreSQL (`200` à tort), est résolu **dans les tests synthétiques de la candidate** par le contrôle explicite sur `PUT/DELETE` et le refus de credentials mixtes, sans autoriser des notifications. Pas de test hébergé ni de vrai compte Web patient, pas de prétention de correction générale du CSRF des autres routes. Les screenshots Chrome sont disponibles mais la comparaison visuelle BEFORE/AFTER multilingue n'a pas encore été certifiée ; l'artefact à lui seul ne prouve pas l'UX D2 en FR/EN/AR.

**Score matérialisé (révision adverse interne) :** Execution **8,6/10**, Adversarial **8,3/10** (écart 0,3), retenu provisoire plafonné **7,9/10** (preuves visuelles multilingues et revue indépendante insuffisantes ; sécurité réelle Web W01 différée par propriétaire). **D2 PARTIEL / PR DRAFT / NON MERGÉE / aucun déploiement**. Aucun flux push/browser/OS/inbox n'existe au runtime de cette candidate ; `delivery_enabled=false`, `browser_push_enabled=false`. Next = validation UX D2 avant/après, revue indépendante, et décision claire sur attente W01 avant tout branchement patient effectif. La présente mise à jour documentaire change le SHA : CI exacte à revalider ; les preuves 9/9 ci-dessus concernent le SHA **code** `7b9434b3`.
