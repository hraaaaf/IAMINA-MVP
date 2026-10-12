# IAMINA — Handover canonique de reprise V1-03 / P3 option A

> **RECTIFICATION CANONIQUE 2026-10-12 (propriétaire)** : **0 client** aujourd'hui ; IAMINA V1 patient **local-first** ; Vercel/Django/Neon dédiés au dev/cert, pas aux patients. Les anciens paragraphes de ce handover sur les clients réellement installés sont **supplantés par §23**. [Dossier pre-launch](../assessments/2026-10-12-v1-03-distribution-privacy-cutover-gates.md). PR #941 exact HEAD `d3562e8` : **25/25 CI verts**, DRAFT sans merge ni déploiement ; gates P5-6 avant **première donnée de santé identifiable**, autorisation merge et Vercel séparées.

**Dernière vérification live : 2026-10-11 (Afrique/Casablanca).**  
**Repo :** `hraaaaf/IAMINA-MVP` · **Lot actif :** V1-03, P3 HTTP aliases dormants, décision utilisateur **A**.  
**Source de vérité sur l'avancement global :** `docs/ROADMAP.md`, présente dans la PR DRAFT #933.  
**Statut :** **engineering du sous-lot #937 certifié**, **pas** merge/release/patient; `NOT_RELEASE_AUTHORIZED`.

## 1. Goal, succès observable, preuves

**Goal exact approuvé :** pour la V1, **ne pas exposer** les alias `/api/v1/diabetes/*`. Garder `/diabetes` comme *préfixe de module réservé*, maintenir `ModuleRegistry`/moteur diabète et les routes *réellement accessibles* `/api/v1/logs/*`, `/api/v1/ai/chat` et stream. Faire correspondre manifeste et triage au routage réellement actif et empêcher tout retour accidentel de P3, y compris avec texte d'urgence.

**Succès engineering (atteint et prouvé) :** [PR #937](https://github.com/hraaaaf/IAMINA-MVP/pull/937), HEAD **`4d287bb1c8049b416b7e0f2c7ad5aa031c370ca7`**, [CI #38174457859](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38174457859) **6/6 jobs success** (Flutter analyze/tests/PWA, backend Ruff+pytest, PostgreSQL, scope, secret hygiene, taille PR), **16/16 workflows GitHub `completed/success`**, zéro workflow rouge à cette vérification. Ne pas reporter ce vert sur de futurs commits.

**Etat GitHub #937 après closeout :** base RESTAURÉE à `parallel/v1-03-module-alias-404-audit-20261011` (parent **PR #936**, base SHA `62cc18bc0266838a98bbd7fe6b3ad8c794c82938`), HEAD inchangé `4d287bb...`, **DRAFT, merged=false, mergeable=true**. Diff parent → HEAD : **2 commits / 7 fichiers**, `ahead=2`, `behind=0`. Aucun merge, Vercel, nouvelle exposition ou patient réel.

**Preuves négatives ajoutées au test** `backend/core/tests/test_p3_dormant_alias_route_guard.py` : absence des alias logs/chat en OpenAPI et resolver Django, HTTP 404 sur les URL P3 avec texte d'urgence synthétique, fournisseur IA non appelé, triage déterministe du vrai chat préservé, aucun `ModuleRegistry.all()` invoqué pour monter les routeurs durant un démarrage Django neuf.

## 2. Changements du sous-lot #937

| Fichier | Modification |
| --- | --- |
| `backend/diabetes/api/main.py` | Supprime le montage dynamique via `ModuleRegistry.all()` ; routes canoniques explicites conservées |
| `backend/diabetes/manifest.py` | `url_prefix="/diabetes"` reste réservé ; `interactive_endpoints=["/api/v1/ai/chat"]` reflète le chat réellement accessible |
| `backend/diabetes/apps.py` | Enregistre le triage depuis la liste du manifeste, plus de faux `/api/v1/diabetes/ai/chat` |
| `backend/core/middleware/triage_vital.py` | Retire l'ancien chemin SSE P3 fictif, conserve le stream canonique |
| `backend/core/tests/test_p3_dormant_alias_route_guard.py` | Tests HTTP/OpenAPI, anti-réactivation urgente, manifest/triage et Django boot |
| `docs/architecture/module-contract-spec.md` | Clarifie le statut V1 réservé/non monté du préfixe P3 |
| `docs/assessments/2026-10-11-v1-03-p3-module-alias-404-audit.md` | Diagnostic et application de la décision A |

**Commits :** `9cba062075768c8ebd8a4744ce77c3f0f1621535` (implémentation et tests), puis `4d287bb1c8049b416b7e0f2c7ad5aa031c370ca7` (imports Ruff I001 uniquement). La première CI [#38174253867](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38174253867) échouait au lint (deux `I001`). La nouvelle CI [#38174457859](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38174457859) est entièrement verte.

**Décision d'architecture :** [ADR-0009](../adr/ADR-0009-v1-p3-dormant-aliases.md) **ACCEPTED**, complète sans annuler ADR-0008. Toute exposition future des alias est **un nouveau chantier et une nouvelle décision**, avec contrat router/auth/CSRF/consent/triage et revue indépendante sécurité/privacy/clinique.

## 3. État vérifié des PR parentes et parallèles (2026-10-11)

| PR | HEAD vérifié | Résultat connu | Base et merge |
| --- | --- | --- | --- |
| [#932](https://github.com/hraaaaf/IAMINA-MVP/pull/932) — OCR unité explicite fail-closed | `15cfe25fcc93fff00a1198d705fb683c7a2eb960` | 16/16 exact-HEAD historique | base `security/v1-03-strip-client-curl-logger-20261011`, DRAFT non mergée, mergeable |
| [#933](https://github.com/hraaaaf/IAMINA-MVP/pull/933) — OCR audit, roadmap, ADR et handover | HEAD documentaire évolutif, **relire GitHub à la reprise** | Ancienne suite tests sur SHA `2828ee75...` 16/16 ; **ne pas attribuer ce résultat au HEAD documentaire** | base #932, DRAFT non mergée, mergeable au dernier contrôle |
| [#934](https://github.com/hraaaaf/IAMINA-MVP/pull/934) — consentement, refus IA durable sur installation option A | `f0b02165b478db6b6bb25d33f534a502ffa542f8` | 19/19 GitHub exact-HEAD ; UI synthétique aux 3 viewports | base #932, DRAFT non mergée, mergeable |
| [#935](https://github.com/hraaaaf/IAMINA-MVP/pull/935) — legacy GET SSE 405 sans redirection | `5f2378ee7935bb64b5af850b6bfb2e68a9a49ebe` | 16/16 exact-HEAD ; POST JSON seul dans OpenAPI | base #932, DRAFT non mergée, mergeable |
| [#936](https://github.com/hraaaaf/IAMINA-MVP/pull/936) — diagnostic P3 bootstrap | `62cc18bc0266838a98bbd7fe6b3ad8c794c82938` | 16/16 exact-HEAD ; trace Django propre : registre vide lors du montage ancien | base #932, DRAFT non mergée, mergeable |
| [#937](https://github.com/hraaaaf/IAMINA-MVP/pull/937) — politique P3 dormante **A** | `4d287bb1c8049b416b7e0f2c7ad5aa031c370ca7` | **16/16 exact-HEAD, 6/6 CI** | **base #936 restaurée, DRAFT non mergée, mergeable** |

**Important :** #937 est empilée sur #936, lui-même sur #932 ; les autres PR #933–#935 sont parallèles et ne doivent pas être mergées aveuglément. **Évaluer ordre, compatibilité et revue de l'empilement avant toute fusion.**

## 4. Autres limites / gates non levés

- **OCR glycémie (#923) :** parsers sans inférence silencieuse d'unité, mais parcours UI capture→lecture→confirmation→sauvegarde pas certifié, provenance optique non prouvée ; cas HI/LO, plage 401–600 mg/dL et correction exigent revue clinicien. Matrice de preuve synthétique dans `docs/assessments/2026-10-11-v1-03-ocr-reachability-unit-audit.md` sur #933. Pas de patient ni média cloud autorisé.
- **Consentement (#924) :** #934 green en engineering ; vrais tests iOS/Android/PWA avec redémarrage, offline et appareils distincts, plus revues privacy/clinique, non acquis. Choix A : par installation, pas révocation serveur globale.
- **SSE / données privées (#925/#927) :** la route GET legacy est 405 et sans redirection dans les tests ; logs CDN/edge/APM/WAF, rétention et vrais anciens clients installés **non inventoriés**. L'endpoint `/api/v1/app-compatibility` existe déjà mais version client absente → état `version_unknown`, pas preuve de migration.
- **Release :** P5-6A/#318 et P5-6B/#320, sécurité/privacy/clinique indépendante et appareils réels obligatoires avant un pilote réel. Aucun candidat production exact-HEAD refigé ; **aucun Vercel sans permission explicite**.
- **Avancement P5 historique dans la roadmap :** **6/12 lots atomiques = 50 %** (lots macro 4/9 = 44,4 %). **Pas un pourcentage de V1-03.** Les décisions produit V1 sont 29/29 approuvées, **pas 29/29 implémentées**.

## 5. Next exact — nouvelle fenêtre de travail

1. **Lire ce fichier puis `docs/ROADMAP.md`.** Revérifier *live* repo, branche, HEAD/PR #932–#937, compare parent #936 → #937 et statut exact des workflows, sans supposer les résultats immuables.
2. Vérifier le **closeout** GitHub #937 (PR body + commentaire dans issue #929), Notion [page IAMINA](https://app.notion.com/p/3f477c66336281b28c78eb11c22f5ee6) et pointer les fichiers canoniques. Corriger toute incohérence sans modifier la surface patient.
3. Enchaîner les audits V1-03 indépendants autorisés : revérification des gates de compatibilité SSE / ingress **sans accès PHI**, préparation de tests vrais appareils du refus IA et pack revue clinique OCR. Toute preuve nouvelle doit être consignée et avoir sa CI propre si code changé.
4. **Human gate réel :** revue sécurité/privacy/clinique et décision de merge pour la pile de PR, puis gate de release pré-patient. Ne pas transformer les 16/16 workflows en validation clinique ni **déployer Vercel** sans permission.

### Séquence restante selon résultat

- **Si PR/CI toujours vertes :** closeout documentaire → préparer revue indépendante → arbitrage merge de la pile → merge seulement si explicitement autorisé et toutes les protections observées → post-merge exact-HEAD → lots V1 suivants.
- **Si CI rouge / HEAD changé :** lire logs exacts → correction limitée et fail-closed → nouvelles suites exact-HEAD → vérifier base parent + diff → mise à jour du handover et de la roadmap.
- **Si gate clinique/privacy ou décision irréversible :** signaler précisément ce qui manque ; ne pas activer OCR, alias P3 ni usage patient.
- **Si GitHub CI asynchrone :** continuer le travail indépendant ; ne pas attendre/poller passivement.

## 6. Repères et reprise

**Chantier :** IAMINA V1-03, P3 aliases dormants option A  
**Dernière preuve :** #937 `4d287bb...` — 16/16, CI #38174457859 6/6, base #936, DRAFT/non merged/mergeable  
**Blocage réel :** pas pour l'engineering #937 ; reste gates indépendants (privacy/sécurité/clinique, vrais appareils, et merge/release)  
**Next exact :** vérification documentaire de reprise et préparation des gates V1-03 sans modifier les routes.  
**Fichier canonique :** `docs/handovers/2026-10-11-iamina-v1-03-option-a-p3-dormant-handover.md` — adossé à `docs/ROADMAP.md`.

**NE PAS PROCLAMER `PRODUCTION_READY`, `GO-LIVE` ou V1-03 clôturé.**

## 7. Reprise complémentaire — pack des revues indépendantes (2026-10-11)

Le pack `docs/assessments/2026-10-11-v1-03-independent-review-readiness.md` a été ajouté sur la branche documentaire #933. Il synthétise les gates SSE/ingress/anciens clients, consentement IA par installation sur appareils réels, revue clinique de l'OCR, et l'intégration de #932–#937. C'est un document de préparation, pas un test exécuté, une validation clinique/privacy ou une approbation de merge. Reprise live : #932/#934/#935/#936/#937 exact-HEAD verts, #933 HEAD documentaire sans CI exacte; main@13b7cce12c86daf60119fb703f22e8c6c192cf8d. Prochaine action : revues indépendantes + essais synthétiques appareils/environnement autorisé, puis nouvelle CI sur tout candidat intégré. Aucun merge/Vercel/patient réel. `NOT_RELEASE_AUTHORIZED`.


## 8. Reprise complémentaire — 11 octobre 2026

Le dossier `docs/assessments/2026-10-11-v1-03-independent-review-readiness.md` documente les audits de frontière LLM, de configuration Vercel en lecture seule et de compatibilité des clients. Vérification ciblée au SHA #934 `f0b02165` : 33 services Dart et 6 entrées Flutter inspectés sans référence retrouvée à la consultation de l'API de compatibilité. L'inventaire des versions distribuées, les réglages réels de journalisation et les essais sur appareils restent non prouvés. Les nouveaux commits documentaires de #933 n'ont pas de CI exacte. Aucune activation, fusion ou mise en production n'est autorisée. Suite : revue externe qualifiée et preuves environnementales, puis autorisation de fusion distincte.


## 9. Divergence des déploiements et correction de portée — 2026-10-11

Audit dédié : `docs/assessments/2026-10-11-v1-03-deployed-sse-url-privacy-divergence.md`. `get_alias` Vercel relie `iamina-review` à `dpl_CJpLFLEQngvjsZXj23FinoXYoH1t` (Git `1e44ba57`) et `iamina-certified` à `dpl_E3fMNHmVk2iH5Qsz9GAUxv8MpGzH` (Git `b13b44e7`). Ancien code source frontend et backend contiennent GET SSE avec `?message`, contrairement aux correctifs #934/#935. **Contrepreuve importante :** le vrai `main.dart.js` web GET 200 (5 066 376 caractères) ne contient pas `chat/stream`. L'UI active `/companion/chat` utilise `CompanionConversationScreen` → `CompanionService.sendChatMessage()` en POST ; `AminaChatView` GET semble être une branche historique non embarquée. **Risque source historique confirmé, fuite GET par le parcours web actif NON démontrée.** Backend public sans message refuse 401 via connecteur ; ne constitue pas test authentifié. Les anciens clients installés, journaux ingress/redaction/rétention et protections effectives restent UNKNOWN. Les déploiements actuels ne prouvent aucune des corrections PR #934/#935, les CI verts ne s'appliquent pas au live. Aucun changement Vercel, merge, essai avec PHI ou nouvelle compilation. Next exact : établir parc et routes réelles sans PHI, autoriser protection ou déploiement coordonné uniquement après décision humaine, tests sur appareils et revues clinique/security/privacy, puis CI d'intégration.


## 9. Gate de sécurité PRIORITAIRE : dérive SSE réelle des déploiements (11 octobre 2026)

Le dossier canonique de preuve est [`docs/assessments/2026-10-11-v1-03-sse-production-drift-pr938.md`](../assessments/2026-10-11-v1-03-sse-production-drift-pr938.md).

- **Preuve production :** Vercel `iamina-certified` production READY 2026-10-02 sur SHA `df004bcb` conserve `GET /api/v1/ai/chat/stream?message=...`. Vercel `iamina-review` production READY 2026-10-08 SHA `1e44ba57` forme encore `http.Request('GET', uri.replace(queryParameters: {'message': message}))` dans le client Flutter. Ces deux commits diffèrent du `main` actuel `13b7cce1`. Il s'agit d'une **capacité de transport risquée dans les sources réellement associées aux déploiements**, non d'une fuite vérifiée.
- **Seconde preuve :** `main` utilisait `TriageVitalMiddleware._log_emergency` avec un extrait patient et `user_id`; migrer SSE en POST sans précaution faisait intercepter un message urgent avant Ninja auth/CSRF et retournait du JSON à un client SSE.
- **Action technique isolée :** [PR DRAFT #938](https://github.com/hraaaaf/IAMINA-MVP/pull/938) sur `main` : Flutter POST JSON URL propre ; backend POST-only, 405 GET, CSRF cookie, scopes SSE, exception logging sûre ; urgence canonique après auth, suppression PHI des logs, OpenAPI et tests synthétiques. **Aucun merge ni déploiement**. Ne pas confondre ses tests/CI en cours avec une correction en production.
- **Gate prioritaire :** CI exacte #938 + preuves de migration clients réellement distribués et politiques ingress/logging/rétention ; arbitrage humain **distinct** de l'approbation du merge et du déploiement Vercel coordonné. Une réponse HTTP 405 ne supprime pas une query envoyée par un ancien client. Préserver la sécurité clinique et les modes local-first/offline.
- **Séquence reprise :** vérifier la CI exacte du HEAD #938, traiter toute régression ; réconcilier les conflits fonctionnels avec #932–#937 **sans les fusionner** ; contrôler le plan d'upgrade PWA/native avec scénarios synthétiques ; demander l'autorisation explicite de merge/deploy avant toute opération irréversible. `NOT_RELEASE_AUTHORIZED`.


## 10. CI #938 — CSRF cookie + Bearer, remédiation sur branche DRAFT (2026-10-11)

CI exacte `38184659246`, HEAD `9e7ca998` : **2 781 tests backend passés, 3 échecs**, pas de validation du lot. Deux tests utilisaient l'ancienne signature directe GET ; un test HTTP prouvait un défaut réel : l'en-tête Bearer falsifié exemptait le CSRF malgré le cookie session (`CsrfExemptApiMiddleware`). Patches poussés sur [PR #938 DRAFT](https://github.com/hraaaaf/IAMINA-MVP/pull/938) : exemption Bearer réservée aux requêtes **sans cookie session**, tests anti-bypass couvrant account/logs/profile/chat/SSE et adaptation des deux tests unitaires POST. HEAD de réexécution `cbddb5621af3e82ac63ca6b98cbaa72ef82fe4eb` ; CI de ce HEAD lancée, verdict final inconnu au moment de cette annotation.

Source : [dossier sécurité V1-03 / drift SSE](../assessments/2026-10-11-v1-03-sse-production-drift-pr938.md), section CI. La preuve à recueillir reste : tests Django et Flutter verts **sur le même HEAD**, réponse urgente SSE canonique post-auth/CSRF, logs sans PHI, puis preuves d'installation clients/ingress et approbations humaines indépendantes avant merge et Vercel. `NOT_DEPLOYED / NOT_RELEASE_AUTHORIZED`.


## 11. Reprise P0 — CSRF pré-Ninja confirmé et réconcilié (2026-10-11)

Au HEAD hotfix `cbddb5621af3e82ac63ca6b98cbaa72ef82fe4eb` la CI `38184949625` a échoué après **2 786 tests passés / 5 sous-échecs** de l'inventaire cookie + faux Bearer sur les routes protégées : malgré l'interdiction d'exemption Bearer avec cookie, la validation de schéma Ninja répondait encore 422/404 **avant CSRF**. Le statut *source-level fixed* ne suffit donc pas. Après deux tentatives dans ce sous-système, la branche DRAFT [#938](https://github.com/hraaaaf/IAMINA-MVP/pull/938) a repris **à SHAs blob identiques** les modules de CSRF central/SessionAuth de la branche #932 déjà CI-validée à son propre HEAD. Nouvelle HEAD #938 : **`e2bbb9a34fccf643c62d329641217648522e7f41`** (11 fichiers). CI auto redémarrée : run `38185214547` et workflows parallèles ; **aucun verdict vert exact-HEAD au moment de l'écriture**.

**Next exact :** diagnostiquer la CI #938 au SHA ci-dessus jusqu'à preuve ; si échec, corriger et relancer sans merge ; si verte, double audit indépendant sécurité + clinique ; soumettre les gates explicites de merge et Vercel et le plan PWA/native/logs/ingress. Conserver #932–#937 DRAFT, P3 dormant et `NOT_DEPLOYED / NOT_RELEASE_AUTHORIZED`. Voir [dossier P0 détaillé](../assessments/2026-10-11-v1-03-sse-production-drift-pr938.md).


## 12. Pré-certification P0 — matrice auth élargie (2026-10-11)

Sur #938 DRAFT, copie byte-identique du fichier de **10 tests** `backend/core/tests/test_v1_03_cross_route_csrf.py` (blob #932 `f8e8e180d5beda31c420f22b3344c8cae803fbaa`), pour vérifier **sur la branche isolée** cookie/CSRF, spoof Bearer, Bearer natif, login public et inventaire des routes unsafe montées. Précédents runs verts P5-5/screenshot/migration mais CI de `e2bbb9a3` annulée par le commit suivant, donc **non certifiée**. Nouvelle tête **`1461e31419920459292d059819ffeced8f6c57fa`**, 12 fichiers, CI GitHub exacte **`38185369954`** en cours et workflows associés en cours au premier contrôle.

Next exact : valider le backend/Flutter sur `1461e314`, corriger tout échec avec log/job exact si nécessaire, puis review complète et gates de migration/logs/clients. Aucun merge/Vercel ; `NOT_DEPLOYED / NOT_RELEASE_AUTHORIZED`.


## 13. 12 octobre — CI #938 run 38185369954 et cause native 401

Run exact [`38185369954`](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38185369954), HEAD `1461e314` : **échec** des deux jobs backend, mais frontend analyze/tests/PWA, migration Django, P5-5 et screenshots verts. SQLite : **2 796 passed + 4 sous-échecs** ; PostgreSQL : **2 800 passed + 4 sous-échecs**. Les 4 échecs portent exclusivement sur le Bearer natif sans cookie (401 au lieu de 422/404).

**Cause croisée vérifiée :** `main/backend/conftest.py` remplace en autouse `FirebaseAuth.__call__` ; `FirebaseAuth` est l'alias de `HybridBearerAuth` et la fixture rejette le natif sans session. C'est une **simulation de test trompeuse**, pas une panne native live prouvée. La version #932 du même `conftest.py` n'altère plus l'auth. Portage par blobs identiques de cette fixture + rétablissement du test de matrice depuis #932 sur la [PR #938 DRAFT](https://github.com/hraaaaf/IAMINA-MVP/pull/938).

**État technique :** nouvelle HEAD #938 `beeed3ecb60b68a9a30b5a9d46736f9a6f520e4d`, **13 fichiers**, run exact **`38230019452`** queued au premier contrôle. Aucun merge, Vercel, PHI. **Next exact :** vérifier son verdict après travail indépendant ; si échec, analyser le job réel/corriger ; si vert, double review et package de migration clients PWA/backend, sans franchir human gates merge/deploy. Status `NOT_DEPLOYED / NOT_RELEASE_AUTHORIZED`.


## 14. 12 octobre — hotfix SSE/CSRF #938 : **CI TECHNIQUE VERTE**, aucun déploiement

La [PR #938 DRAFT](https://github.com/hraaaaf/IAMINA-MVP/pull/938) est toujours OPEN/non fusionnée, base `main` `13b7cce1`, HEAD exact **`beeed3ecb60b68a9a30b5a9d46736f9a6f520e4d`**, 13 fichiers. [CI `38230019452`](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38230019452) : **SUCCESS, 6/6**. Pytest : SQLite **2796 passed / 5 skipped / 3 xfailed**, PostgreSQL **2800 passed / 1 skipped / 3 xfailed**, **178 subtests** dans chaque job. Flutter **646 passed / 1 skipped**, web release build OK. Workflows migration `38230019366`, répétition P5-5 `38230019333`, E2E compagnon `38230019311` : tous SUCCESS.

**Cause closeout :** quatre 401 natifs étaient causés par la fixture test globale `backend/conftest.py` sur `main` qui patchait `FirebaseAuth.__call__`, alias de `HybridBearerAuth`. Suppression du patch test seulement, maintien de la fixture DB de #932 et des vrais scénarios CSRF. Preuve du test intégré = CI ci-dessus, pas seulement source.

**Limite fondamentale :** la PR corrige un **candidat**, pas les SHA du frontend/backend déjà déployés (anciens GET avec message dans URL). Elle n'intègre pas l'option A P3 dormant (#937), ni les autres PR #932–#937, toujours DRAFT. Dossier exact des preuves et risques : [`docs/assessments/2026-10-11-v1-03-sse-production-drift-pr938.md`](../assessments/2026-10-11-v1-03-sse-production-drift-pr938.md), section 14.

**Next exact :** préparer/soumettre les éléments pour la décision humaine de merge **puis** le déploiement Vercel séparément ; avant cela, établir l'inventaire réel des versions PWA/native et l'ingress/rétention, revue sécurité/clinique, scénario de mise à jour sans ancien GET et double audit des impacts UI à mêmes viewports. Après approbation : intégration/CI exacte, smoke synthétique et closeout post-déploiement. **Ne pas merger ni déployer sans autorisation explicite.**

**État : P0 hotfix `TECHNICAL_CI_GREEN`, `DRAFT / NOT_MERGED / NOT_DEPLOYED`. IAMINA V1-03 : `NOT_RELEASE_AUTHORIZED`. P5 historique : 6/12 = 50 %.**


## 15. 12 octobre — gate migration clients : preuve du risque cache, pas encore d'upgrade

Audit GitHub source sur **#938 HEAD `beeed3ec`** : version Flutter `0.1.0+1`, `IAMINA_CACHE_SCHEMA='0.1.0+1'`, app shell `main.dart.js` cache-first et fallback bootstrap sur la même version. Hors domaine hosted-review, un ancien client PWA peut donc rester sur l'ancien code GET même après changement serveur ; **une modification web seule n'est pas preuve de migration**. Le SW ignore les réponses `/api/` pour la mise en cache applicative, sans empêcher le GET réseau historique. Contrat backend `/api/v1/app-compatibility` existe mais n'infère pas la version si métadonnées absentes et ne distingue pas les builds réutilisant `0.1.0+1`.

Inspection Vercel **en métadonnées seulement**, le 12/10 : dernière production review `dpl_CJpLFLEQngvjsZXj23FinoXYoH1t` (2026-10-08 SHA `1e44ba57`) ; dernier backend certified `dpl_7SogpUMHNHd9rF7s7rfALccKduv7` (2026-10-02 SHA `df004bcb`). Ils n'ont **pas** été remplacés par #938. Les drains demeurent inconnus (API 404).

**Next exact autorisé :** préparer matrice d'upgrade ancienne PWA/iOS/Android avec marqueurs synthétiques, vérifier politiques de rétention/ingress via accès autorisé et recenser versions distribuées ; préparer nouveau build/version/SW dans branche d'intégration DRAFT après arbitrage de la fenêtre de compatibilité, pas sur la PR P0 déjà verte. Tests exact-HEAD et double revue à faire. Aucun merge ni Vercel sans autorisation explicite.

Détails complets : `docs/assessments/2026-10-11-v1-03-sse-production-drift-pr938.md` section 15. `TECHNICAL_CI_GREEN` pour #938 inchangé, mais `MIGRATION_NOT_PROVEN / NOT_RELEASE_AUTHORIZED`.


## 16. 12 octobre — exécution parallèle bornée des quatre pistes V1-03

**Déclenchement :** l'utilisateur demande explicitement d'avancer **en parallèle** dès que les tâches sont indépendantes. Les audits et preuves peuvent être menés concurremment, sans attendre les autres ; **ne pas** confondre avec des tests réels / travaux de fond asynchrones une fois la session close. Les actions irréversibles et les cinq conflits de fichiers candidats attendent le point de convergence.

### Pistes indépendantes, Goal → succès → preuve

| Piste | Goal | Succès observable | Preuve actuelle / Next exact |
| --- | --- | --- | --- |
| **A : compatibilité SSE / versions PWA** | aucun ancien client ne crée de nouvelle URL de santé sans contrôle, migrer au POST | inventaire réel par build/méthode ; nouveau numéro de version + cache schema distincts ; upgrade synthétique depuis ancien SW vérifié et POST sans query | Audit source section 15 : `0.1.0+1` répété dans pubspec/SW/bootstrap, `main.dart.js` cache-first. **PAS de distribution réelle inventoriée** ; préparer tests autonomes PWA sans modifier #938 vert |
| **B : refus IA par installation** | empêcher AI/voix/image/stream après refus, y compris redémarrage/hors ligne | iOS, Android et PWA réels avec version/build identifié ; refus persistant et appels réseau à zéro, changement de compte et réacceptation contrôlés | #934 tests Dart `consent_local_decline_store_test.dart` utilisent `Mock<FlutterSecureStorage>`; `v1_03_local_decline_network_gate_test.dart` utilise `MockClient` et fausse auth. **Mocks ≠ vrais appareils**. Continuer les tests synthétiques indépendants, puis QA appareils sans patient |
| **C : OCR glycémie** | aucune valeur ni unité inventée, aucun enregistrement implicite | corpus optique autorisé, preuve d'unité visible, UI confirmation explicite avant écriture, annulation 0 DB, revue clinicien HI/LO et plage 401–600 mg/dL | #932 garde unité et #933 audit : OCR non raccordé aux consommateurs examinés ; **pas de parcours patient ni preuve clinique/optique**. Maintenir désactivé jusqu'au gate |
| **D : infra/logs/security** | connaître toutes les destinations et règles de collecte avant diffusion | configuration Vercel/CDN/APM/WAF, durée de rétention, tests à marqueur synthétique, approbation responsable privacy | Métadonnées Vercel #15 : review `1e44ba57`, certified `df004bcb`, anciens GET encore dans code source. Appel drains HTTP 404 = **INCONNU**, pas « aucun drain ». Aucune lecture PHI autorisée ; inventaire sans contenu patient |

**Piste E déjà techniquement prouvée, sans dépendance à ces audits :** P3 alias dormant selon décision A, #937 SHA `4d287bb1`, 16/16 workflows historiques verts ; non intégré à #938. Refaire tests P3 sur toute branche d'intégration.

### Frontière d'intégration — preuve GitHub par SHA blob (pas hypothèse)

Comparaison **à trois HEAD exacts** #932 `15cfe25f`, #937 `4d287bb1` et #938 `beeed3ec` sur les **10 chemins en commun entre #932 et #938** :
- **5 identiques #932 ≡ #937 ≡ #938 par SHA blob** : `backend/amina/middleware/csrf_exempt_api.py`, `backend/amina/vercel_session_auth.py`, `backend/conftest.py`, `backend/core/tests/test_v1_03_cross_route_csrf.py`, `frontend/test/services/v1_03_sse_privacy_contract_test.dart`.
- **5 différents** : `backend/ai/api/v1/ai.py`, `backend/core/middleware/triage_vital.py`, `backend/core/tests/test_input_safety.py`, `docs/api/openapi.json`, `frontend/lib/services/api_client.dart`. Ces différences nécessitent une **revue fonctionnelle ligne/parcours** sur branche d'intégration, pas un copier-coller par ordre arbitraire. Les trois variantes SSE du router sont `POST` et non `GET`, mais #938 place explicitement l'urgence canonique après auth/CSRF ; #932/#937 n'utilisent pas la même voie. Préserver cette protection dans toute consolidation.
- Les branches #934/#935 sont descendantes de #932 ; l'intersection de fichiers ne prouve pas l'absence de conflits dans leurs changements de consentement. Faire une comparaison différentielle supplémentaire au besoin.

**Point de convergence (SEULE étape non parallèle)** : aligner branche d'intégration et choix de cutover ; scénario intégré auth/CSRF + SSE/urgence + refus IA + garde OCR + P3 dormant + PWA ; suite exacte GitHub (SQLite, PostgreSQL, Flutter, version SW, CI E2E). Cela **ne remplace pas** les validations indépendantes privacy/clinique ni les autorisations explicites de merge et de déploiement Vercel.

**État : quatre pistes documentées et analyses sources effectuées dans cette session ; aucune preuve externe inventée, aucun appareil réel testé, pas de merge/deploy.** PR #938 conserve son HEAD `beeed3ec`, CI `38230019452` vert ; PR documentaire #933 reçoit cette mise à jour sans certification CI exacte de son nouveau HEAD. **Next exact :** poursuivre indépendamment A (matrice upgrade), B (QA réel), C (avis clinique), D (politiques journaux) puis intégrer seulement avec toutes les pièces requises. `V1-03 NOT_RELEASE_AUTHORIZED`.


### Complément de contre-revue ligne/parcours : **garde de consentement SSE ABSENTE de #938 isolée**

Après le comparatif de blobs, lecture côte à côte des méthodes :
- `frontend/lib/services/api_client.dart::chatStream` sur **#932** commence par `final localDenial = _localAiDenialCode;` et rejette `ProviderApiException(... statusCode: 403)` **avant** `_authService.getIdToken()` et l'envoi réseau. Sur **#938** isolée, `chatStream` appelle immédiatement `_authService.getIdToken()` puis construit `buildPatientSseRequest`, **sans ce garde local en tête de méthode**. Ceci n'annule pas les tests de transport POST/CSRF du hotfix, mais interdit de prendre #938 comme intégration complète du refus IA #24.
- `backend/core/middleware/triage_vital.py` sur #932 possède une interception spéciale de l'urgence SSE **avant** la vue ; #938 exclut expressément le stream du middleware et assure la réponse d'urgence SSE **dans la vue après auth/CSRF**. L'intégration doit préserver la seconde frontière tout en conservant le fonctionnement du chat canonique et du triage.
- Les deux `backend/ai/api/v1/ai.py::chat_stream` sont des POST JSON, mais #938 introduit l'urgence déterministe via `compose_emergency_for_patient` dans la vue.
**Test d'intégration obligatoire, pas encore exécuté :** refus local IA avant authentification/HTTP pour chat ET stream, ainsi que POST SSE urgence avec cookie/CSRF, Bearer natif et anonyme, sans PHI dans GET/log. Compléter la matrice avant un merge quelconque de la pile.


## 17. 12 octobre — branche d'intégration SSE + refus IA réellement créée, PR #939

**Goal :** réunir dans un même HEAD les garanties de consentement AI local #934 et d'urgence SSE après auth/CSRF #938, sans reprendre les régressions LLM du hotfix isolé. **Preuve GitHub :** [PR #939 DRAFT](https://github.com/hraaaaf/IAMINA-MVP/pull/939), branche `integration/v1-03-sse-optout-auth-20261012`, base **PR #934** à HEAD exact `f0b02165b478db6b6bb25d33f534a502ffa542f8` ; candidat **`bb25925d20517656238b8c14e2fe9c215ee42006`**, **6 fichiers** (3 modifications + 3 tests nouveaux), `ahead 6, behind 0` vérifié avant la PR.

**Contre-audit décisif avant portage :** la version `backend/ai/api/v1/ai.py` de #938 basée sur `main` réintroduit dans `/ai/summary` un appel à `_call_llm_for_summary(... full_pivot_text, report.patterns, ...)` et dans le Doctor Brief un `get_gateway_llm()` avec comptages patient ; la version #932/#934 avait retiré ces voies au profit des observations locales. Copier #938 intégralement serait donc une régression egress ; **interdit**. Le correctif a été porté **uniquement sur le bloc urgence `chat_stream`**, selon la version #938, tout en conservant `project_public_kpis`, `report.insights`, `build_local_doctor_brief`, le fallback `AIProcessorPolicyDenied` et le contrôle local `_localAiDenialCode` du frontend **avant** `getIdToken()`. Le middleware SSE pré-auth a été retiré, l'urgence est maintenant un SSE canonique après auth. La matrice tests #938 (POST JSON, cookie/Bearer/CSRF, 405 GET sans redirect/provider et journal triage sans snippet patient) est incluse.

**Preuve locale de revue source :** **9/9 invariants statiques contrôlés sur le nouveau SHA** ; ni lint ni tests réels revendiqués. Le premier [workflow Companion `38249745829`](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38249745829) était `in_progress` à la première inspection ; aucune conclusion CI globale encore acquise. Autres workflows potentiels à découvrir sur le nouveau HEAD, puis si échecs examiner jobs exacts et corriger.

**Next exact :** obtenir verdict des tests backend SQLite/PG, frontend/opt-out et captures ; si vert comparer l'intégration #939 avec #937 dormant + option PWA version distincte, puis tests intégrés sur HEAD réconcilié. Les validations clinicien OCR, vrai appareils, ingress rétention et distribution sont encore des human/external gates. PR #938 conserve son CI vert *séparé*, mais **#939 n'est pas encore certifiée**. Aucun merge, Vercel, données patient. `NOT_RELEASE_AUTHORIZED`.


## 18. 12 octobre — exécution parallèle réelle : PR #939 (SSE+opt-out), #940 (version PWA)

**Piste SSE + refus IA, preuve de code** : [PR DRAFT #939](https://github.com/hraaaaf/IAMINA-MVP/pull/939), HEAD **`bb25925d20517656238b8c14e2fe9c215ee42006`**, base #934 `f0b02165`, diff **6 fichiers**, 9/9 invariants statiques vérifiés. Portage **du seul bloc d'urgence SSE** #938 dans `ai.py` de #934 : garde opt-out avant Bearer/HTTP préservée, résumés/Doctor Brief déterministes préservés, refus média tiers fail-closed, urgence SSE après auth/CSRF, triage middleware ne bypass plus le stream, trois tests backend synthétiques inclus. **Pourquoi cette approche :** portage brut de `ai.py` #938 aurait réintroduit le formatage LLM des motifs/résumés patient et Doctor Brief avec données patient, un recul majeur de la politique V1-03. Premier contrôle GitHub #939 : Companion [`38249745829`](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38249745829) `completed/success`. **Pas** de succès CI backend/Flutter exact-HEAD établi par ce seul run ; la PR est basée sur #934 et les triggers de CI dépendent de leur filtre de branche.

**Piste client PWA, preuve de code** : [PR DRAFT #940](https://github.com/hraaaaf/IAMINA-MVP/pull/940), HEAD **`9fd74783b7413a19113e35e6afd4322b94f89709`**, base #934 `f0b02165`, diff **6 fichiers**, 7/7 invariants source vérifiés. Version d'essai `0.1.0+2` dans pubspec, SW `IAMINA_CACHE_SCHEMA`, bootstrap fallback ; backend politique `DEFAULT_LATEST_BUILD=2`, minimum build 1 (ancien GET **non déclaré sûr**), test Python `current` vs `update_available` et trois tests Dart triplet/méthode POST/no-cache API. Aucun forced-update inventé. Premiers runs : FRUG-1 [`38250503015`](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38250503015) et UI screenshot [`38250502950`](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38250502950) `in_progress` au premier contrôle. **Pas de preuve** d'upgrade d'une vraie PWA installée ; workflow spécialisé P5-4A est filtré pour PR vers `main`, pas nécessairement déclenché sur #940 enfant de #934.

**Coordination** : ces PR sont candidates indépendantes, jamais des productions. Prochain lot autonome = branche d'intégration combinée `#939 + #940 + #937` en conservant autorité SSE post-auth, refus AI avant transport, chemins P3 dormants, version PWA distincte et protections LLM de #932 ; **ne pas lancer inutilement une batterie lourde pendant que GitHub est occupé sur #940**. Au point de convergence : CI réellement déclenchée sur HEAD intégré et tests P5-4A upgrade ancien→nouveau, préservation locale, optout multi-plateforme/clinique/ingress. Merge et Vercel nécessitent toujours des autorisations explicites.

**Statut :** `INTEGRATION_DRAFTS_OPEN / CI_PARTIAL / NOT_RELEASE_AUTHORIZED`. Aucune validation clinique, infra log ou migration parc réel revendiquée.


## 19. 12 octobre — convergence exécutée : #941 DRAFT sur main, 25 workflows déclenchés

**Goal :** prouver les protections V1-03 sur un seul HEAD après travail parallèle, sans aucune donnée patient réelle, sans merge ni déploiement. **PR d'intégration [#941](https://github.com/hraaaaf/IAMINA-MVP/pull/941)** OPEN/DRAFT, branche `integration/v1-03-sse-optout-pwa-p3-20261012`, base `main@13b7cce12c86daf60119fb703f22e8c6c192cf8d`, HEAD exact **`22ff929624c3860446b58ce6130852594d3060ed`**. Comparaison avec `main` : ahead **159**, behind **0**, **87 fichiers cumulés des PR parentes** ; depuis #939 `bb25925d` : 12 commits, 12 fichiers supplémentaires issus de #937 et #940, et seulement eux.

**Constitution et preuves avant CI :**
- Base #934/#932 avec refus AI `_localAiDenialCode` **avant Bearer/HTTP**, SSE POST JSON sans santé en URL, résumé/Doctor Brief déterministes sans `get_gateway_llm()` et refus média tiers fail-closed.
- Correctif #939 : bloc urgent `chat_stream` de #938 **après auth/CSRF**, `compose_emergency_for_patient`, suppression du pré-triage SSE en middleware. Tests synthétiques GET 405, cookie+Bearer/CSRF, POST JSON/urgence/aucun fournisseur, sans PHI de log.
- Contrat P3 option A de #937 : `diabetes.api.main` ne monte plus les routeurs via registre, manifeste/ready reflètent routes exposées ; tests P3 404/absence OpenAPI/Django resolver/urgence/bootstrap.
- Contrat d'essai PWA de #940 : version Flutter/SW/bootstrap `0.1.0+2`, version minimum API `0.1.0+1` et latest build 2 ; **pas de forced upgrade** avant inventaire distribué, mais tests version/parité POST/API cache.
- **11/11 invariants source vérifiés à HEAD `22ff9296`** (les invariants ne sont pas des tests runtime ni une validation clinique). Le code main-based #938 n'a **pas été recopié en entier** dans `ai.py` pour ne pas réintroduire des appels LLM sur données patient.

**Premier contrôle exact-HEAD GitHub #941 : 25 workflows démarrés**, 0 succès global déclaré. Quelques runs critiques :
- [CI `38251414965`](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38251414965) **queued** au premier contrôle (backend SQLite+PostgreSQL/Flutter).
- [Django migration drift `38251414824`](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38251414824) **queued**.
- [P5-4A PWA update and recovery proof `38251414930`](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38251414930) **queued**.
- [P5-4A PWA offline app-shell proof `38251415007`](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38251415007) **queued**.
- [P5-5 End-to-End Pilot Rehearsal `38251414964`](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38251414964) **queued**.
- [Companion chat E2E `38251414823`](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38251414823) **in_progress**.
Les vingt-cinq runs sont à examiner **une fois après travail documentaire indépendant**, puis toute failure → logs/diagnostic/correctif/recertification sur **nouveau HEAD**. Ne pas confondre les succès isolés #938, #939 (Companion seulement), #940 (FRUG/UI seulement) avec validation #941.

**Gates ouverts même en cas 25/25 vert :** mise à jour effective des PWA anciennes et vrais iOS/Android, inventaire de distribution par build, ingress/CDN/APM/WAF et politique des logs/drains/rétention, clinician OCR HI/LO/401–600, revues privacy/sécurité/clinique, captures UI BEFORE/AFTER mêmes viewports + regard indépendant, et coupure backend/frontend/rollback sans réintroduire GET. Les validations de mise en production restent humaines : approbation de **merge** puis autorisation **Vercel séparée**. Aucun déploiement ni donnée patient manipulée.

**Statut : `INTEGRATED_DRAFT_CI_RUNNING / NOT_MERGED / NOT_DEPLOYED / NOT_RELEASE_AUTHORIZED`.** Prochaine action : analyser les verdicts exacts du run #941 après travail indépendant ; si rouge corriger, si vert préparer revues/compatibilité sans déclarer V1-03 close. P5 historique 6/12=50 %, pas un % V1-03.


## 20. 12 octobre 2026 — PR #941 première CI rouge, correctif ciblé et recertification

**PR intégrée** [#941](https://github.com/hraaaaf/IAMINA-MVP/pull/941), branche `integration/v1-03-sse-optout-pwa-p3-20261012`, toujours DRAFT/non fusionnée. Le **HEAD original** `22ff929624c3860446b58ce6130852594d3060ed` a produit 25 workflows : au contrôle après exécution, 15 réussis, **1 en échec**, 9 en cours. Échec [Developer portability `38251414829`](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38251414829), job macOS `114818413128` : **2862 passés, 3 échecs, 5 ignorés, 3 xfailed** (186 subtests). Le backend CI [`38251414965`](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38251414965) a aussi rendu **2 échecs** : PG **2867 passés / 2 échoués** ; SQLite **2863 passés / 2 échoués**. Frontend de cet ancien run annulé après nouvelle révision, donc jamais compter comme vert.

**Diagnostic exact et corrections limitées aux tests :**
1. `backend/core/tests/test_v1_03_sse_post_privacy.py::test_urgent_post_stream_returns_canonical_sse_not_json` attendait une entrée `CRITICAL` du middleware de pré-auth ; le comportement intentionnel du code intégré est maintenant **pas d'interception avant auth**, donc **pas de log middleware** pour SSE. Test réécrit pour vérifier l'absence de cet appel de journalisation et conserver les assertions SSE canonique, `is_emergency`, `no-store`, provider non appelé.
2. Dans le même fichier, `test_urgent_post_preserves_sse_and_no_patient_message_logging` patchait `core.middleware.triage_vital.evaluate_input_safety`, qui ne traite plus la route SSE ; fausse urgence, événement non JSON, échec. Patch désormais `core.input_safety.evaluate_input_safety` réellement utilisé dans la vue authentifiée, et assertion `critical_log.assert_not_called()` pour absence de log patient pré-auth ; le test exige toujours `is_emergency`, `token` et `[DONE]`.
3. `backend/evaluation/test_clinician_prep_protected_shadow_benchmark.py::test_benchmark_module_imports_standalone_with_django_setup` : sous macOS host, la sous-exécution `python -c import evaluation...` partait de la racine repo, sans `backend` dans `sys.path`, `ModuleNotFoundError`. Correctif **harness-only** : `cwd=Path(__file__).resolve().parents[1]` qui pointe sur `backend`, sans modifier le code applicatif ni assouplir `assert result.returncode == 0`.

**Deux commits de correction** : `89327df0eb4f01119c4eb1bd823eb5484fdcf69f` et `d3562e814e39d412516f421e66cb285fa7df50ce`. **Nouveau HEAD exact #941 : `d3562e814e39d412516f421e66cb285fa7df50ce`.** Vérification source des trois tests : assertions de refus journalisation et invariants SSE conservés, assertion subprocess intacte ; **réussite runtime NON ENCORE DÉMONTRÉE** au premier relevé.

**Recertification automatique sur le nouveau HEAD** : [CI `38252290789`](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38252290789) initialement queued, [Developer portability `38252290702`](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38252290702) initialement pending, [P5-4A PWA update `38252290695`](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38252290695) queued, 25 nouveaux workflows total (20 queued / 5 pending au premier contrôle). Ces nouveaux runs **supplantent** les conclusions des anciens SHAs ; ne pas reporter les anciens verts sur le nouveau HEAD. **Next exact :** une inspection des conclusions/jogs sur `d3562e8` après travail documentaire, échec → logs et correction, si vert → préparation revue humaine clients/logs/clinique. Pas de merge ni Vercel, pas de PHI.

**Statut : `DRAFT / NEW_CI_RUNNING / NOT_MERGED / NOT_DEPLOYED / NOT_RELEASE_AUTHORIZED`.** 29 décisions V1 distinctes du suivi historique P5 6/12 = 50 %.


## 21. 12 octobre — PR #941 HEAD d3562e8 : CI centrale verte, deux harness externes isolés

**Relevé factuel GitHub Actions** sur [PR #941 DRAFT](https://github.com/hraaaaf/IAMINA-MVP/pull/941), HEAD **`d3562e814e39d412516f421e66cb285fa7df50ce`** : **25/25 workflows terminés, 23 SUCCESS et 2 FAILURE au premier passage**. Les deux échecs sont **P5-4A PWA update and recovery proof** `38252290695` et **TD-008 device integration baseline** `38252291102`. Les deux seuls runs ont été relancés via GitHub **rerun failed jobs** sur le MÊME HEAD ; demandes GitHub acceptées. Pas de commit supplémentaire, pas de nouvelle vague complète.

**Preuves fortes du candidat intégré :**
- [CI `38252290789`](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38252290789) **SUCCESS, 6/6 jobs** : SQLite **2865 passed, 5 skipped, 3 xfailed et 186 subtests passed** (job `114822678044`) ; PostgreSQL **2869 passed, 1 skipped, 3 xfailed et 186 subtests passed** (job `114822678372`) ; Flutter **688 passed, 1 skipped** et **`Built build/web`** (job `114822678225`). Aucune régression prouvée des gardes SSE/CSRF, refus AI avant réseau, P3 dormant et contrôle de version dans ces suites.
- [Developer portability `38252290702`](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38252290702) **SUCCESS** : launcher Windows, launcher macOS et **suite macOS host** verts après corrections des tests.
- Migrations Django, P5-5 rehearsal, PWA browser persistence, PWA offline app-shell et parcours UI synthétiques : **SUCCESS** au même HEAD.
- **PWA update `38252290695`** job `114821404776` : build Flutter de probe terminé, puis Chrome CDP localhost `:9225` est resté inaccessible pendant le délai de démarrage `50×0.2s` dans le shell ; aucune suite Chrome P5-4A enregistrée pour cet essai, aucune preuve de casse fonctionnelle de mise à jour. Le P5-4A recovery était **SUCCESS sur le HEAD précédent #941 `22ff9296`**, mais ne pas transférer ce succès comme preuve sur le nouveau HEAD ; relance limitée en cours.
- **Android `38252291102`** job `114821406455` : émulateur API 35 `x86_64` sur runner sans `/dev/kvm`, lancé `-accel off`, boot annoncé après **469537 ms**, puis `adb shell input keyevent 82` retourne **`Broken pipe (32)`** et code 224. Aucun test du parcours Android n'a été exécuté sur cet essai ; conclusion de qualification appareils **toujours INCONNUE**, pas un succès ni une régression applicative diagnostiquée. Relance exacte limitée acceptée.

**Next exact :** regarder la conclusion des deux tentatives de relance **une fois**, après le travail documentaire indépendant. Si nouveau échec CDP/ADB identique, abandonner la répétition et fiabiliser la disponibilité/diagnostic du runner dans un lot harness ciblé ; ne pas désactiver le test ni abaisser le seuil. Si verts, inscrire **25/25 seulement pour le nouveau HEAD exact et la tentative**, sans déduire validation clinique/équipements réels. Les gates clients réellement distribués, ingress/logs/drains/rétention, clinicien OCR et revue indépendante demeurent.

**Statut : `INTEGRATED_CI_CORE_GREEN / RETRY_TWO_HARNESSES / NOT_MERGED / NOT_DEPLOYED / NOT_RELEASE_AUTHORIZED`.** Aucun accès PHI, aucune action Vercel.


### 21a. Nouvelle preuve PWA : seconde tentative Chrome VERTE sur le même commit

Après la première tentative P5-4A rouge sur lancement Chrome CDP, GitHub `rerun failed jobs` du [run `38252290695`](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38252290695) a produit le job **`114830462759` `completed/success`**, au **même HEAD intégré `d3562e8`**. Étapes `Prove startup-driven failed-update safety and healthy activation in Chrome` et `Upload retained update/recovery proof` réussies. Artefact **`p5-4a-pwa-update-recovery-proof`** ID `11749571584`, SHA-256 archivé `46ec08bf51bc721c8ef7cf00bdc9a804cddbee5e31bd02ca1314b77fcbd9a20e` ; preuve limitée à l'upgrade PWA **synthétique en Chrome CI**, pas un parc PWA réellement diffusé.

**Décompte des workflows #941 après cette tentative : 24/25 prouvés verts**, sous réserve de dernière tentative Android **job `114830488188` `in_progress`** lors du contrôle. Aucun nouveau commit candidat ni déclenchement supplémentaire. Next : lire verdict Android, puis si vert signer le closeout CI technique **25/25**, tout en gardant les gates terrain/privacy/clinique et autorisations de release. Si l'émulateur échoue encore au boot/ADB, changer de stratégie harness sans affaiblir tests.


## 22. 12 octobre 2026 — CI d'intégration #941 CERTIFIÉE 25/25, pas d'autorisation de sortie

**Résultat exact** : [PR #941 DRAFT](https://github.com/hraaaaf/IAMINA-MVP/pull/941), HEAD **`d3562e814e39d412516f421e66cb285fa7df50ce`**, base `main`, **25/25 workflows associés à ce commit `completed/success`** confirmés via GitHub Actions. Pas de commit supplémentaire sur #941 : le HEAD certifié reste inchangé. **Preuve complémentaire Android** : [TD-008 run `38252291102`](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38252291102), dernière tentative job **`114830488188` `completed/success`** ; étape `Run integration baseline on Android emulator` **completed/success**. C'est un **émulateur GitHub Actions**, pas une certification sur téléphone réellement utilisé ni un relevé du parc distribué.

**Autres preuves exact-HEAD déjà acquises** : [CI centrale `38252290789`](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38252290789), 6/6 jobs success ; SQLite **2865 passed, 5 skipped, 3 xfailed, 186 subtests** ; PostgreSQL **2869 passed, 1 skipped, 3 xfailed, 186 subtests** ; Flutter **688 passed, 1 skipped** + `flutter build web` ; [Developer portability `38252290702`](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38252290702) Windows/macOS success. [P5-4A update/recovery `38252290695`](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38252290695) après relance ciblée job `114830462759` success, preuve conservée en artefact `p5-4a-pwa-update-recovery-proof` ID `11749571584`. Migrations Django, P5-5 rehearsal, tests UI et persistance PWA success.

**Portée de la certification** : `TECHNICAL_CI_GREEN_25_OF_25` sur ce HEAD et ces workflows ; couvre les tests automatisés intégrés, **pas** la non-divulgation dans les logs ingress réels, **pas** la migration des clients SSE GET effectivement installés, **pas** les appareils physiques iOS/Android, **pas** une autorisation clinique OCR ou une revue sécurité/confidentialité externe. Aucun log ou donnée patient réel examiné.

**État Git et revues** : #941 est **DRAFT / OPEN / NOT_MERGED / NOT_DEPLOYED**, **0 soumission de revue indépendante recensée** à la validation. En particulier, ne pas fusionner des PR de base historiques en aveugle et ne pas activer l'OCR. Les preuves API/de sécurité ne se substituent ni au clinicien ni aux personnes responsables privacy/security.

**Next exact — gates restants, coordonnables en parallèle** :
A. QA terrain PWA ancien GET `0.1.0+1` vers POST `0.1.0+2`, clients réellement distribués et reprise offline/online ; inventorier les canaux/version/bindings et documenter le cutover sans redirection, retour au GET ou invalidation de consentement.
B. Vérifier sur périmètre autorisé la configuration exacte des ingress/CDN/WAF/APM/drains, règles et durée de journalisation des URL, avec marqueurs synthétiques uniquement ; exposition historique non traitée comme fuite de patient observée.
C. QA sur **appareils physiques** iOS/Android + PWA des refus IA persistants et hors ligne, auth/CSRF et parcours d'urgence ; revue sécurité/privacy indépendante.
D. OCR image glycémie reste OFF, demander preuve d'unité explicite, HI/LO/401–600 mg/dL, UI confirmation et évaluation qualifiée clinique sur corpus autorisé.
E. Préparer dossier de revue + stratégie merge sans régression ; **demander autorisation explicite du merge**, CI post-merge, puis **autorisation Vercel séparée**, smoke synthétique de deployment, closeout des docs canoniques. Même avec 25/25, **aucun merge ni Vercel automatique**.

**Verdict** : **CERTIFICATION CI TECHNIQUE #941 TERMINÉE** sur SHA `d3562e8` ; **LOT V1-03 GLOBAL NON CLÔTURÉ / NOT_RELEASE_AUTHORIZED** jusqu'aux gates terrain, clinique, privacy/security, merge/deploy. P5 global historique **6/12 = 50 %**, non réestimé par cette certification.


## 23. 12 octobre 2026 — RECTIFICATION propriétaire : ZÉRO CLIENT et architecture LOCAL-FIRST

**Information nouvelle et prioritaire du propriétaire : IAMINA a actuellement 0 client.** Cette information **annule les tâches de migration de clients existants** suggérées dans les sections historiques 15–22. Ne pas refaire un inventaire de clients, chercher des sessions patients historiques, ni attendre un cutover de parc inexistant ; ne pas présenter l'ancien code GET sur les builds de **revue/certification** comme une fuite réelle.

**Source de vérité que nous avions négligée** : `docs/LOCAL_FIRST_RUNTIME_BOUNDARY.md` établit que l'exécution patient est **local-first** (enrollment, stockage et actes cliniques locaux disponibles sans réseau) et que le Vercel `iamina-certified`/Django/Neon sert au **développement et à la certification**, hors runtime patient tant que l'architecture n'est pas changée. `docs/ROADMAP.md` §9 permet le développement et le merge de code après preuve, sans exiger avant chaque commit/merge les gates P5-6A/B qui sont exigés **avant la première donnée de santé identifiable**. Les déploiements Vercel nécessitent **toujours** une permission distincte et ne constituent pas une release patient.

**Autre contre-preuve historique à préserver** : le [dossier d'inspection du bundle web servi](../assessments/2026-10-11-v1-03-deployed-sse-url-privacy-divergence.md) indique que le **`main.dart.js` web effectivement inspecté** ne contient aucun `chat/stream` ; le parcours visible utilise `CompanionService` **POST /ai/chat**. `ApiClient.chatStream GET` existe **dans la source historique**, mais ne prouve pas l'usage du GET dans le web review, encore moins sur une clientèle. Le hotfix #941 reste un durcissement pré-lancement pertinent : GET 405, POST JSON, auth/CSRF, refus local.

**Goal révisé** : **premier lancement propre** à build `0.1.0+2` sur PWA/iOS/Android, avec test synthétique (enrollment sans réseau, persistance, consentement/refus AI, transport et reprise offline), garde OCR **OFF**. Aucun test de « migration client `0.1.0+1` » nécessaire pour un parc réel inexistant ; les tests SW de laboratoire sont des non-régressions utiles mais ne représentent pas un déploiement client.

**État des preuves** : [#941](https://github.com/hraaaaf/IAMINA-MVP/pull/941), HEAD `d3562e814e39d412516f421e66cb285fa7df50ce` **25/25 SUCCESS**, DRAFT non mergé/non déployé ; Android certifié **émulateur seulement**. Nouveau [dossier de pré-lancement/first install](../assessments/2026-10-12-v1-03-distribution-privacy-cutover-gates.md), version remplacée pour éliminer le faux blocage. Aucune revue indépendante de #941 constatée. Aucun appareil physique/patient ni conformité clinique/privacy déclarés validés.

**Séquence réelle** : qualification autonome sur installations **neuves synthétiques** → revue ciblée des protections et du merge (sans passer en revue de fausses données historiques) → **autorisation humaine merge** → CI post-merge/closeout → **autorisation Vercel distincte seulement si déploiement dev/cert souhaité** → **avant première donnée identifiable** : nouveau freeze SHA, P5-6A/#318 + P5-6B/#320, processeurs *effectivement* activés et topologie locale, audits fail-closed, validation de release humaine. L'avis clinique OCR reste un gate **d'activation OCR**, pas une condition qui force à interrompre du code dormant.

**Verdict corrigé** : `ZERO_CLIENTS / LOCAL_FIRST / CI_25_OF_25_GREEN / NO_EXISTING_CLIENT_MIGRATION / NOT_MERGED / NOT_DEPLOYED / NOT_PATIENT_AUTHORIZED` ; P5 historique 6/12 = 50 %, aucun nouveau % inventé.


## 24. 12 octobre 2026 — ZÉRO CLIENT, qualification première installation : PR #942 (tests dédiés)

**Goal exact** : certifier sur un build **neuf et local-first** qu'une première inscription et réouverture ne dépendent pas de Vercel/Django/Neon, qu'une mesure **synthétique** est conservée après fermeture/réouverture de SQLite **sur disque** et qu'un refus IA local persistant prévaut toujours sur un ancien reçu validé. Aucun client existant à migrer.

**Faits source** : `frontend/integration_test/pilot_critical_journeys_test.dart` couvrait déjà l'écran d'inscription locale et l'enregistrement glycémie, mais via `NativeDatabase.memory()` et `_FailingAuthService` simulé ; `docs/LOCAL_FIRST_RUNTIME_BOUNDARY.md` exige plus qu'un exercice mémoire pour attester le comportement local-first. Les tests de `ConsentEvidenceStore` existants vérifient la persistance logique d'un marqueur via `Mock<FlutterSecureStorage>`, pas le système de stockage d'un vrai OS.

**Implémentation exécutée** : [PR DRAFT #942](https://github.com/hraaaaf/IAMINA-MVP/pull/942), branche `test/v1-03-zero-client-first-install-offline-20261012`, **HEAD `5d3f4fa1e2fa1e6824c8046471611581a76ec05a`**, ancêtre exact de #941 `d3562e814e39d412516f421e66cb285fa7df50ce`. **Un seul nouveau fichier de test**, zéro code runtime/UI modifié : `frontend/test/services/v1_03_fresh_install_local_first_contract_test.dart`. Vérification GitHub `compare_commits(base=#941, head=#942)` : **2 commits / 1 fichier**, 8/8 invariants source de préparation. Trois essais :
1. `AuthService` vierge et storage mock : impossible de s'enregistrer avant init, session locale créée sans bearer/HTTP, conserve son ID après recréation, refus remote enrollment, signout vide marqueur/token, nouveau démarrage reste fermé hors réseau.
2. SQLite Drift fichier temporaire : `SYNTHETIC` glucose 123.0 enregistré localement en `pending`, fermeture/reconnexion de **deux instances SQLite sur le même fichier**, valeur présente sans synchronisation.
3. Refus IA : présence de profil et reçu précédent, refus persisté dans storage mock, `ConsentService` reconstruit avec refus local, `CompanionService` rejette avant HTTP ; témoin `networkCalls=0`.

**Portée honnête** : utilisation d'un mock `FlutterSecureStorage` ≠ expérience Keychain/Keystore réelle ; SQLite disque en test ≠ persistance sur appareils physiques, et aucun changement UI n'est apporté. L'exécution du nouveau fichier **n'était pas encore démontrée au premier pointage CI**.

**Certification déclenchée** : la PR #942 cible `main` pour déclencher la CI complète sur **ce nouveau HEAD**. Au premier contrôle, **25 workflows `queued`**, notamment [CI `38263636140`](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38263636140), [Developer portability `38263636060`](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38263636060), [Android TD-008 `38263635974`](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38263635974), [PWA update `38263635978`](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38263635978) et [P5-5 `38263636175`](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38263636175). Le **25/25 vert de #941** demeure un certificat de son SHA **distinct** ; ne pas l'étendre à #942. Avant benchmark lourd supplémentaire, vérifier GitHub en cours, puis échec → diagnostiquer et corriger, vert → closeout technique.

**Next exact** : analyser la première conclusion exacte #942, corriger uniquement si échec et recertifier ; qualifier ensuite une **installation vierge sur vrai PWA/iOS/Android** avec fixtures synthétiques et OS secure storage réel ; obtenir revue engineering ciblée et **autorisation humaine merge** (pas d'autorisation implicite). Vercel dev/cert demande un autre accord ; avant premier patient identifiable, reprendre P5-6A/B et les gates roadmap §9.

**État** : `ZERO_CLIENTS / LOCAL_FIRST_FIRST_INSTALL_TESTS_ADDED / PR942_CI_RUNNING / NO_MERGE / NO_DEPLOY / NOT_PATIENT_AUTHORIZED`. P5 historique `6/12=50%` inchangé.


## 25. 12 octobre — V1-01 repris en parallèle, 3 sous-chantiers CAL indépendants

Le propriétaire demande une exécution **en parallèle** des trois sous-lots non dépendants : CAL-09/10 **caractérisation UTC/jour clinique**, CAL-11 **source primaire USDA**, CAL-12 **isolation export PDF non certifié**. Le chantier prioritaire est de nouveau V1-01, conformément à la roadmap des 29 décisions. Aucun élément de V1-03 n'est automatiquement promu au statut « livré » ; la PR #942 first-install reste secondaire.

**Trois branches isolées depuis [#920](https://github.com/hraaaaf/IAMINA-MVP/pull/920) HEAD `81bf4d6ac4e182f3058ca6ff52b504ce8404beb9` (17/17 CI) :**
- `audit/v1-01-cal09-10-timezone-characterization-20261012` : **2 tests** `backend/diabetes/tests/test_v1_01_cal09_10_timezone_characterization.py` prouvant par oracles synthétiques les mêmes cinq instants avec 1 date UTC mais 2 dates UTC+1. Le code actuel `paired_meal_response._patterns` utilise `pre_at.date()`, avec seuils existants `MIN_OBSERVATIONS=3` et `MIN_DISTINCT_DAYS=2`. Aucun choix clinique patient (fuseau, jour, durée repas) imposé ; ce décalage produit une différence de statut et reste **gate clinique**.
- `audit/v1-01-cal11-usda-source-oracle-20261012` : script standard library `backend/scripts/validate_v1_01_cal11_fdc.py` + **8 cas pytest synthétiques** `backend/core/tests/test_v1_01_cal11_fdc_source_oracle.py`. Si l'archive JSON Foundation April 2026 est fournie, le script refuse IDs FDC pomme/banane manquants, dupliqués ou liés à une description incohérente, mauvais nutriment glucides 1005/unité et quantités hors bornes catalogue ; **aucun chiffre nutritionnel modifié ou certifié** car téléchargement du zip officiel infructueux (URL primaire `https://fdc.nal.usda.gov/download-datasets/`); grammes banane `110–115` également non certifiés.
- `audit/v1-01-cal12-pdf-quarantine-20261012` : test Flutter dans `frontend/test/services/local_report_pdf_test.dart`, bloque les `import`/`export` depuis `frontend/lib` de la primitive ASCII non typée `LocalReportPdf`, indépendamment du scanner des appels directs. **PDF clinique en Unicode/RTL toujours inactif/non certifié**.

**Convergence sans campagnes redondantes** : [PR #943 DRAFT](https://github.com/hraaaaf/IAMINA-MVP/pull/943), branche `integration/v1-01-cal09-cal11-cal12-parallel-20261012`, HEAD exact `f7ebe654cd69a03acf6a3694ff0633e8a5b5042e`, 4 commits/4 fichiers vs #920. CI GitHub PR `main` : **17 workflows déclenchés**, 11 in_progress / 6 queued au premier contrôle, main [run `38268340588`](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38268340588). Succès CI non encore établi, aucun changement runtime/UX, aucune donnée patient.

**Next exact** : examiner CI 17/17 sur le commit intégré, corriger toute erreur de test/ruff, refaire une seule certification sur le HEAD corrigé si besoin, continuer USDA primaire et matrice de décisions cliniques. Les revues qualifiées et autorisation de merge sont de vrais human gates ; Vercel distinct et interdit sans autorisation. Tracker Notion source : 29 arbitrées, 0 complètement livrées, #19/#22/#28 en cours. P5 historique 6/12 = 50 % distinct.


## 26. 12 octobre — V1-01 #943 : CI exacte CERTIFIÉE 17/17 (3 travaux parallèles)

**Goal atteint, sous-périmètre technique seulement :** trois contrôles CAL indépendants, intégrés sur une unique PR et certifiés sans comportement clinique ou UX modifié. [PR #943 DRAFT](https://github.com/hraaaaf/IAMINA-MVP/pull/943), HEAD **`f7ebe654cd69a03acf6a3694ff0633e8a5b5042e`** ; GitHub Actions **17/17 `completed/success`**, vérifié sur ce SHA. [CI principale run `38268340588`](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38268340588) 6/6 jobs SUCCESS ; **backend SQLite 2 821 passed, 5 skipped, 3 xfailed et 141 subtests passed**, **PostgreSQL 2 825 passed, 1 skipped, 3 xfailed et 141 subtests passed** ; **Flutter 674 passed, 1 skipped, PWA `Built build/web`**. Migrations, parcours et Chrome BEFORE/AFTER aussi SUCCESS. L'ancienne #920 est toujours DRAFT et non mergée ; cette PR ne l'a pas fusionnée.

**Étendue précise :**
- CAL-09/10 : la divergence descriptible `_patterns` entre jour UTC et UTC+1 est démontrée par fixtures purement synthétiques, **politique clinique du jour et fuseau patient encore non arbitrée**.
- CAL-11 : script d'audit FDC `2026-04` et ses tests de validation d'archives *synthétiques* sont verts. L'[archive primaire USDA avril 2026](https://fdc.nal.usda.gov/download-datasets/) est bien publiée (JSON Foundation Foods 459K ; [journal de publication USDA](https://fdc.nal.usda.gov/log/)), mais récupération effective de ZIP **impossible** dans cet environnement (erreur de téléchargement et DNS) ; aucune comparaison officielle des **7 FDC IDs pomme/banane**, aucun poids portion ni valeur de glucides certifiés par cet audit.
- CAL-12 : scanner Flutter refusant `import` ou `export` du module PDF ASCII non typé depuis tout `frontend/lib` est testé, sans activation d'un PDF clinique Unicode/RTL/consentement.

**Statuts distincts :** `V1-01_SUBLOT_CI_CERTIFIED_17_OF_17` ; **décision produit #19 OPEN / V1-01 global PAS CLOS**. Aucune revue externe clinique/privacy/FR-AR-Darija/RTL constatée, aucun merge, Vercel ni usage patient. Tracker 29 décisions : 0 livrées complètement, #19/#22/#28 en cours au dernier registre ; P5 global 6/12=50 % distinct.

**Next exact :** validation de la provenance alimentaire via source USDA réelle (ou API officielle avec clé autorisée) puis corriger toute référence fausse en fail-closed ; arbitrage humain qualifié du jour clinique et des fenêtres de repas, revue de contrats export/consentement et copie multilingue ; matrice numérique CAL-01–12 par producteur/consommateur et intégration des décisions #22. Après revue, demander autorisation merge, post-merge et closeout canonique ; Vercel demande consentement distinct. Aucune décision clinique auto-déduite d'un test de caractérisation.


## 27. 12 octobre — CAL-11 : source USDA primaire téléchargée, parsing corrigé, DNS intermittent

- **PR #943 certifiée** : `f7ebe654cd69a03acf6a3694ff0633e8a5b5042e` 17/17 SUCCESS, non mergée. **PR #944 DRAFT** : `e77304be0d049516f4d8b07914427ae3ebe9552d` nouvelle preuve ciblée pour CAL-11 ; aucun runtime clinique modifié.
- **Premier run [38272356607](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38272356607)** : ZIP **officiel USDA Foundation Foods 2026-04-30 téléchargé et testé valide**, SHA enregistré en artefact GitHub [11756709069](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38272356607/artifacts/11756709069) ; validation bloquée avant lecture des IDs par **placeholders JSON `null` dans `FoundationFoods`**.
- **Correction** : le script `backend/scripts/validate_v1_01_cal11_fdc.py` élimine désormais exclusivement ces `null` et continue de refuser chaînes, objets mal formés, doublons et nutriments ambigus ; deux tests d'oracle ajoutés. Commit exact `e77304be0d049516f4d8b07914427ae3ebe9552d`.
- **Nouveau run [38272863911](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38272863911)** : première tentative échouée **DNS `curl: (6) Could not resolve host: fdc.nal.usda.gov`**, avant comparaison des IDs. **Relance du seul job en échec acceptée**, pas de changement produit. Si DNS rééchoue, ne pas répéter en boucle : récupérer de manière contrôlée l'archive primaire depuis un réseau autorisé, conserver SHA et rejouer le validateur hors ligne.
- **CAL-11 toujours OPEN** tant que les sept IDs pomme/banane ne sont pas rapprochés des lignes source officielles et que le poids portion n'est pas sourcé ; échec réseau ≠ erreur nutritionnelle. Le dossier clinique [CAL-09/10/11/12](../assessments/2026-10-12-v1-01-cal09-cal11-cal12-decision-gates.md) présente les options du jour patient à faire approuver, ainsi que la quarantaine PDF ASCII. Zéro client et local-first, aucune autorisation merge/Vercel. Next : verdict de la relance, puis preuve source ou blocage externe précis.


## 28. 12 octobre — CAL-11 USDA source primaire réconciliée / #945 CI lancée

**Résultat important depuis §27** : téléchargement GitHub de l'[artefact primaire USDA #11758012445](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38273801139/artifacts/11758012445), archive source ZIP `FoodData_Central_foundation_food_json_2026-04-30.zip` SHA-256 **`186e988ec542e913f51ef62b86a47758e8cdd0d1dc3889e7b055581f3c09c77a`**. Inspection complète `FoundationFoods` : 395 entrées brutes avec `null`, 363 IDs non nuls. Les **7 IDs fruits du catalogue historique absents** de ce snapshot ne sont pas des nombres vérifiables avec cette édition. Confrontation directe des lignes **2026 présentes** au nutriment USDA `id=1005`, unité `g`, familles et poids :
- pomme `1750339=14.8`, `1750340=15.7`, `1750341=14.8`, `1750342=14.1`, `1750343=14.7` g/100g ;
- banane `1105073=20.1`, `1105314=23.0` g/100g ;
- portions réelles source `foodPortions` `Banana/Peeled` **110 g** pour `1105073`, **115 g** pour `1105314`.

**Correction effective sur branche DRAFT** [#945](https://github.com/hraaaaf/IAMINA-MVP/pull/945), HEAD `a061ba035f2e7bcfa2c14e21b7b0aa3b9968ad87` : `frontend/lib/core/data/nutrition_catalog.dart` **7 IDs remplacés**, pomme min **14.2→14.1** (vérité source), banane 20.1–23.0 et 110–115 g inchangés mais désormais **preuve primaire exacte** ; `backend/scripts/validate_v1_01_cal11_fdc.py` ajoute contrôle strict des poids `Peeled`, accepte `unitName='g'`, tests Python/Dart mis à jour ; tableau SHA+7 lignes dans [audit CAL-11](../assessments/2026-10-12-v1-01-cal11-official-source-reconciliation.md), sur #945. **Aucune inférence de dose médicale, changement de formule ou donnée patient.**

**Vérification croisée indépendante déjà passée contre l'archive ZIP retenue** : les sept IDs, descriptions, quantité glucides, unité, deux poids banane concordent. Le [run primaire #38281623476](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38281623476) et [CI complète #38281623510](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38281623510) étaient **queued** au premier contrôle. **Ne pas transférer le 17/17 de #943** vers cette nouvelle correction de catalogue. Échec → diagnostic exact, correction sous SHA nouveau ; vert → QA présentation des nombres BEFORE/AFTER, score fondé sur screenshots réels ; pas de certification clinique globale implicite.

**Statuts** : `CAL11_PRIMARY_ROWS_7_OF_7_VERIFIED / PR945_RUNTIME_PATCH_DRAFT / PR945_CI_PENDING / NOT_MERGED / NOT_DEPLOYED`. CAL-09/10 jour/fuseau clinique et CAL-12 PDF typé Unicode/RTL **toujours ouverts**, imposer une validation qualifiée avant changement de ces comportements. P5 historique 6/12=50 % et tracker V1 0/29 complètement livrées restent distincts.

**Next exact :** suivre seulement source runner #38281623476 et CI #38281623510, puis revoir les deltas numériques UI et préparer revue nutritionnelle ; aucune demande de merge/Vercel à ce stade.
