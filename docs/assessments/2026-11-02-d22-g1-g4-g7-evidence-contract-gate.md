# IAMINA — D22 G1/G4/G7 — Contrat clinique de quantité glycémique (CANDIDAT NON ACTIVÉ)

> **NOTE DE TRANSFERT — 03/11/2026 :** ce document est une photographie historique du préflight D19→D22. Par décision propriétaire, ses arbitrages G1–G7 et sa validation clinique ont été **reportés à [D32 #1248](https://github.com/hraaaaf/IAMINA-MVP/issues/1248)** ; ils **ne bloquent plus l'acceptation technique bornée de D22**. Voir [l'état D22 actualisé](2026-11-03-d22-web-technical-acceptance.md). Aucune approbation scientifique/clinique, migration, merge ou publication patient n'est déduite de ce changement de périmètre. Les lignes historiques ci-dessous sont conservées comme sources d'audit, non comme état courant.


Date : 2026-11-02  
Base auditée : `main@de0bbf995a4aeba961937cae5837e20655eb17dc`  
**Statut : `CANDIDATE_ENGINEERING_ONLY / CLINICAL_GATE_PENDING / NO_RUNTIME_WIRING`**

## Décision et résultat attendu

**Décision D22 :** établir une séparation stricte entre (a) la valeur + unité réellement déclarées au moment de la mesure, (b) l'unité préférée d'affichage, (c) l'origine / l'autorité d'une cible thérapeutique, et (d) les lignes historiques sans provenance vérifiable.

**Goal :** éviter toute inférence silencieuse d'unité, arrondi cumulatif et promotion de données anciennes en objectifs validés.  
**Succès technique :** modèle immuable pur testable ; unité d'origine explicite ; aucune conversion si unité inconnue ; constante documentée ; conservation de la valeur originale ; aucun changement de code Flutter actif, de schéma, de backend ou de patient.  
**Preuve :** `frontend/lib/core/domain/glucose_quantity_evidence.dart` et `frontend/test/core/domain/glucose_quantity_evidence_test.dart`, CI de la PR au SHA exact (à renseigner après exécution).  
**Ce qui n'est PAS le succès :** l'approbation clinique, un consentement, une migration, le classement thérapeutique des anciens journaux ou la certification D22 complète.

## Inventaire vérifié de production

| Producer/consumer | Main le 02/11/2026 | Risque/gate |
| --- | --- | --- |
| `frontend/lib/data/drift/database.dart` `LogEntries.bloodSugar` | `REAL NOT NULL` sans `sourceUnit` ni valeur brute d'origine. Colonne `source='manual'` = **mode d'acquisition**, PAS unité de la quantité | Impossible de prouver a posteriori l'unité originale d'une ligne |
| `PatientProfiles.unitPreference` | `mg/dL` par défaut, stockée à part | Préférence ≠ provenance de l'enregistrement |
| `PatientProfiles.targetRangeLow/High` | `REAL`, défauts 70/180 | Nombres historiques ≠ objectifs individuels autorisés |
| `frontend/lib/features/auth/onboarding_chat_screen.dart` | Sauvegarde explicite `targetRangeLow=70` / `targetRangeHigh=180` | Source/approbation absentes dans ces champs |
| `frontend/lib/features/dashboard/widgets/add_log_sheet.dart` | Capture manuelle de texte avec unité de draft ; calcul mg/dL via facteur 18.0 ; conversion au toggle conserve un canonique temporaire ; sauvegarde `bloodSugar: mgdl` | UX 5/5 validée mais persistance de `sourceValue+sourceUnit` non faite |
| `frontend/lib/core/utils/glucose_formatter.dart` | `mgdlToMmolFactor=18.018`, conversions d'affichage ; code d'entrée non strict vis-à-vis d'unités externes | Divergence du facteur et éventuelle acceptation d'unité inconnue |
| `frontend/lib/features/dashboard/clinical_engine.dart` | `calcTIR(logs,low,high)` calcule une **fraction de relevés manuels**, contrairement à un temps CGM | Interdire de la qualifier de TIR sans source CGM, continuité et fenêtre validées |
| `AppDatabase.defaults()` et `forPatientVault(scope)` | Legacy `amina` non attribuable à une identité ; vault séparé existe mais son branchement runtime/synchro reste à vérifier | Interdiction de migrer silencieusement `amina` vers le patient connecté |

Aucun incident clinique réel n'est confirmé par cet inventaire ; les risques sont des surfaces de code observées.

## G1 — Unité d'autorité : choix A recommandé, décision humaine PENDING

**Recommandation technique A :** enregistrer pour chaque *nouvelle* mesure `source_value` brute, `source_unit` explicite UCUM (`mg/dL` ou `mmol/L`), `source_kind` (`manual`, plus tard instrument documenté), `recorded_at`, `patient_vault_identity`, `canonical_mgdl` dérivé et `conversion_contract_version`. La préférence `display_unit` est **indépendante** et jamais invoquée pour déduire `source_unit`.

- Inconnu / alias invalide → rejet d'une *nouvelle* entrée ou blocage des consommateurs nécessitant des unités. Ne pas deviner par grandeur (`7.8` peut être ambigu).
- Provenance `userEntered` signifie « saisi par une personne », **pas mesure certifiée par laboratoire ou clinicien**.
- Ne pas présumer qu'une unité déclarée au clavier prouve l'unité d'un ancien glucomètre.
- FHIR `Quantity.value` + `unit` + `system=http://unitsofmeasure.org` + `code` UCUM à la frontière interopérable. Pas de nouveau payload API tant que version, auth et compatibilité ne sont pas approuvées.
- Alternative B : quantité `(value, unit)` typée par enregistrement sans canonique stocké. À soumettre au même examen de cohérence et de migration.

**Autorités attendues :** ingénierie données + privacy, clinicien pour les calculs/effets thérapeutiques ; aucune signature reçue.

## G4 — Conversion : constante physique candidate, politique clinique PENDING

- Source primaire NIST Chemistry WebBook : glucose C6H12O6, masse moléculaire **180.1559 g/mol** ; `1 mmol/L = 18.01559 mg/dL`. Deuxième source NIST SRM 965c : `180.156 ± 0.004 g/mol` (incertitude masses atomiques).
- Les facteurs **18.0** (saisie), **18.018** (formateur main) et **18.016** (branche D19 non mergée) restent tels quels dans l'application jusqu'à décision de compatibilité, arrondi et migration approuvée.
- Proposition de contrat de présentation *pour le modèle futur uniquement* : valeur originale toujours immuable ; affichage mg/dL entier et mmol/L à 1 décimale (à valider selon l'appareil et le contexte), **aucune écriture d'une projection arrondie comme nouvelle valeur source**. Édition réelle = nouvelle valeur avec unité d'édition et traçabilité.
- Oracles synthétiques : 10 mmol/L → 180.1559 mg/dL ; 140 mg/dL → 7.8 mmol/L affiché ; 7.83 mmol/L → 141.0620697 mg/dL numérique, puis retour au brut 7.83 sans écriture. NaN, infini, zéro/négatif refusés pour les nouvelles valeurs.
- Revue négative après premiers 3/3 workflows verts sur `b9ffc6f` : des **entrées pourtant finies** telles que `1e308 mmol/L` débordent en `Infinity` après multiplication ; des valeurs positives extrêmement petites peuvent **sous-déborder à zéro** après division. Le module **non branché au runtime** rejette désormais le résultat converti non fini/non positif, et vérifie la conversion lors de la création de `userEntry` (tests dédiés). Ne pas annoncer PASS avant CI du nouveau SHA.
- Ne pas reclasser rétroactivement les mesures ni les cibles à proximité des seuils sur la base d'un changement de facteur.

**Autorités attendues :** responsable moteur de calcul + clinicien, puis équipe migration.

## G7 — Legacy, sécurité, restauration : aucune migration avant gate

**Mode safe par défaut :** pour un enregistrement historique sans `source_unit` ou `target_authority`, préserver intégralement les octets/nombres bruts, marquer `unknownLegacy` ou `unverified`, ne pas normaliser, ne pas interpréter comme cible personnelle, **ne pas effacer ni transférer** un dossier. Un `PatientProfiles.unitPreference` présent ne suffit pas à récupérer l'origine.

**Préconditions de toute future migration (NON exécutées ici) :**
1. Inventaire version Drift et schémas backend/API ; preuves de propriété des identités/vaults et séparation comptes A→logout→B, y compris consentement et reconnexion.
2. Backup/snapshot **avant écriture**, chiffré, corrélé à l'identité de vault, intégrité hash et plan de restauration vérifié hors production sur jeux synthétiques. Un rollback de **Vercel frontend** ne restaure pas une DB ou une migration IndexedDB.
3. Migration **additive/versionnée** : champs source nullable, anciens champs non modifiés, aucune conversion automatique des lignes `unknown`. Vérifier row counts, hashes des valeurs et idempotence. Conserver une stratégie double-lecture en version N/N+1 et plan de retour arrière.
4. Refus de classifier un ancien `70/180` sans `patient_id + authorizer + source + effective_at + approval_status`, décision G2/G3/G5 indépendante.
5. Revue privacy/DB et clinique ; test hors-prod des chemins retrait du consentement, réseau défaillant, collision d'identité, doublons, réinstallation et session A/B.

**Sources primaires :** SQLite `ALTER TABLE` et limites (`https://www.sqlite.org/lang_altertable.html`). Ces prescriptions sont une **recommandation d'ingénierie**, pas une certification CNDP.

## FUE/Gates connus

| Test | Résultat exigé | Aujourd'hui |
| --- | --- | --- |
| G1-01 à G1-04 | Unité UCUM explicite ; alias inconnus refusés ; source immuable ; affichage séparé | Couvert par tests **unitaires du modèle isolé**, CI à confirmer |
| G4-01 à G4-03 | facteur exact NIST, no-op round-trip sans perte, entrée invalide refusée | Couvert en modèle isolé, CI à confirmer |
| G7-01/G7-02 | lignes anciennes inconnues 70/180 non converties, raw préservé | Couvert en modèle isolé, CI à confirmer |
| F01/F02/F04 | cas de bout en bout App → Drift → API → reload avec unité originale | **NON EXÉCUTÉ** |
| F03/F05 | aucun 70/180 legacy classé ; dashboard/export/report cohérents | **NON EXÉCUTÉ** |
| F06 | double compte, vault, logout A→B et consentement | **NON EXÉCUTÉ** |
| F07 | FR/AR/RTL 390/768/1280, clavier, offline/zoom et capt. comparables | **NON EXÉCUTÉ** |
| Migration | Backup+restore, hash/rollback, idempotence, version DB/API | **NON EXÉCUTÉ** |

**No-GO tant que des approbations cliniques et de données sont absentes.** Les tests du modèle n'apportent pas une preuve de consommation effective par l'application.

## Human gate limité

- **G1 :** accepter ou modifier A/B ; responsable données/privacy : `PENDING`, clinicien sur les usages : `PENDING`.
- **G4 :** approuver formule, arrondis, version, gestion des anciennes mesures/exports : `PENDING`.
- **G7 :** approuver plan de sauvegarde, propriété des vaults, rollback et traitement des inconnues : `PENDING`.
- **G2/G3/G5/G6 :** demeurent `PENDING` ; aucune prise de décision clinique implicitement promue par le présent document.

## Closeout et reprise

**Ce qui est volontairement inactif :** aucune importation du nouveau module dans un écran ni service ; aucune table/colonne, migration, API, nouvelle politique runtime d'arrondi ou déploiement Vercel. Le cadran utilisateur accepté en production `f78f0fa` reste inchangé.

**Next exact :** obtenir CI exacte sur PR de contrat isolé ; comparer code et tests ; obtenir décisions G1/G4/G7 et revue technique/clinique ; puis créer une PR distincte de migration *staging-only*, jeux synthétiques, sauvegarde/restore et FUE, sans déployer avant validation.

**Références :**
- NIST WebBook `https://webbook.nist.gov/cgi/cbook.cgi?Name=glucose&cTC=on&cTG=on&cTP=on&cTR=on`
- NIST SP 260-253 `https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.260-253.pdf`
- HL7 FHIR R5 Quantity `https://hl7.org/fhir/R5/datatypes.html`
- ADA Diabetes Care 2026, Section 6 `https://doi.org/10.2337/dc26-s006`
- SQLite `https://www.sqlite.org/lang_altertable.html`
