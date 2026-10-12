# IAMINA V1-01 — Décisions CAL-09/10, CAL-11 et CAL-12

> **ACTUALISATION PRIORITAIRE 2026-10-12 — CAL-11 SOURCE+CI VERTES :** [PR #945](https://github.com/hraaaaf/IAMINA-MVP/pull/945) `34dd3fbfab7c8b125f2097546ce18d1bbc3d5f58`, **18/18 success**, dont [certification USDA primaire `38282204938`](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38282204938) `SOURCE_ROWS_MATCH` et [CI `38282205019`](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38282205019) 6/6. Le ZIP officiel SHA256 `186e988ec542e913f51ef62b86a47758e8cdd0d1dc3889e7b055581f3c09c77a` confirme **7/7 IDs corrigés** et 110/115 g Banana/Peeled. Les sections antérieures qui disent « primaire indisponible », « run queued » ou « CAL-11 aucune référence certifiée » sont **historiques et supplantées pour #945**. La décision #19 reste ouverte jusqu'à QA numérique BEFORE/AFTER, contrat du jour clinique CAL-09/10, PDF CAL-12 et revues. [Handover V1-01 de reprise](../handovers/2026-10-12-iamina-v1-01-cal-handover.md). Aucun merge, Vercel ni usage patient.

**12 octobre 2026 — dossier de décision, PAS une certification clinique**

## 1. Source exacte et résultat

- **27/29 ?** La source de vérité du programme V1 est la checklist Notion de **29 décisions**, décision #19 « fiabilité clinique », #22 « unités avant cibles ». Aucune de ces décisions n'est intégralement livrée selon le registre au 12 octobre.
- **CI prouvée** : [PR #943 DRAFT](https://github.com/hraaaaf/IAMINA-MVP/pull/943), HEAD `f7ebe654cd69a03acf6a3694ff0633e8a5b5042e`, **17/17 GitHub Actions success** ; [CI `38268340588`](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38268340588) 6/6 : 2821 SQLite, 2825 PostgreSQL, 674 Flutter tests passed + build PWA. Tests sur fixtures SYNTHÉTIQUES uniquement. Aucune politique clinique ni valeur source réelle modifiée.
- **Validation primaire en cours** : [PR #944 DRAFT](https://github.com/hraaaaf/IAMINA-MVP/pull/944), branche `audit/v1-01-cal11-official-usda-runner-proof-20261012`, HEAD initial `268da2e48bbf06a38e484dfac895c495d292738b`. Nouveau workflow `V1-01 CAL-11 USDA primary-source verification` tente de télécharger directement l'archive officielle Foundation Foods `2026-04-30` sur GitHub, puis exécute l'oracle qui recherche les **7 FDC IDs** et vérifie nutriment `1005`, grammes/100g, famille et bornes. Succès non déduit de #943. Source officielle : https://fdc.nal.usda.gov/download-datasets/ ; mise à jour primaire : https://fdc.nal.usda.gov/log/.
- **Contrainte produit** : propriétaire confirme **0 client**, futur patient local-first ; aucun rebasage des calculs sur Vercel/Neon ni nettoyage de « données clients » inexistantes.

## 2. CAL-09/10 — jour clinique, observation et repas

**Code exact inspecté dans #920 :**
- `backend/diabetes/services/clinical/paired_meal_response.py::_patterns` utilise `pair.pre_at.date()` pour `distinct_days`. `MIN_OBSERVATIONS=3`, `MIN_DISTINCT_DAYS=2` viennent de `personal_response.py`. Les calculs de delta sont descriptifs et exigent un épisode repas explicitement lié ; le producteur ne limite pas la durée positive entre pré et post.
- `personal_response.py` utilise aussi `_event_at(entry).date()` (deux emplacements). `governed_longitudinal.py` utilise `item.observed_at.date()`. Aucun contrat explicitement approuvé de fuseau IANA patient n'est établi pour ces agrégations.
- Le test CAL-09/10 de #943 construit 5 observations aux **mêmes instants** : **1 jour UTC contre 2 jours UTC+01**, ce qui suffit à basculer le statut existant. **Ce test démontre une ambiguïté de sémantique, pas le fuseau correct.**

**Arbitrage qualifié requis avant changement de runtime :**

| Option | Signification | Risque / test indispensable |
| --- | --- | --- |
| **A — Jour civil du patient, fuseau IANA explicite** (*proposition technique à faire approuver*) | Capture de l'ID `Africa/Casablanca` ou autre zone **choisie/provenant de source approuvée**, et calcul de tous les jours cliniques à partir des instants UTC dans la zone sélectionnée. | Gérer décalages été/hiver, voyage, changement volontaire de zone, dates dupliquées/manquantes, source de la préférence et absence de zone ; cohérence Home/Reports/IAmina. Ne jamais inférer la zone depuis IP ni la fixer à Casablanca pour tout patient. |
| **B — Jour UTC universel** | Garder le comptage actuel quand les timestamps sont stockés UTC, le libeller sans ambiguïté « jour UTC ». | Le jour affiché peut ne pas être le jour vécu localement ; contradiction UI à évaluer cliniquement et en accessibilité. |
| **C — Offset de chaque mesure** | Grouper selon la date contenue dans l'offset d'origine (si effectivement persisté et fiable). | Un historique contenant plusieurs offsets peut créer des comptages non reproductibles, risques de voyage/DST ; aujourd'hui provenance offset non démontrée. |

**Décisions humaines ciblées** :
1. Choix A/B/C et provenance fiable d'un fuseau pour le journal et toutes les sorties CAL-09/10.
2. Sémantique du « jour » pour sufficience d'évidence : affichage, limites si source temporelle absente ou contradictoire, backward compatibility (0 client, migrations données de test uniquement).
3. Définition clinique et étiquetage de la *durée de paire repas* : actuellement n'importe quel `post_at > pre_at` est descriptivement calculé ; **ne pas imposer un cutoff arbitraire**. Si non approuvé, conserver `elapsed_minutes` explicite et les restrictions de causalité, sans présenter « réponse thérapeutique ».

**Acceptation vérifiable après arbitrage** : tests datés avant/après minuit local, frontières DST/voyages, `Z` vs offsets, absence de fuseau (fail-closed), comparabilité Home/Reports/AI synthétiques ; test de séparation patient, evidence density identique lorsque zone/période équivalente. Revue médicale et UX appropriées avant libellé patient.

## 3. CAL-11 — sept références nutritionnelles primaire USDA

**Nombres existants IAMINA #920 (non re-certifiés depuis archive officielle) :**

| Famille | FDC IDs déclarés | Glucides déclarés |
| --- | --- | --- |
| Pomme | `1105664, 1105547, 1105781, 1105430, 1105897` | `14.2–15.7 g / 100g` |
| Banane | `790774, 790991` | `20.1–23.0 g / 100g` |
| Portion banane | **aucun FDC ID portion vérifié** | `110–115 g` pelés (statut PROVENANCE NON CERTIFIÉE) |

**Gate exact** : archive USDA officielle `FoodData_Central_foundation_food_json_2026-04-30.zip`, SHA256 du fichier téléchargé, chaque identifiant FDC effectivement présent dans `FoundationFoods`, description cohérente avec la famille, nutriment glucides `1005` avec unité source `G`, valeurs source par aliment dans les bornes déclarées. Le script ne certifie pas pour autant que l'agrégation min/max est appropriée à toutes les variétés ni que les poids de portion sont vérifiés.

**Deux issues possibles seulement** : `SOURCE_ROWS_MATCH` avec les 7 preuves reproduites (puis curation humaine source/portion), ou `BLOCKED/FAIL` avec ID et défaut exact. En `BLOCKED/FAIL`, **ne pas modifier silencieusement les données de la base, ne pas substituer des chiffres de forums**, et préparer une décision produit fail-closed pour la fonction de glucides numériques correspondante.

**Aucune précision insulinique/dose ou provenance clinique n'est inférée du seul référentiel nutritionnel**. Les portions marocaines sans poids établi restent **qualitatives**.

## 4. CAL-12 — report PDF et consentement

**Prouvé par code+tests** : `frontend/lib/services/local_report_pdf.dart::LocalReportPdf.build` est une primitive *synthetic local* PDF sur une page, **ASCII uniquement** avec `LocalReportLine(label,value)` non typés et `generatedAtUtc` obligatoire. #943 a ajouté la quarantaine **import/export** depuis `frontend/lib`, en plus de la quarantaine par appel direct.

**Non implémenté/non certifié** : document clinique patient FR/AR/Darija Unicode+RTL, sujet autorisé, consentement/destination, métriques typées+preuve source, fenêtre exacte et données manquantes. L'export JSON administratif est un autre contrat, pas un PDF clinique.

**Dépendances réelles avant activation** : accord sur les types d'informations à exporter (mesures observées vs estimation analytique vs CGM certifié), identité/consentement/fenêtre provenance, traitement des données absentes, traduction médicale, polices/RTL autorisées, captures BEFORE/AFTER même viewports et revue clinique/privacy/linguistique ; jamais une PDF remplie de nombres dérivés d'IA. **En attendant, PDF clinique OFF/quarantaine conservée.**

## 5. Séquence sans attendre passivement

1. Lire le run USDA réel de #944, récupérer le rapport public et traiter exactement l'ID/unité/format erroné s'il y a discordance. Erreur réseau = **blocage externe**, pas nombre certifié.
2. Préparer une demande d'arbitrage CAL-09/10 avec options A/B/C ci-dessus pour clinicien/produit (aucune modification runtime avant réponse).
3. Conserver le PDF clinique OFF, implémenter un contrat typé seulement après définition du besoin et validation de la livraison ; une CI de quarantaine verte est une **preuve de non-activation**, pas une preuve de qualité d'un futur PDF.
4. Vérifier revue indépendante de #943 et prioriser décision #19 ; **aucun merge ni déploiement Vercel sans autorisation explicite**, aucune donnée patient réelle. P5 historique 6/12=50 % ; tracker V1 0/29 décisions intégralement livrées à ce stade.

**Verdict :** `CAL_SUBLOTS_TESTED / CLINICAL_DAY_DECISION_OPEN / FDC_PRIMARY_IN_PROGRESS / CLINICAL_PDF_QUARANTINED / NOT_MERGED / NOT_PATIENT_AUTHORIZED`.


## 6. 12 octobre — ZIP USDA atteint en CI, contrôle encore ouvert

[PR #944](https://github.com/hraaaaf/IAMINA-MVP/pull/944) : [run 38272356607](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38272356607) a téléchargé et vérifié la structure ZIP **officielle USDA Foundation 2026-04-30** avec succès (artefact 11756709069). Première exécution de l'oracle : **échec du parseur** sur des entrées nulles du tableau FoundationFoods, avant toute comparaison des 7 identifiants.

Correctif sur #944 HEAD `e77304be0d049516f4d8b07914427ae3ebe9552d` : seuls les placeholders JSON `null` sont ignorés, les autres types non-object restent refusés ; deux tests synthétiques ajoutés. [Nouveau run 38272863911](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38272863911) déclenché ; résultat source primaire à lire, sans présumer réussite. Les valeurs nutritionnelles actuelles et le runtime restent inchangés. CAL-09/10 et PDF CAL-12 gardent leurs revues humaines.


## 7. 12 octobre — source USDA CAL-11 réconciliée (ancien NO-GO remplacé)

**Rectification fondée sur la source primaire, pas sur des valeurs de sites dérivés :** le [ZIP USDA Foundation 2026-04-30 conservé dans GitHub](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38273801139/artifacts/11758012445), contrôlé avec SHA256 `186e988ec542e913f51ef62b86a47758e8cdd0d1dc3889e7b055581f3c09c77a`, fournit des IDs **actuels** différents des 7 IDs historiques du catalogue, tous absents de ce snapshot. Le nouveau mapping a été examiné ligne par ligne dans `FoundationFoods` (nutriment 1005, unité `g`) : pommes `1750339=14.8`, `1750340=15.7`, `1750341=14.8`, `1750342=14.1`, `1750343=14.7` ; bananes `1105073=20.1`, `1105314=23.0` g de glucides / 100 g. Les sous-objets `foodPortions` enregistrent les portions `Banana`/`Peeled` correspondantes **110 g et 115 g**, sans exiger d'extrapolation.

**Correction poussée** : [PR DRAFT #945](https://github.com/hraaaaf/IAMINA-MVP/pull/945) HEAD initial `a061ba035f2e7bcfa2c14e21b7b0aa3b9968ad87`, branche `fix/v1-01-cal11-usda-2026-official-source-map-20261012`. Cinq fichiers : catalogue fruits (sept nouveaux IDs ; seule borne numérique modifiée **14.2 → 14.1** pour pomme), tests Flutter, oracle et tests Python enrichis pour portions source, tableau canonique [CAL-11 des 7 lignes](2026-10-12-v1-01-cal11-official-source-reconciliation.md). Ni mesures réelles, ni posologie, ni formule de glucides modifiée.

**Statuts de preuve différents :** `7/7_SOURCE_ROWS_MATCH_LOCAL_ARTIFACT` est **prouvé** contre le ZIP retenu ; mais **CI #945 exact-HEAD encore en cours**, [run USDA primaire `38281623476`](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38281623476) et [CI intégrée `38281623510`](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38281623510) initialement queued. Ne pas déclarer le produit « corrigé/certifié » avant passage source réelle CI + backend/frontend et inspection de l'affichage numérique.

**Prochains gates :** vérifier runs exacts, corriger erreurs source/test/format si nécessaire, QA BEFORE/AFTER aux mêmes viewports pour toute valeur visible ; revue ciblée nutrition pour la portée des références et portions (pas une prescription). CAL-09/10 jour clinique et CAL-12 export médical Unicode/RTL restent indépendants et ouverts. PR #943 toujours certifiée 17/17 **sur son ancien SHA**, aucune fusion ni Vercel.
