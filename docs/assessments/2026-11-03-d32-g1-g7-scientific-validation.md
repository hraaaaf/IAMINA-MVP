# IAMINA — D32 Web : recherche et validation scientifique/clinique/technique (G1–G7 transférés de D22)

**Création :** 03/11/2026, décision propriétaire. **Issue canonique :** [D32 #1248](https://github.com/hraaaaf/IAMINA-MVP/issues/1248). **Statut : BACKLOG / RESEARCH_NOT_STARTED / NO_CLINICAL_POLICY_APPROVED.** Ce dossier ne rend AUCUNE valeur, cible, conversion ou migration disponible pour les patients.

## Nom, goal, succès, preuve

**Nom :** D32 — validation par sources scientifiques et preuves d'ingénierie des unités, objectifs, CGM, sécurité et migration Web.

**Goal :** établir un contrat patient-safe et reproductible à partir de sources officielles et indépendantes, puis vérifier par calculs/tests source→persistance→API→UI→exports, sur données synthétiques, avant toute activation. Les recommandations médicales générales ne sont pas des prescriptions automatiques pour chaque patient.

**Succès observable :** pour chaque G1–G7, une fiche d'arbitrage contenant hypothèses, ≥2 références sérieuses indépendantes (primaires quand possible) avec version/date, analyse des contradictions, modèle/calculettes repros, tests négatifs, UX, état d'intégration et décision explicite proportionnée au risque. Si les références scientifiques ne démontrent pas une propriété de sécurité ou une autorisation individuelle, utiliser des tests de système et une revue de compétence adéquate plutôt que fabriquer une « preuve scientifique ».

## Sept contrats transférés, tous à instruire dans D32 et NON VALIDÉS

| Gate | Question scientifique/technique | Oracle/acceptation requis |
| --- | --- | --- |
| **G1** — unité/provenance | Source_value et source_unit UCUM, éventuel canonique mg/dL, display_unit distincte, interopérabilité FHIR | Unité jamais inférée de la magnitude, champs connus à toute frontière, inconnus refusés |
| **G2** — cible clinique | Autorité qualifiée, patient, provenance, date et statut d'une cible individualisée | Aucun `70/180` historique/default traité comme une cible prescrite |
| **G3** — legacy | Que faire d'une valeur brute d'unité inconnue, d'un dossier existant et d'un backfill | Préservation des bruts, aucune réécriture/classification implicite, migration réversible |
| **G4** — conversion/arrondi | Facteurs historiques 18.0/18.016/18.018, masse molaire du glucose, politique de précision, extrêmes | Conversion validée par calcul indépendant ; édition non glycémique garde la mesure source intacte |
| **G5** — métriques | TIR/AGP/GMI capteur CGM vs répartition de relevés manuels, objectifs autorisés | Données capteur traçables, métriques absentes si preuve absente ; parité API, rapports, CSV/PDF |
| **G6** — UX/accessibilité | Libellés FR/AR, bidi/RTL, parcours clavier, lecteur d'écran et zoom natif navigateur 200 % | BEFORE/AFTER mêmes états 390/768/1280, contrôles clavier/focus et audit natif arabe |
| **G7** — vie privée/DB | Identité A/B, consentement, synchro réelle, provenance non usurpable, version Drift, backup, rollback | Tests négatifs authentifiés, migration additive/réversible, restauration vérifiée et aucune fuite |

## Méthode de recherche — à exécuter lors de D32

1. Établir la **question précise, unité, dimension et risque**. Les affirmations scientifiques exigent ≥2 sources sérieuses indépendantes ; en cas de divergence/risque élevé, une troisième. Distinguer date de publication, date de validité et cadre Maroc/Web.
2. **Sources primaires à vérifier lors des recherches :** NIST Chemistry WebBook / masse moléculaire du glucose, ADA *Standards of Care* sur les cibles individualisées et la surveillance glycémique, consensus ATTD/ADA sur CGM Time in Range, HL7 FHIR + UCUM sur les quantités, W3C WCAG pour zoom/accessibilité, SQLite et documentation Drift/Flutter sur migration/backup. Les URLs/versions à vérifier avant d'en faire preuve ; aucune validation déjà effectuée sur ce dossier.
3. Tableau d'examen par assertion : `claim → sources avec liens/date/DOI → méthode/calcul indépendant → données/fixtures → tests → limites → recommandation → verdict`. Rejeter le consensus imprécis et les seuils individuels extrapolés.
4. Tests de sécurité/provenance **distincts** de la littérature : identité réelle authentifiée A→B→A, jetons invalidés, consentement, API/DB/sync, données source signées ou auditables, snapshot et restauration synthétiques, compatibilité navigateur/Drift versionnée. Un article ne prouve pas l'absence de fuite dans une application.
5. Revues spécialisées et arbitrage produit documentés sur code/test SHA précis. Déploiement Vercel seulement avec accord utilisateur explicite ; aucun test sur données patient réelles par défaut.

## Reprises et dépendances exactes

- D22 techniquement acceptée sur scope de confinement Web : [#1165](https://github.com/hraaaaf/IAMINA-MVP/issues/1165) / [dossier D22](2026-11-03-d22-web-technical-acceptance.md). Les six PR Web D22 sont **fusionnées dans `main@29a7c0ccb5e4271bb9f2e5e2bce15849d7bf0fef`**, avec #1247 documentaire ; les 86/86 workflows prémerge SUCCESS restent des preuves historiques, la CI postmerge est [#41668434340](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41668434340). **Aucun déploiement Vercel ni validation patient implicites**.
- Points manquants **transférés** : F02 conversion des cibles approuvées, F05 PDF/CSV/API/CGM, F06 auth/API/consentement, F07 zoom natif/lecteur écran/revue arabe, vraie migration Drift et restauration.
- Modèles expérimentaux G1/G4/G7 [#1221](https://github.com/hraaaaf/IAMINA-MVP/pull/1221) et répétition SQLite G7 [#1222](https://github.com/hraaaaf/IAMINA-MVP/pull/1222) fusionnés sans activation runtime clinique ; leurs tests ne sont pas une certification des consommateurs Web.
- D19 [#920](https://github.com/hraaaaf/IAMINA-MVP/pull/920) reste Draft ; conflit de précision/calcul à traiter en D32, sans fusion implicite.
- KPI API au défaut 70/180 [issue #1224](https://github.com/hraaaaf/IAMINA-MVP/issues/1224), désormais suivi **D32**, non résolu par le seul masquage de la présentation.

**Next exact D32 :** recherche indépendante sur G1/G4/G5 puis matrice de preuves ; conserver `G2/G3/G7` comme contraintes de propriété/consentement nécessitant aussi de vrais tests. Ne pas commencer une conversion runtime ou prescription non autorisée.
