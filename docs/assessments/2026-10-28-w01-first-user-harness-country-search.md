# IAMINA W01 — first-user E2E harness aligned with current Web onboarding

Date: 2026-10-28. Scope: test harness only, not application runtime.

## BEFORE — source evidence
- Old run #40739595534 at old SHA 8a9f7f1 failed the first-user journey on Maroc; a separate diagnostic also did not observe a signup POST. Neither is proof on today's code.
- The old test clicked a static Maroc button, while the actual current Flutter onboarding renders a searchable DropdownMenu with the onboarding-country-search key. Typing is not enough; a real menu option must be selected.
- Script still clicked removed D6 tone choices (Simple et chaleureux / Neutre et professionnel).

## AFTER — targeted repair
- Focus visible searchable country input, type Maroc, choose its suggestion using semantics, then require the exact current French diabetes-type question (only rendered after an actual country code is selected).
- Remove old D6 tone clicks. No product UI change.
- Static tests read current Flutter widget and French localization. A CI job runs Node syntax check and static contract without opening a browser or creating a user.

## Goal / success / evidence
Goal: reduce false failure in W01 first-user test without weakening protections or making claims about the real hosted journey.
Success: three static tests PASS and Node script syntax PASS on exact SHA; CI and PR readback attest code.
Limits: the *complete* hosted Web → BFF → API → Neon, authenticated app-lock and first-user FUE remain NOT_VERIFIED on this candidate. This PR made no Vercel deployment or Neon write through the assistant; however its first automatic PR-triggered historical E2E **DID execute an authenticated-API signup attempt** before cancellation (see incident below). Never claim no account was created.

Status: candidate, not a W01/D9 product certification. D9 remains OPEN.

## 28/10/2026 incident — legacy CI fired a live signup on PR; forced safe-gate fix

- PR #1162 first code SHA `5fd9165a` inadvertently triggered legacy [first-user hosted run #40768344797](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40768344797) on pull_request. The main journey was CANCELLED, but its `if: always()` diagnostic ran at **21:02:42–21:02:57 UTC** and logged **"Synthetic pointer signup reached onboarding with a backend POST."** This confirms the diagnostic observed a successful signup POST to `https://iamina-review.vercel.app`. It does **not** certify an authenticated end-to-end first-user journey or cleanup. The old alias resolves to Vercel deployment `dpl_8eqWcB1cTJudwE9Rw581WenUsy1K` with target `production`, code SHA `60de80ec`, and therefore is **NOT** the current protected W02 Preview.
- Emergency correction at `5b8e3e0657cad00c6cdbec2d1b68d73c97df432b`: legacy `.github/workflows/first-user-prod-e2e.yml` now adds a job gate requiring both `workflow_dispatch` **AND** explicit repository variable `IAMINA_ALLOW_REAL_PROD_E2E == true`. On a new pull_request event, legacy E2E [#40768551237](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40768551237) was **SKIPPED**; static harness [#40768542592](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40768542592) **SUCCESS** at same SHA. **This guard currently lives only on the DRAFT branch, not on the default/base branch**, so merging/reconciling this security guard after review is still necessary to eliminate global PR-triggered signups.
- Read-only independent Neon QA `noisy-truth-00115950 / br-green-meadow-b9j6o0bp`: `auth_user=0`, zero username/email prefix `ux95-signup-`.
- Read-only independent Neon Production `square-sun-82359137 / br-fragrant-frost-b1lbdfzs`: **29** existing `ux95-signup-` user records, **22 created on 28/10**, but **0 created from 21:02:42 through 21:03:00 UTC**; latest matching `date_joined=20:59:20.707Z`. Thus **the successful signup from the cancelled run cannot be identified as a new user in this specific Production Neon DB**. It might have targeted another backend/database, might not have persisted, or timestamps might differ; do not infer identity or location without a verified deployment-to-database mapping. Do not retrieve or print users' PII.
- **No account cleanup authorized or performed** on Production. A direct SQL delete is forbidden for this workflow; any live synthetic account cleanup must be authorized and use the exact application's supported deletion route, with independent read-only postcheck. The 29 old synthetic records in Production are a distinct inventory issue, NOT attribution to the cancelled run.

**Incident status:** live signup POST observed; persisted identity/backend **UNRESOLVED**. **Next exact:** establish read-only alias→BFF→API→DB mapping; decide via explicit human authorization whether to clean known synthetic accounts through verified app endpoints; keep real E2E disabled. W01 and D9 product NO-GO, no new deployment/Neon write.


## 28/10/2026 — Frontend production → API production : source et Vercel corroborés

Audit **en lecture seule**, sans inscription ni SQL d'écriture :

- Vercel `iamina-review.vercel.app` → déploiement exact `dpl_8eqWcB1cTJudwE9Rw581WenUsy1K`, target **production**, repo `hraaaaf/IAMINA-MVP`, SHA `60de80ec070157f912cb62c80a7ded1e9bde75a6`.
- À ce SHA, `frontend/vercel_build.sh` cible exclusivement le projet frontend Vercel `prj_AYaUi32KTDHak8I7dmdQpDrqd8SI` et **force** `API_BASE_URL=https://iamina-certified.vercel.app` et `IAMINA_REMOTE_ACCOUNT_ENROLLMENT=true` lorsque `VERCEL_PROJECT_ID` correspond. La configuration `AuthService` et `ApiClient` utilise `API_BASE_URL` pour les appels `/api/v1`. Ce mécanisme est une preuve de câblage **source build** si Vercel expose l'ID projet attendu, pas une trace réseau certifiée de l'exécution précise.
- Vercel confirme que `iamina-certified.vercel.app` pointe sur `dpl_9tPKqRpMiyEMhCtQ99Jc5QV2ew77`, target **production**, projet backend `prj_Pn9FnyconF3h2w9gOU74iV98kJoU`, SHA `9d24cff11fc422fe0c6235757dbf317eebe32912`.
- **Séparation des environnements confirmée sur configuration** : le projet Vercel backend possède `DATABASE_URL` ciblé `production` et `preview`, plus des variables `IAMINA_EXPECTED_DB_HOST` et `IAMINA_EXPECTED_DB_NAME` ciblées `production`. Aucune valeur de variable ni identifiant secret inspecté ou exposé ici. Les métadonnées ne prouvent **pas** quel branchement Neon effectif a été utilisé par cette requête historique.
- Conclusion prouvée : le POST signup observé dans le run annulé #40768344797 provenait de l'alias frontend Production ; l'architecture déployée du frontend est explicitement configurée pour joindre l'API Production certifiée. **Il manque encore une preuve d'identité exacte API → connexion DB/branche Neon au temps de la requête**, ainsi que l'identifiant synthétique applicatif et sa suppression. Les 29 comptes synthétiques historiques observés précédemment en lecture seule sur Neon Production ne doivent pas être associés à ce run sans preuve.
- **Gate** : aucun replay du signup, aucun effacement direct SQL, aucun test hébergé créant un compte sur production. Le garde PR auto-signup #1162 reste en DRAFT et n'est pas sur la branche base ; PR/merge non autorisés automatiquement.

**Next :** vérifier hors secrets l'empreinte d'identité de la connexion Production via endpoint d'attestation BFF/API prévu, puis faire correspondre exactement à Neon en lecture seule. Si le système n'expose aucune attestation fiable sans secret, **STOP — human/security gate**, ne pas inventer de correspondance ni demander à créer un compte.


## 28/10/2026 — Production API runtime log correlation (read only)

Vercel runtime logs queried **read-only and aggregated by requestPath**: project `prj_Pn9FnyconF3h2w9gOU74iV98kJoU` (`iamina-certified`), deployment `dpl_9tPKqRpMiyEMhCtQ99Jc5QV2ew77`, environment `production`, exact UTC window `2026-10-28T21:02:35Z` to `2026-10-28T21:03:10Z`. Vercel returned **two /api/v1/auth/register log entries**. This window overlaps the cancelled first-user diagnostic at 21:02:42–21:02:57 UTC. No user identifiers, tokens, request bodies or PII fetched. **Two log entries are not proof of two requests, two 2xx statuses, or two successfully persisted accounts.**

Combined with the verified old frontend `iamina-review.vercel.app` production deployment SHA `60de80ec` and build-script target `iamina-certified.vercel.app`, this is **strong API-routing correlation**, NOT proof of the exact DB connection or user identity. The independent read-only Production Neon check documented earlier found no matching `ux95-signup-` account created in that exact window, and the precise remote account/DB attribution remains unresolved.

**NO-GO on automatic account-creating replay**. Never delete existing Production synthetic users without verified attribution, supported application deletion endpoint and explicit authorization. Next: obtain a non-sensitive, owner-authorized DB identity attestation for the exact historical deployed backend (or accept that historical DB attribution is not recoverable), then use W01 synthetic QA only.


## 28/10/2026 — Fenêtre Production : un compte à domaine réservé identifié (lecture seule)

Requête SQL read-only supplémentaire, strictement agrégée sur `Neon square-sun-82359137 / br-fragrant-frost-b1lbdfzs / neondb` : `auth_user=199` total, `ux95-signup-%=29`, `e2e-first-user-%=38`, `w01g5-%=0`. Entre `2026-10-28T21:02:35Z` et `21:03:10Z`, **un et un seul compte** a `date_joined` dans cette fenêtre; à la seconde près, `2026-10-28T21:02:55Z`, domaine e-mail réservé `@example.invalid`, préfixe username **autre** (pas `ux95-signup-`, `w01g5-` ni `e2e-first-user-`). Aucun e-mail exact, identifiant, bearer ou PHI extrait. Cela complète le précédent constat correct `ux95-signup-` **0** dans cette fenêtre : l'ancien contrôle par seul préfixe ne pouvait exclure un compte synthétique sous un autre préfixe.

Le log de diagnostic du run #40768344797 signale un POST signup réussi à 21:02:42–21:02:57 UTC, et l'API production a deux entrées `/api/v1/auth/register` dans la fenêtre. **Correspondance temporelle forte mais causalité non établie** sans request ID/log corrélé et identité BFF→Neon au moment T. Le propriétaire signale disposer de **deux comptes fictifs** utilisables pour QA, mais leur identité/environnement exacts ne sont pas encore corroborés ; ces comptes ne sont pas assimilés automatiquement à ce compte historique.

**Statut sécurité :** aucune suppression, inscription ni mutation Neon. Aucun test clinique Production. QA indépendante `noisy-truth-00115950 / br-green-meadow-b9j6o0bp / iamina925_empty` : `auth_user=0` au dernier contrôle lecture seule. D9 FUE Web hosted NOT_VERIFIED. **Next :** établir mapping identité compte/backend avec preuves autorisées (sans secrets), ou conserver attribution incertaine ; poursuivre uniquement sur branche QA isolée.


## 28/10/2026 — Deux comptes A/B historiques confirmés ; attestation API toujours requise

**Read-only Neon independent result** for `noisy-truth-00115950` / `br-sweet-frog-b9ok6ptp` / `iamina925_empty` queried **as restricted application role `iamina_preview_app`**, not owner: `current_database()=iamina925_empty`, `current_user=iamina_preview_app`, `current_setting('neon.project_id')=noisy-truth-00115950`, `current_setting('neon.branch_id')=br-sweet-frog-b9ok6ptp`; **2 existing A/B test accounts found by exact email match**, both active. No passwords, sensitive values, user IDs or clinical rows retrieved; no SQL write.

Vercel historical synthetic deployment pair **READY / Preview**, both at source SHA `06b2ad57e18e565d0c8e01c28a260541cf759475`:
- Web `dpl_4g6w19iYnExYzoQZRxbzHv9MTKuQ` host `iamina-review-r8m9yx2jk-achraf-benmoussa-s-projects.vercel.app`.
- API `dpl_6wKTvU7YcwUc8FyN7944RKdjbAxo` host `iamina-certified-7xj7cbbzc-achraf-benmoussa-s-projects.vercel.app`.
- Notion W01 history records branch-scoped Web Preview API URL pointing to this exact API deployment, confirmed source `frontend/vercel_build.sh` and `frontend/api/preview-proxy.js` require same-origin BFF and strict Preview OIDC gate, never Production alias. This establishes configuration, **not a successful authenticated runtime request**.
- API source `backend/amina/preview_db_identity.py` provides read-only 4-field SQL identity attestation but requires **normal Preview SSO/OIDC**. Its successful response through BFF has **not** been independently observed. Do not override SSO or bypass OIDC.

**Outcome:** A/B users located, 4 independent QA DB values verified. **Remaining gate:** authenticated Web → BFF → API Preview actual DB attestation = NOT_VERIFIED; no login A/B, no writes, no delete, no deploy. Once normal SSO access and live identity response are established, run authorized A→B→A only with explicit nonpatient boundary, then any clean-up requires exact authorization and application-owned deletion plus independent SQL proof. W01 G5/D9 still OPEN; patient NO-GO.


## 28/10/2026 — Hosted Preview Web→BFF→API→Neon identity: observed via ordinary browser GET

**Live read-only browser evidence:** [TinyFish run de176950-49d4-455c-a2be-1c8630deae24](https://agent.tinyfish.ai/runs/de176950-49d4-455c-a2be-1c8630deae24) opened historical W01 Web `iamina-review-r8m9yx2jk-achraf-benmoussa-s-projects.vercel.app`, then same-origin GET `/api/v1/ops/preview-db-identity`. Browser observed exact 4-field JSON `database_name=iamina925_empty`, `role_name=iamina_preview_app`, `neon_project_id=noisy-truth-00115950`, `neon_branch_id=br-sweet-frog-b9ok6ptp`. **Independent direct Neon read-only SQL as restricted role corroborated all four**. Browser did not use app credentials or create/change users; historical QA branch retains both known A/B test accounts. This closes **identity observation only**, not G5 E2E product.

**Critical protection discrepancy:** the browser reported no SSO login barrier for Web Preview or identity GET, despite Vercel Web project config `ssoProtection.enabled=true`, `deploymentType=preview`. This is **not proof the SSO configuration is globally ineffective** (could be deployment scope, cached session, tool auth, indirect access, or another cause), but protection behavior is **NOT_VERIFIED**. Do not weaken/remove security, do not assume a login has been authenticated. **STOP before A/B authenticated API writes until the preview protection expectation is independently reconciled.**

D9 remains OPEN, patient NO-GO, no new Vercel deployment/Neon mutations. Next: review precise deployment protection effective state, session behavior from fully fresh browser and API unauthenticated negatives; only then test A→B→A on isolated synthetic QA with user-approved cleanup protocol.


## 28/10/2026 — Live Web→BFF→API→Neon four-field identity PASS

**Live browser evidence:** [TinyFish read-only run de176950-49d4-455c-a2be-1c8630deae24](https://agent.tinyfish.ai/runs/de176950-49d4-455c-a2be-1c8630deae24) COMPLETED after seven browser steps. Historical Web Preview `iamina-review-r8m9yx2jk-achraf-benmoussa-s-projects.vercel.app` served Flutter onboarding. Safe same-origin GET `/api/v1/ops/preview-db-identity` returned **exactly** `database_name=iamina925_empty`, `role_name=iamina_preview_app`, `neon_project_id=noisy-truth-00115950`, `neon_branch_id=br-sweet-frog-b9ok6ptp`. All four equal independent restricted-role Neon SQL session results. **The narrow endpoint attestation Web→BFF→API→Neon is PASS** for this historical Preview deployment pair on source `06b2ad57`; neither clinical transport nor signup/logout A→B→A was tested.

**Critical new anomaly:** Browser run reports **no SSO challenge** on Web root or DB identity endpoint while the Preview protection was expected to require normal authenticated access. This is observation, not proof that all access controls are absent; could be pre-existing browser session, session cookies, or deployment protection mismatch. **Do not begin account authentication, mutation or confidential data tests** until Vercel deployment protection is independently checked and any discrepancy resolved. Browser run created no accounts, credentials, mutations or bypass link. Historic A/B both present and active on matching QA DB. No passwords used.

**Next exact:** independently read Vercel deployment-protection scope and browser session context; if an anonymous fresh session can access this endpoint, classify protection failure and resolve in authorized non-production config before A→B→A. Passwords not needed while security gate is open.


## 28/10/2026 — SSO anonymous negative control PASS

[Fresh **anonymous** TinyFish browser run 4a969d3f-1765-4c72-ba71-03f83f06ab7a](https://agent.tinyfish.ai/runs/4a969d3f-1765-4c72-ba71-03f83f06ab7a) **COMPLETED** after 2 browser steps. Unauthenticated GET `https://iamina-review-r8m9yx2jk-achraf-benmoussa-s-projects.vercel.app/api/v1/ops/preview-db-identity` was redirected to normal Vercel SSO login `vercel.com/login?next=/sso-api...`. This is direct negative proof that a fresh anonymous browser **cannot** read the DB identity endpoint; no bypass credentials/cookies used. The earlier TinyFish existing-profile run `de176950-49d4-455c-a2be-1c8630deae24` returned the valid four-field JSON. Absence of an SSO prompt in that earlier browser is plausibly session-related but not independently proved; do not claim a specific session state without its cookies.

**Scoped gate outcome:** historical W01 Preview read-only four-field identity positive control **PASS** and anonymous SSO negative control **PASS**. Source code BFF guards and independent Neon SQL concur. **Remaining**: application login A/B, API bearer isolation, logout/revocation, deletion and independent user-count cleanup are NOT_RUN. Existing A/B identities are active; do not reset passwords, delete accounts or attempt login without approved secure credentials or a prepared authorized app workflow. No real patient data; W02 D9 product remains OPEN.
