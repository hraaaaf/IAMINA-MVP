# IAMINA — HANDOVER CANONIQUE V1-01 / Décision produit #19

## Désignation des relecteurs par rôle — 12 octobre 2026
Comité de six sièges défini dans [GitHub issue #946](https://github.com/hraaaaf/IAMINA-MVP/issues/946) : R1 clinicien endocrinologue (CAL-09/10 et CAL-12), R2 diététicien (CAL-11), R3 DPO santé (CAL-12), R4 relecteur médical FR/AR/Darija (CAL-11/12), R5 auditeur QA indépendant (CAL-09/10/11/12) et R6 responsable produit IAMINA (arbitrages et permissions séparées). **Aucune identité réelle ni acceptation de mandat n'a été vérifiée et 0 signature a été recueillie.** CAL-09/10/11/12 restent bloqués au gate humain, PDF OFF, #945 DRAFT. Next : trouver/mandater les titulaires, collecter avis signés; aucun merge ni Vercel.

## GATE HUMAIN — DOSSIER FORMEL PRÊT (12 octobre 2026)
**Dossier de relecture document-only :** [CAL-09/10/11/12 — options et cases de signature](../assessments/2026-10-12-v1-01-clinical-review-gates.md), publié sur la PR docs #933 `77fdd246cb7de88e2697243069261d518d935111`. **Aucun relecteur médical, diététique, privacy ou linguiste n'a encore signé**. CAL-11 : choix de portée de l'intervalle USDA; CAL-09 : sens du jour UTC/IANA/offset; CAL-10 : durée pré/post repas non bornée; CAL-12 : contrat PDF clinique typé, consentement et Unicode/RTL (PDF patient OFF). Aucune de ces options n'est approuvée par ce document.
**Référence QA inchangée :** PR #945 HEAD `90855610f02d6e8d058527ec084cf5c853ef23ba`, 19/19 verts, Chrome 18/18 sans pageerror, USDA vérifié. **Next exact :** désigner des relecteurs qualifiés, collecter décisions signées et restrictions; ensuite tests/corrections sur nouveau SHA, puis autorisation explicite de merge, revue post-merge et Vercel distinct. **Human gate réel : aucun merge ni déploiement.**

## 🔒 ACTUALISATION LIVE CERTIFIÉE — 12 octobre 2026, 21h46 UTC — **LIRE AVANT SECTIONS HISTORIQUES**
**Source de vérité actuelle :** [PR #945 DRAFT](https://github.com/hraaaaf/IAMINA-MVP/pull/945) sur `fix/v1-01-cal11-usda-2026-official-source-map-20261012`, HEAD exact **`90855610f02d6e8d058527ec084cf5c853ef23ba`**. GitHub `get_pr_info` confirme **OPEN, DRAFT, merged=false, mergeable=true, base main**. Aucun merge ni Vercel/patient.

**Goal technique CAL-11 :** corriger les bornes des glucides USDA pomme 100 g et montrer de vraies captures navigateur FR/EN/AR à 3 tailles avant/après sans exception JS. **Succès observable vérifié :**
- **19/19 workflows `completed/success` sur ce même HEAD** ; [CI principale #38306271658](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38306271658) **6/6 jobs success** (backend SQLite/ruff+pytest, PostgreSQL, frontend Flutter analyse/tests/PWA, hygiene, scope, PR size); [oracle primaire USDA #38306271271](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38306271271) SUCCESS.
- [Chromium dédié #38306271368](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38306271368), job `115000961311`, **SUCCESS**, exécute **14 tests Flutter dédiés** puis scénarios navigateur BEFORE/AFTER sur **FR/EN/AR × 390×844, 768×1024, 1280×900**.
- **Artifact réellement téléchargé et inspecté :** [`cal11-apple-100g-before-after-18-png` #11773107560](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38306271368/artifacts/11773107560), archive SHA-256 **`f96fc5a14ae4f183fb25eafa4fd612e0b2c5a590600e7a7437a5200bf4a56bcf`** (rétention GitHub jusqu'au **2026-11-02**). **18/18** PNG vérifiés contre checksums SHA-256 enregistrés + dimensions, **18/18 `pageErrors: []`**, **18/18 `serviceWorkerRegistry.supported=true,count=1`**. Les anciens `flutter_bootstrap.js:122:26` / `registration.update()` apparaissaient uniquement lorsque le harness Playwright bloquait les Service Workers ; permettre leur enregistrement dans le banc et refuser tout `pageerror` a supprimé l'exception dans cet essai comparatif. Cela valide le **harness**, pas l'absence de tout défaut dans le produit complet.
- **Parité visuelle numérique 9/9 :** diff des PNG BEFORE→AFTER, pour chaque langue et viewport, bbox unique **7×11 px**, correspondant au chiffre borne basse pomme `14.2→14.1`; 53 pixels modifiés pour FR/EN et 55 pour AR. Pas de déplacement d'éléments détecté pour le **widget isolé**. Source USDA visible, chiffres lisibles, RTL Ar correct. **Score = 9/9 comparaisons de parité**, *pas* un score général UX ou validation clinique.
- Modifications sur #945 : `frontend/lib/core/data/nutrition_catalog.dart` et référence `docs/NUTRITION_DATA_SOURCES.md` réconciliées; test widget `frontend/test/l10n/nutrition_bidi_contract_test.dart`; mini-app UI en contexte isolé, capture Playwright, workflow CI et protocole `docs/assessments/2026-10-12-v1-01-cal11-apple-ui-parity-protocol.md`. Le dernier correctif `90855610` change **uniquement harness + protocole**, pas le runtime patient.

**VRAI GATE HUMAIN / NEXT EXACT (supplante la section 5 historique ci-dessous) :** demander validation indépendante de la pertinence de l'intervalle de cultivars USDA appliqué à une pomme générique et du libellé nutritionnel; arbitrage clinique + UX **CAL-09/10** sur le jour IANA patient vs UTC et durée post-prandiale (aucun choix implicite); décision clinique/linguistique/privacy **CAL-12** sur les champs PDF typés, consentement, Unicode/RTL FR/AR/Darija, **PDF patient OFF**. Revues privacy/sécurité/clinique et FR/AR/Darija; rationalisation PR #920/#943/#944/#945; **accord explicite distinct avant merge** ; Vercel séparément et sans données patients. Décision V1 #19 toujours **OPEN**, aucun déploiement. **P5 historique 6/12 = 50 %**, V1-01 non chiffré, 0/29 décisions complètement livrées au dernier registre.

**Important :** les sections 1–6 restantes documentent le premier handover historique sur `34dd3fb...` ; les anciens statuts 18/18 et « pas de captures » sont **supplantés**, ne pas les appliquer au HEAD `90855610`. Les points de gouvernance et risques cliniques demeurent pertinents.

---
**Point de reprise vérifié : 12 octobre 2026 — fin de campagne CAL-11**

> **Règle d'ouverture d'une nouvelle conversation :** lire CE fichier, puis vérifier en direct le HEAD de la PR #945, la CI exacte, les PR #943/#920, les revues et `docs/ROADMAP.md`. Les conclusions historiques sont des preuves sur leurs **SHA respectifs**, pas sur main. Ne pas relancer une campagne CI lourde si GitHub est déjà occupé. Aucun merge ni Vercel sans permission explicite.

## 1. Goal / succès observable / preuve

**Goal V1-01** : livrer la décision #19 de la roadmap produit V1 (29 décisions approuvées), avec fiabilité des calculs et de la présentation clinique : CAL-01…CAL-12 ; décision connexe #22 sur l'ordre des unités et des cibles. Le programme V1-01 est **EN COURS**, pas une release patient. L'utilisateur confirme **0 client**, architecture patient **LOCAL-FIRST** (référence `docs/LOCAL_FIRST_RUNTIME_BOUNDARY.md`), Vercel/Django/Neon utilisés seulement en dev/cert jusqu'à décision d'architecture contraire.

**Succès vérifiable à ce jour** : le sous-chantier **CAL-11** (provenance nutritionnelle USDA pomme/banane) est réconcilié contre l'archive USDA primaire officielle **et** a passé les tests automatiques **sur un même HEAD #945**. Ce succès **ne** signifie ni revue nutritionnelle clinique, ni qualité du futur PDF multilingue, ni clôture de toute la décision #19.

## 2. Git / branches / PR / CI : faits vérifiés

| Élément | HEAD / preuve | État exact |
|---|---|---|
| Repo / main base | `hraaaaf/IAMINA-MVP`, base des PR `main@13b7cce12c86daf60119fb703f22e8c6c192cf8d` | Aucun merge de ces DRAFT constaté |
| **PR #945 — CORRECTION CAL-11** | [PR #945](https://github.com/hraaaaf/IAMINA-MVP/pull/945), branche `fix/v1-01-cal11-usda-2026-official-source-map-20261012`, **HEAD `34dd3fbfab7c8b125f2097546ce18d1bbc3d5f58`** | **DRAFT/OPEN, NOT_MERGED. 18/18 workflows `completed/success`** |
| #945 — CI principale | [run `38282205019`](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38282205019), **6/6 jobs success** | SQLite **2831 passed, 5 skipped, 3 xfailed, 141 subtests** ; PostgreSQL **2835 passed, 1 skipped, 3 xfailed, 141 subtests** ; Flutter **675 passed, 1 skipped** + build web PWA |
| #945 — certificat primaire USDA | [run `38282204938`](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38282204938), job `114921970431` **success**, message **`SOURCE_ROWS_MATCH`** | Le ZIP public USDA **pinné SHA-256** a été réutilisé depuis l'ancien run certifié ; **7/7 FDC IDs + 2 portions Banana/Peeled vérifiés** |
| #945 — artefact preuve | [artefact `11761897278`](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38282204938/artifacts/11761897278) | Archive publique et rapport retenus temporairement (rétention workflow **30 jours**), à repinner/renouveler une fois expirés |
| **PR #943 — parallèles CAL-09/10, CAL-11 oracle, CAL-12** | [PR #943](https://github.com/hraaaaf/IAMINA-MVP/pull/943), HEAD `f7ebe654cd69a03acf6a3694ff0633e8a5b5042e` | **17/17 success**, DRAFT, non mergée ; cette CI couvre des oracles/harness, pas les arbitres médicaux |
| PR #920 — V1-01 origine | [PR #920](https://github.com/hraaaaf/IAMINA-MVP/pull/920), HEAD `81bf4d6ac4e182f3058ca6ff52b504ce8404beb9` | **17/17 success**, DRAFT/non mergée |
| PR #944 — ancienne tentative primaire | [PR #944](https://github.com/hraaaaf/IAMINA-MVP/pull/944), HEAD `aa908bf58a6954b5010ab0251206a3250ef5c809` | 17 success + 1 failure **ATTENDUE** : anciens IDs absents de Foundation 2026 ; **supplantée par #945**, ne pas fermer/merger avant rationalisation des PR |
| PR #942 — QA first-install | [PR #942](https://github.com/hraaaaf/IAMINA-MVP/pull/942), HEAD `5d3f4fa1e2fa1e6824c8046471611581a76ec05a` | DRAFT, **24/25 success, 1 failure PWA** ; **hors chemin critique V1-01** |
| PR #933 — documentation V1/V1-03 | [PR #933](https://github.com/hraaaaf/IAMINA-MVP/pull/933), branche `parallel/v1-03-ocr-ui-provenance-20261011` | DRAFT, docs uniquement, ce handover y réside ; ne pas inférer présence sur main |
| Revues indépendantes #943/#945 | GitHub PR reviews consultés | **0 review soumis** au point de reprise |

**Tous les chiffres de tests proviennent des logs des jobs GitHub #945, non d'une extrapolation à partir de l'ancien 17/17.** Les workflows autres que la CI principale et le certificat USDA ont aussi `success` au HEAD #945.

## 3. CAL-11 — ce qui a réellement été corrigé

**Source officielle vérifiée :** USDA FoodData Central *Foundation Foods JSON* `FoodData_Central_foundation_food_json_2026-04-30.zip`. ZIP primaire SHA-256 **`186e988ec542e913f51ef62b86a47758e8cdd0d1dc3889e7b055581f3c09c77a`**. Attention : checksum **du ZIP source** et checksum **de l'enveloppe d'artefact GitHub** sont distincts. Le run #945 vérifie le SHA source avant de lire les lignes. La récupération sur `fdc.nal.usda.gov` était intermittente (DNS), d'où l'utilisation de la copie publique issue du [run source `38273801139`](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38273801139).

| Aliment | FDC ID actuel dans snapshot USDA 2026-04 | Glucides, g/100 g | Portion pelée (source) |
|---|---:|---:|---:|
| Pomme red delicious | 1750339 | 14.8 | — |
| Pomme fuji | 1750340 | 15.7 | — |
| Pomme gala | 1750341 | 14.8 | — |
| Pomme granny smith | 1750342 | 14.1 | — |
| Pomme honeycrisp | 1750343 | 14.7 | — |
| Banane overripe | 1105073 | 20.1 | 110 g |
| Banane ripe/slightly ripe | 1105314 | 23.0 | 115 g |

**Sept anciens identifiants** pomme/banane ont été démontrés absents **du seul snapshot Foundation 2026-04** ; ne pas affirmer qu'ils n'existent dans aucun autre jeu de données. La [PR #945](https://github.com/hraaaaf/IAMINA-MVP/pull/945) a **remplacé les sept IDs**, changé la **borne basse pomme 14.2→14.1 g/100g**, conservé banane 20.1–23.0 et portions 110–115 g désormais associées aux lignes `foodPortions` sources. `backend/scripts/validate_v1_01_cal11_fdc.py` vérifie le nutriment FDC `1005`, grammes/100g, descriptions, valeurs, IDs et `Banana/Peeled` ; pytest et Flutter figent les invariants.

**Dossier de preuve (sur branche #945, pas main) :** [audit officiel CAL-11](https://github.com/hraaaaf/IAMINA-MVP/blob/fix/v1-01-cal11-usda-2026-official-source-map-20261012/docs/assessments/2026-10-12-v1-01-cal11-official-source-reconciliation.md). Ce correctif nutritionnel **ne** certifie pas la variabilité individuelle, une portion réellement consommée, la dose insulinique ou un bénéfice clinique.

## 4. Reste ouvert — trois pistes indépendantes

### A — CAL-11 vérification visuelle et revue

- **BEFORE** : capturer la présentation d'une estimation pomme avec l'ancienne borne `14.2` au commit #943, et la même vue/état à commit #945 avec `14.1`.
- **Goal** : montrer que seul le nombre et sa provenance changent, avec unité/arrondi/texte et intervalle lisibles FR/EN/AR ; sans fausse précision clinique ni valeur « recommandée ».
- **Mockup/référence** : présentation existante et tests Flutter du catalogue.
- **Implémentation** : déjà dans #945 ; **AFTER** : capture aux **mêmes viewports** que BEFORE, comparaison côte à côte et score visuel **seulement si captures effectivement inspectées**. Aucune capture de comparaison n'est encore prouvée ici.
- **Revue** : validation nutritionnelle et limites de l'étiquette « analytical » par relecteur qualifié ; sans revue, ne pas annoncer #19 livrée.

### B — CAL-09/10 fuseau et jour clinique

- `backend/diabetes/services/clinical/paired_meal_response.py` regroupe les épisodes par `pre_at.date()` ; tests #943 démontrent que les **mêmes cinq instants** donnent **1 date UTC et 2 dates UTC+1**, changeant la suffisance d'évidence avec seuil existant de 3 observations / 2 jours.
- **Décision qualifiée ouverte** : jour civil patient avec fuseau IANA explicitement choisi **(option technique préférée pour UX, pas politique médicale approuvée)**, jour UTC toujours affiché comme tel, ou offset-source si prouvé. Ne **pas** coder de règle médicale/fuseau par défaut (Casablanca n'est pas la zone de tous les patients).
- Tester DST, voyage, minuit, données de fuseau manquantes, Home/Reports/IAmina avec fixtures synthétiques et revue clinique/UX. Fenêtre `post_at > pre_at` sans limite clinique approuvée : ne pas inventer un cutoff.

### C — CAL-12 PDF clinique Unicode/RTL

- La primitive PDF `frontend/lib/services/local_report_pdf.dart` est **ASCII/non typée/quarantainée** ; #943 ajoute un test anti-`import/export` runtime, sans génération PDF clinique patient.
- Décision qualifiée ouverte : **schéma typé de mesures**, source/intervalle/consentement/destination, FR/AR/Darija Unicode/RTL, données absentes, confidentialité et revue linguistique/clinique. Garder la fonctionnalité patient **OFF** tant que ce contrat n'est pas validé.

**Source des arbitrages détaillés :** [matrice CAL-09/10/11/12](../assessments/2026-10-12-v1-01-cal09-cal11-cal12-decision-gates.md).

## 5. Next exact / Séquence restante / human gates

**Next exact autorisé en autonomie :** QA numérique **BEFORE/AFTER mêmes viewports** de l'estimation pomme #943 vs #945 (si navigateur CI ou machine de test disponible), recueillir captures/proof et note de score. Vérifier aussi que les tests UI ne présentent pas l'intervalle comme une dose ; si non atteignable, inscrire `BLOCKED_DEVICE_BROWSER`, poursuivre les audits non visuels. En parallèle, préparer une proposition de contrat **sans seuil médical** CAL-09/10 et PDF CAL-12 à soumettre à relecteurs qualifiés.

**Séquence restante :**
1. QA visuelle/source CAL-11 et revue nutritionnelle ciblée ; artefact USDA avant expiration.
2. Arbitrage qualifié **CAL-09/10** puis implémentation/harness, tests UTC/IANA/DST, CI nouveau SHA.
3. Arbitrage produit/clinicien/privacy/linguiste **CAL-12** ; seulement ensuite contracter le PDF Unicode/RTL et tests/snapshots.
4. Vérifier cohérence décision #22 unités→cibles et autres CAL-01…08 contre l'arbre intégré.
5. **Revues indépendantes** sécurité/privacy/clinique sur les fonctions actives ; ne pas confondre CI verte et approbation de traitement patient.
6. **Human gate merge GitHub**, explicite (pas encore accordé) ; rationaliser PR parentes #920/#943/#944/#945, vérifier absence de régression globale et CI post-merge, closeout docs/Notion/roadmap.
7. **Human gate Vercel distinct**, explicite si environnement dev/cert à déployer ; Vercel n'est pas le runtime patient V1. Avant **première donnée de santé identifiable** : freeze exact SHA, P5-6A/#318 et P5-6B/#320, topologie et processeurs réellement activés, décision de release humaine.
8. Après V1-01 : V1-02 (décision #28), puis terminer V1-03 (#24/#26/#28) et les lots V1-04…V1-11 selon la roadmap canonique. Travaux indépendants possibles en parallèle, une seule campagne lourde quand possible.

**Blocages réels** : décisions médicales/jour clinique, contrat PDF clinical/RTL/consentement, revues indépendantes et accès à banc navigateur ou appareil pour captures numériques réelles, **autorisation explicite merge et Vercel**. Pas de CI en cours observée pour #945 : elle est **18/18 succès**.

## 6. Gouvernance et état

- **29/29 décisions produit arbitrées** selon checklist Notion, **0/29 intégralement livrées au dernier relevé du registre** ; sous-travaux verts ≠ décisions livrées. Les décisions #19/#22/#28 sont en cours selon suivi précédent.
- **P5 historique : 6/12 = 50 %**, suivi canonique distinct de la roadmap des 29 décisions. Aucun pourcentage V1-01 inventé.
- **0 client** confirmé par le propriétaire. **Aucune donnée clinique réelle** requise pour l'audit. OCR clinique reste OFF dans V1-03, non un prérequis CAL-11.
- **PR #945 : `TECHNICAL_CI_CERTIFIED_18_OF_18` ; décision #19 `OPEN` ; état produit `NOT_MERGED / NOT_DEPLOYED / NOT_PATIENT_AUTHORIZED`.**
- **Dernières preuves écrites** : GitHub workflows, source USDA 2026-04, audit CAL-11 et ce handover. Les anciennes sections de suivi « CI queued » du dossier V1-03 sont **historiques et supplantées** par la présente synthèse vérifiée.

**FICHIER CANONIQUE PRINCIPAL À RELIRE :** `docs/handovers/2026-10-12-iamina-v1-01-cal-handover.md` — IAMINA V1-01 / CAL — **% V1-01 non certifié**.
