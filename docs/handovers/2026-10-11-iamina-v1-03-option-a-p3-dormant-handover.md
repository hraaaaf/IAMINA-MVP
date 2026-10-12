# IAMINA — Handover canonique de reprise V1-03 / P3 option A

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
