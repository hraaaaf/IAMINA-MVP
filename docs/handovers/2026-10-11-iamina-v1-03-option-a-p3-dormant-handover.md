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
