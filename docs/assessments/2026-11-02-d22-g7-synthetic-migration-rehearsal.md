# IAMINA — D22 G7 — Répétition SQLite synthétique avant toute migration

**Date :** 2026-11-02  
**Goal :** prouver sur un jeu entièrement fictif qu'une future table de provenance peut être ajoutée *sans modifier* les mesures et cibles historiques, avec snapshot/restore et non-propagation entre coffres distincts.  
**Décision :** G1/G4/G7, **candidat technique uniquement**. **AUCUNE migration active**, aucun patient réel, aucun déploiement Vercel.  
**Base auditée :** `main@de0bbf995a4aeba961937cae5837e20655eb17dc`, Drift v12.

## Portée mesurable / protocole

- **Code** : `scripts/d22_g7/test_sqlite_rehearsal.py` — uniquement Python `sqlite3`, `unittest` et `tempfile`. Un script de tests sans CLI acceptant un chemin DB ; chaque instance crée une base neuve jetable dans un dossier temporaire. **Aucun import Flutter/backend**.
- **CI dédiée** : `.github/workflows/d22-g7-synthetic-sqlite-rehearsal.yml`, `python -m unittest discover -s scripts/d22_g7 -p 'test_*.py' -v`.
- **Fixture** : **sous-ensemble** des tables Drift v12 `log_entries` (id/blood_sugar/client_uuid/source) et `patient_profiles` (user_id/target_range_low/high/unit_preference). Le test d'une fixture simplifiée **ne prouve pas** la migration du schéma Drift complet ni la compatibilité sqlite3 WASM/IndexedDB.
- **Table *proposée* `glucose_measurement_evidence_v1`** : `log_entry_id` FK, `original_source_value`, `original_source_unit_ucum`, `unit_system=http://unitsofmeasure.org`, `provenance=user_entered`, `conversion_contract=nist_glucose_1801559_v1`, `recorded_at_utc`. L'application conserve les colonnes et défauts existants. **Aucune ancienne ligne n'est rétroremplie** et aucune donnée historique n'est reclassée.
- **G1/G4** : valeurs nouvelles refusées si `source_unit` absent/alias inconnu, valeur non finie/non positive, débordement du calcul candidat `18.01559` ; ce test Python est un *oracle indépendant* du contrat Dart non branché en [PR #1221](https://github.com/hraaaaf/IAMINA-MVP/pull/1221), et non une modification de la conversion clinique active.
- **G7 tests** : snapshots avant/après de toutes les valeurs legacy (70/180 conservés, unitPreference préservée), idempotence, schéma préexistant conflictuel refusé, CREATE TABLE atomique annulé après erreur injectée, FK invalide/duplicate rejetés, deux fichiers distincts `native_101/native_202` sans transfert des métadonnées, snapshot SQLite online backup et copie/restauration byte-hash SHA256 + intégrité.
- **Caveat important** : deux fichiers différents **ne prouvent pas l'authentification, l'appartenance réelle, le logout→login, le consentement ni la séparation d'une API distante**. Aucun vrai coffre patient ou profil réel n'est ouvert. Une sauvegarde synthétique temporaire non chiffrée **n'est pas** un protocole de backup des données médicales réelles.

## Vérifications attendues avant toute activation patient

| Gate | Ce que prouve cette PR si CI verte | Ce qu'elle ne prouve PAS |
| --- | --- | --- |
| G1 | Refus d'unité UCUM non déclarée en test | Provenance d'une source réelle, unité glucomètre validée |
| G4 | Résultat numérique fini, source intacte ; facteur candidat NIST | Approbation du facteur/arrondi/éditions en production |
| G7 | Création de table sidecar synthétique et rollback transactionnel | Migration Drift 12→13 réelle, absence de régression Flutter Web/IndexedDB |
| G7 | Sauvegarde SQLite cohérente, SHA256 et restauration | Backup chiffré et restaurable de vrais vaults multi-appareils |
| G7 | Pas de transmission entre deux fichiers sqlite fictifs | Isolation réelle A→logout→B, auth, données legacy ou API |

## Séquence de release clinique à ne PAS sauter

1. Qualifier le contrat G1/G4 et obtenir la revue clinique et données/DB sur [PR #1221](https://github.com/hraaaaf/IAMINA-MVP/pull/1221).
2. Finaliser G2/G3/G5 : **qui autorise une cible**, quelles valeurs historiques restent `unknown`, et comment calculer les métriques (ne jamais appeler le ratio de relevés manuels `TIR CGM`).
3. Concevoir une **migration Drift additive réversible séparée**, nouveau schemaVersion seulement après décision, backup chiffré et restauré prouvé avant écriture ; inclure compatibilité backend/exports et service de sync.
4. Tester web en PREVIEW avec données synthétiques : 390/768/1280, FR/AR RTL, navigation clavier, pertes réseau, A→logout→B, reconnect, restore/idempotence, anti-contamination des dossiers.
5. Revue sécurité/privacy et clinique documentée, CI dernier SHA, autorisation humaine et acte de publication Web ultérieur. **Aucun de ces gates n'est franchi par cette PR de tests synthétiques**.

## Références primaires

- SQLite Online Backup API : https://www.sqlite.org/backup.html
- SQLite ALTER TABLE et limites : https://www.sqlite.org/lang_altertable.html
- HL7 FHIR Quantity (value/unit/system/code) : https://hl7.org/fhir/R5/datatypes.html
- NIST WebBook glucose 180.1559 g/mol : https://webbook.nist.gov/cgi/cbook.cgi?ID=50997
- ADA Standards of Care 2026 : https://doi.org/10.2337/dc26-s006

**État à la création :** implémentation de la répétition en PR DRAFT, **CI et résultats de tests à inscrire après exécution réelle**, aucune certification médicale.  
**Next exact :** lancer la workflow sur le HEAD du périmètre isolé, corriger tout échec ; conserver les deux PR en DRAFT jusqu'aux revues G1/G4/G7.
