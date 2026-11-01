# IAMINA — D7 / First User Experience — patient revenant modifier son profil

**Date :** 31 octobre 2026. **Décision : D7 — Déclaration du type de diabète et des traitements réellement pris, sans prescription ni inférence automatique.**
**Lot de consolidation :** [PR #1208](https://github.com/hraaaaf/IAMINA-MVP/pull/1208) (Web, Draft, sans merge). **Référence clinique / FUE :** [D7 gate canonique](2026-10-29-d7-web-fue-coverage-gate.md), [règles qualité](../QUALITY_SCORING_POLICY.md).

## Choix de la FUE et objectif

**Persona :** un patient déjà utilisateur d'IAMINA revient dans son espace pour corriger ce qu'il a *déclaré*. L'objectif n'est pas de valider un formulaire isolé : il doit pouvoir reconnaître ses choix, les modifier, les enregistrer, les retrouver après réouverture, sans changement de traitement imposé par IAMINA.

**Goal :** une personne peut distinguer et éditer indépendamment type de diabète, traitements effectivement pris et choix « rien à déclarer / je ne sais pas », avec un statut de sauvegarde exact et une conservation sûre des informations du bon coffre.

**Succès observable :** scénario sans erreur sur le **vrai produit Flutter Web** au SHA testé, sur données synthétiques, avec preuves par état avant/après, sauvegarde persistante, rechargement, sécurité du verrou, FR/AR RTL et viewports 390×844, 768×1024, 1280×900. La FUE doit couvrir aussi les erreurs et la récupération. **100 % des cas requis = PASS** pour la validation binaire D7 ; NOT_RUN ou FAIL implique FUE_NO_GO. Aucune conclusion médicale ni score inventé.

## Parcours utilisateur principal — FUE-D7-01

1. **F01 — Entrée et retour.** Ouvrir IAMINA Web sur navigateur neuf ; choisir le parcours local autorisé, configurer/déverrouiller le coffre, terminer l'onboarding ; revenir dans « Profil > Suivi médical ». Le formulaire et les actions doivent être accessibles sans blocage ni donnée médicale fictive.
2. **F02 — Déclaration initiale.** Choisir « Type 2 » et déclarer volontairement « Médicaments oraux » et « Insuline ». Enregistrer : vérifier l'absence de message « synchronisé serveur » sans acquittement ; les éléments sont bien deux choix distincts.
3. **F03 — Persistance.** Fermer/réouvrir l'écran, recharger physiquement la page, déverrouiller ; retrouver exactement type 2 et les deux traitements (ni perdu, ni dupliqué).
4. **F04 — Correction de type.** Passer de type 2 à type 1, enregistrer/recharger ; les deux traitements restent inchangés. Aucun conseil thérapeutique automatique.
5. **F05 — Incertitude puis décision explicite.** Passer de type 1 à « Je ne sais pas / plus tard » ; garder les traitements. Sélectionner explicitement « Aucun traitement à déclarer », sauvegarder/recharger ; la déclaration passe à « aucun », sans prétendre que l'utilisateur ne prend aucun médicament au sens clinique.
6. **F06 — Retour au choix.** Déclarer explicitement « Insuline », enregistrer/recharger : « aucun » est remplacé par la déclaration volontaire, sans restauration cachée d'anciens choix.
7. **F07 — Résilience réseau et statut.** Répéter une sauvegarde en local/pas de réseau, puis restaurer la connexion : le libellé ne doit pas annoncer un succès distant non vérifié ; aucune requête vers un domaine non autorisé, aucune erreur JS/PWA bloquante.
8. **F08 — Présentation et accessibilité.** Capturer les états initial, « type inconnu » et « aucun traitement » sur 390×844, 768×1024 et 1280×900 ; vérifier intégrité du formulaire, CTA visibles, clavier/focus, AR en RTL et FR, textes non prescriptifs. Même viewport/état pour les comparaisons BEFORE→AFTER.

## Parcours associé au correctif #1208 — FUE-D7-02 (consentement et verrou)

Ce parcours est **dans le périmètre produit** de la PR #1208 ; la FUE-D7-01 seule ne le clôt pas.

- **C01 — Choix libre.** Sur la Preview QA protégée et épinglée au SHA exact, sélectionner « Continuer sans IA » ; pas de consentement implicite, le profil reste utilisable.
- **C02 — Verrou explicitement ignoré.** Si « continuer sans verrouillage » a été choisi, le bouton « Accepter » ne doit pas enregistrer de consentement ; le parcours doit offrir « Activer le verrouillage ».
- **C03 — Consentement effectif.** Activer/déverrouiller le coffre, puis accepter explicitement la notice versionnée ; le serveur doit confirmer l'enregistrement, et la navigation doit être cohérente.
- **C04 — Échec et récupération.** Si l'API refuse/échoue, afficher un message explicite, sans fausse acceptation ni fuite de données ; « Continuer sans IA » reste possible.
- **C05 — Retrait / retour.** Vérifier que le retrait du consentement reste contrôlable, et que l'état ne se rétablit pas silencieusement.

**Attention :** le retour iPhone positif de l'utilisateur valide le parcours qu'il a réellement essayé sur la Preview `2fe625cf...`, **pas automatiquement les états négatifs, les viewports supplémentaires ou le SHA de #1208**. Pas d'accès à l'environnement protégé ni de déploiement sans permission spécifique. Les identifiants, tokens, captures nominatives et données de santé ne doivent jamais être versés dans les artifacts.

## Frontière conditionnelle — isolation A → B → A

Le cœur D7 est **un patient revenant sur son dossier**. Réutiliser la preuve W02 d'isolation lorsque son SHA/frontière reste applicable. Pour les frontières modifiées par #1208 (verrou/consentement), ajouter une vérification **ciblée et non destructive** de changement de session A→B→A si les preuves W02 ne couvrent pas le risque. Ne pas ouvrir `GET /api/v1/profile` dans le BFF simplement pour faire passer un test : le coffre clinique reste local-first et protégé.

## Exécution et registre de preuves (à compléter, sans présumer des résultats)

| Cas | Preuve attendue | Statut initial |
| --- | --- | --- |
| F01–F06 | Vrai Chrome + Flutter Web / WebAuthn / SQLite WASM IndexedDB, états avant/après et reload | NOT_RUN pour cette PR |
| F07 | Network egress/offline et vérité du statut de sauvegarde | NOT_RUN pour cette PR |
| F08 | 9 captures comparables 390/768/1280 ; FR/AR RTL ; clavier/focus et erreurs | NOT_RUN pour la FUE intégrée complète |
| C01–C05 | Recette vraie Preview QA du consentement, verrou et retrait sur le SHA correct | NOT_RUN sur cette PR |
| Isolation owner si applicable | Preuve W02 compatible ou A→B→A ciblé, sans données réelles | À justifier / NOT_RUN |
| Revue clinique/privacy | Choix non prescriptifs, sécurité, stockage, CNDP et absence de faux ACK | PENDING |
| Exécution et adversarial / Perfection Pass | Scores sur preuves, analyse des écarts, dernier passage de perfection | NOT_RUN |

### Banc automatisé de départ

Le test `scripts/d7_web_actual_profile_e2e.py` est repris de la branche QA D7 : **huit phases** sur le vrai Web local, un coffre synthétique, Chrome et WebAuthn, **neuf captures** (type 2 / inconnu / aucun × 3 viewports). Il peut prouver F01–F06 partiellement et une partie de F07/F08. Il utilise des libellés anglais pour les interactions automatisées ; les widgets FR/EN/AR et leurs responsive tests sont exécutés séparément. **Ce banc ne certifie ni FR/AR sur la navigation complète, ni consentement distant, ni permissions réelles, ni A→B→A authentifié.**

Le workflow `.github/workflows/d7-fue-returning-patient-web.yml` est **sans secrets**, uniquement Pull Request, avec conservation bornée des PNG synthétiques et du verdict JSON. Toute sortie `PASS` de ce banc est une **preuve partielle** et ne transforme pas la FUE globale en PASS.

**Décision de closeout :** ne pas sortir la PR #1208 de Draft et ne pas merger tant que la matrice complète n'est pas à 100 % PASS, que les dimensions critiques et le Perfection Pass de `docs/QUALITY_SCORING_POLICY.md` ne sont pas satisfaits et que le gate humain de fusion n'a pas été donné. Aucun déploiement Vercel autorisé par cette fiche.

## 31/10/2026 — Perfection Pass / adversarial finding: withdrawal must be fail-closed

**BEFORE — confirmed source finding on deployed main `ed8c67e0`:** `ProfileScreen._confirmWithdrawConsent()` discarded the bool result of `ApiClient.withdrawConsent()` and always showed the success Snackbar even when DELETE returned false/failed. This violated the C05 negative/recovery case and represented a **blocking privacy/truthfulness defect**. It also did not clear `ConsentEvidenceStore`, allowing stale local proof to remain. **No prod user records were read or modified to establish this code-level finding.**

**Goal:** a withdrawal click immediately disables the local AI gate, saves a durable *patient-vault-scoped* pending-withdrawal marker before network contact, explicitly validates the server's `ai_consent_given=false` receipt, clears local notice evidence and DB only after verified remote revocation, and preserves a visible retry action across page reload if remote withdrawal is unconfirmed. Never show `Consentement retiré` on a failed remote result. Clear pending only after both server and local writes are confirmed. An explicit new verified grant may clear a previous pending marker.

**Prepared patch under PR `fix/d7-consent-revocation-fue-20261031`:** introduces `d7_consent_withdrawal.dart`, owner-scoped marker in secure storage, fail-closed ConsentService, startup pending-state restoration, Profile retry CTA and explicit success/warning messages FR/EN/AR, exact server response check in ApiClient. New C05 tests exercise success, rejection, offline exception, marker failure, cleanup failure, retry and misleading 2xx receipt. Workflow D7 adds these synthetic cases before Chrome patient-profile FUE.

**Important limits / binary gates:** synthetic test suite on a PR can prove only these controlled conditions; it is not evidence for real hosted auth/WebAuthn/remote consent across FR/AR or an independent privacy signoff. **FUE D7 remains NOT_VERIFIED** until all required C01–C05 cases on a real permitted QA environment, profile persistence/negative states, actual viewport comparisons, and Perfection Pass score are reviewed with adequate evidence. Old production remains on `ed8c67e0` unless a separate authorized deployment follows.


## 31/10/2026 — Closeout de livraison PR #1209 : production déployée (FUE globale non certifiée)

**Décision et propriétaire** : merge de la PR #1209 et déploiement Vercel Production expressément approuvés. Cela valide **l'autorisation de mise en production**, non la totalité des critères de certification clinique/privacy de la FUE.

**Goal correctif** : ne jamais afficher de faux accusé de réception « Consentement retiré » après échec de suppression serveur. Arrêt local immédiat, marqueur de retrait en attente spécifique au coffre patient, contrôle de réponse serveur `ai_consent_given=false` et avis effacés, nettoyage local après reçu, retry explicite et messages FR/EN/AR.

**Preuves d'intégration** :
- [PR #1209](https://github.com/hraaaaf/IAMINA-MVP/pull/1209) fusionnée via squash, commit applicatif **`a5d1c61c31d0fcc375dabbeec4607506041504f8`**.
- Contenu **identique** au commit testé `fab1496f252f051efe1bb1724fa61883bc835818` : Git tree SHA `e5f85796d224bd638eff0f7b3c48874e0d4b0530`.
- **11/11 workflows pré-merge SUCCESS**, dont [CI complète #41210398742](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41210398742) et [FUE D7 synthétique #41210398830](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41210398830) ; D5 clavier [#41210398745](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41210398745) SUCCESS à la 2e tentative.
- Vercel frontend production `iamina-review` : deployment **`dpl_9LQqNzbj9RbN51cFLcajifxzq3dm`**, **READY**, target `production`, commit exact `a5d1c61`. Alias public **`https://iamina-review.vercel.app`** vérifié relié à ce deployment ID. Backend et DB non déployés/modifiés.
- **Smoke public (données anonymes uniquement)** : `GET /login`, `GET /flutter_bootstrap.js` et `GET /main.dart.js` = **HTTP 200** ; backend `GET /api/v1/account/consent` **HTTP 401 sans identifiant** ; backend `GET /api/v1/health` = `status=ok`, `db=ok`, **`cache=unavailable`** (suivi opérations séparé). Sandbox temporaire de contrôle arrêtée.
- **Rollback** identifié : ancien déploiement frontal `dpl_DiuwDsGWM2eLZhodpFfeZ5tbU7xC`, SHA `ed8c67e0`. Aucun rollback exécuté.

**Statut closeout honnête** :
- `MERGE=PASS` · `PROD_DEPLOYMENT=READY` · `ALIAS=PASS` · `HTTP_SMOKE=PASS` · `SECURITY_SYNTHETIC_FUE=PASS`.
- `POST_MERGE_CI` : suivre [CI #41240704162](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41240704162) et audits UI associés jusqu'au verdict final (in_progress lors du lancement/smoke, ne pas inventer de succès).
- `FUE_C01-C05_HOSTED_AUTH_FR_AR=NOT_CERTIFIED` · `INDEPENDENT_CLINICAL_PRIVACY_REVIEW=NOT_CERTIFIED` · `D7_GLOBAL_VERIFIED=NO`. Les tests synthétiques et le GET anonyme ne prouvent ni un vrai retrait sur compte patient ni une certification réglementaire.
- Aucun % de certification, double score ni score visuel absolu attribué sans revue des preuves correspondantes.

**Next exact** : vérifier les CI post-merge sur `a5d1c61` ; réaliser la FUE consentement hébergée avec comptes synthétiques autorisés (refus, erreur/retry, retrait, reload, FR/AR), puis audit privacy/clinique indépendant et Perfection Pass documentaire. Le commit documentaire ajouté à cette fiche, s'il existe, ne modifie pas le **SHA du code Vercel déployé** `a5d1c61`.


## 01/11/2026 — D7 #1212 security fix: merged and production-deployed, product certification remains open

**Decision / scope:** owner explicitly authorized: « Oui tout marche bien, j’ai fait tout le reste moi même, merge to main et deploy to prod ». This authorizes **PR #1212 safety fix release to Production**. The owner's statement is treated as **manual attestation** for checks not instrumented, not an independent clinical/privacy signature or complete hosted FUE evidence.

**GitHub merge verified:** [PR #1212](https://github.com/hraaaaf/IAMINA-MVP/pull/1212) was un-drafted and squashed into `main` as **`d4fdf6d4b2046b0633ca77c7de80be4d3b53bb60`**. GitHub PR `CLOSED/MERGED`; immediately after merge `compare(d4fdf6d, main)` returned `identical`, and `frontend/lib/features/auth/consent_screen.dart` on main contains the fail-closed condition `lock == null || !lock.isUnlocked`. Reviewable patch = 2 Flutter files (source + widget tests), no DB migration or API change. On PR head `f776817d5272738ae9d5d7bcc95c648f34abec22`, **8/8 GitHub Actions workflows were `completed/success`**, including Flutter Web local FUE and app-lock; backend PostgreSQL suites in general CI were **SKIPPED** by scope. Job log `124727188799` explicitly showed `PASS` for the new regression test refusing consent with missing lock provider. The completed local Web test's 9 PNG artifacts match SHA256 and dimensions but are not hosted Django-session evidence.

**Vercel Production verified:** project `iamina-review` / `prj_AYaUi32KTDHak8I7dmdQpDrqd8SI`. **New Production deployment `dpl_DyVNLd3dA4EuUk4aiYaX1HRGqhSz` `READY`, `target=production`, Git source `main@d4fdf6d4b2046b0633ca77c7de80be4d3b53bb60`**. Immutable build URL `https://iamina-review-pxgma41lm-achraf-benmoussa-s-projects.vercel.app`; canonical public alias `https://iamina-review.vercel.app` was independently resolved through Vercel `get_alias` to **that exact deployment ID**, after build READY. GitHub combined commit status reported `Vercel – iamina-review: success`. Vercel aggregated runtime errors in a 30-minute window reported none; error/fatal grouped counts for this deployment in the last 5 minutes showed no groups. These may reflect **no traffic** and DO NOT prove a fully functioning authenticated page or patient experience. Direct external public HTTP smoke could not be confirmed due external network/URL-fetch restrictions; no production authenticated login, patient writes or medical mutations were performed.

**Rollback reference:** prior production deployment `dpl_9LQqNzbj9RbN51cFLcajifxzq3dm`, `READY`, Git `a5d1c61c31d0fcc375dabbeec4607506041504f8`. Preserve this ID to diagnose/revert if a real production regression is reported. **No rollback executed**.

**Product D7 release versus certification:** user accepted original iPhone 5/5 manual tests on QA source `55fa500`, then verbally reported the remaining checks worked and explicitly approved release; he did not supply independently verifiable clinical/privacy expert signoff, real hosted negative/retry A→B instrumentation, FR/AR 390/768/1280 FUE evidence, execution/adversarial scoring or final Perfection Pass. Therefore **`PATCH_RELEASE_PRODUCTION=VERIFIED_BY_VERCEL_METADATA`**, **`D7_GLOBAL_CERTIFIED=NO / FUE_NO_GO`** and **Chantier B 0/17 formally certified**. Do not turn a deploy into a regulatory/clinical qualification. No deployment of a broader D7 rewrite was authorized or performed.

**Next exact / remaining sequence:** capture a real user-visible public Production smoke if owner session can visit and report only synthetic/non-sensitive facts; obtain and inspect full hosted authenticated QA A/B, network failure/withdrawal retry and consent evidence, FR/AR RTL and keyboard/a11y same-viewports; obtain risk-specialist clinical/privacy review; enter execution/adversarial scores under `docs/QUALITY_SCORING_POLICY.md`, complete Perfection Pass, certify D7 only with full pass and closeout; then proceed to D22 subject to D19 clinical gates. This documentation-only post-release commit does not change the released Flutter runtime `d4fdf6d4`.
