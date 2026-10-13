# IAMINA D7 — Contrat de convergence multi-traitement et sécurité

**Statut : PROPOSITION D'ARCHITECTURE, NON IMPLÉMENTÉE, NON CERTIFIÉE.** Relevé 13/10/2026 sur PR #986 `5b05041fa9fca8164b0f79f1d3aab34e69194197`.
Autorités : [décision D7 originale, option A](https://app.notion.com/p/3f377c663362812dbe78cead75e71922) ; handover `docs/handovers/2026-10-13-iamina-d7-revue-profil-medical.md`. Le présent document ne modifie pas la décision.

## Goal / Succès / Preuve

**Goal :** profil médical déclaratif, progressif et non bloquant ; types type1/type2/gestationnel/prédiabète/autre/inconnu ; plusieurs traitements simultanés ; aucune prescription, dose, diagnostic ou adaptation de cible/triage.

**Succès observable :** la patiente ou le patient choisit plusieurs traitements, revient sur ses choix, reporte l'entrée et retrouve les mêmes faits après fermeture, connexion et synchronisation autorisées ; un compte B ne lit ni ne modifie jamais les données du compte A sur le même appareil.

**Preuve :** migrations Drift/PostgreSQL non destructives et rejouables, API scellée sur `request.user`, tests positifs/négatifs A→logout→B→A, migration et reprise multi-appareil, Flutter/Chrome AFTER sur 390×844/768×1024/1280×900, revues indépendantes sécurité + clinique + UX, et certification CI au HEAD exact.

## Écarts vérifiés dans le code

1. `frontend/lib/data/drift/database.dart` schéma v10 : `PatientProfiles.treatment` est un scalaire ; `watchProfile()` effectue `limit(1)` **sans filtre patient** ; les écritures de consentement et Ramadan sélectionnent également un profil non filtré.
2. `frontend/lib/features/auth/onboarding_chat_screen.dart` : `_finish` bloque si type ou traitement absent, écrit sous `firebaseUser?.uid.hashCode.abs() ?? 1`. Un `hashCode` n'est pas une identité persistante contractuelle et ne relie pas correctement l'auth native.
3. `frontend/lib/features/profile/profile_screen.dart` : lecture d'un profil sans owner et écriture sous `userId=1`.
4. `frontend/lib/services/consent_service.dart` : complétion medicale liée à deux chaînes non vides ; « unknown » enregistré peut être faussement assimilé à « complet » ; consentement AI doit rester totalement indépendant.
5. `backend/diabetes/models/patient.py` : `diabetes_type` et `treatment_type` sont scalaires ; `backend/diabetes/api/v1/profile.py` PATCH et `schemas.py` sont scalaires. La base connaît `prediabetes`, `oral_meds`, `diet_exercise`, `insulin_pump`, `insulin_injections`, `insulin` ; Flutter utilise `pre`, `tablets`, `lifestyle`, `insulin`, `other`, `unknown`.
6. CI #38403241359 du HEAD #986 : Flutter success, tests backend + PostgreSQL **skipped**. Aucun test d'isolation native A→B ni d'API multi-traitement validé.

**Qualification :** risque structurel de mélange de profils inféré du code ; aucune fuite réelle n'est démontrée. Ne pas traiter la PR #963 DRAFT comme preuve d'isolation native.

## Contrat proposé à implémenter

- **Types canoniques versionnés :** `type1 | type2 | gestational | prediabetes | other | unknown`. `null` = non répondu, et non « unknown ». Conversion `pre`↔`prediabetes` uniquement aux frontières versionnées, sans conclusion clinique.
- **Traitements déclaratifs multiples :** état séparé `not_answered | unsure | declared | none_declared` ; `declared` porte une collection dédupliquée de codes précis, avec provenance `patient_declared` et version/date. Jamais de traitement pré-rempli, déduit du type ou recommandé. `none_declared` doit venir d'une action explicite, jamais d'une liste vide implicite.
- **Migration :** extension additive local+backend, sauvegarde des colonnes scalaires héritées et valeurs originales, aucun effacement automatique ; aucun collapse vers une seule option, aucune perte de spécialité pompe/injection, mapping `tablets`→`oral_meds` non présumé si la sémantique est plus large ; inconnus legacy conservés avec provenance et confirmation patiente requise. Tests sur v10→vNext, DB neuve, double exécution/backfill, doublons, restauration, offline/replay et rollback.
- **Identité :** isolation lecture, stream, écriture, export, consentement et restauration par une identité authentifiée stable et explicite. Un identifiant local de session hors-ligne n'est pas un identifiant médical de compte distant. Ne jamais employer `hashCode`, ID `1` ou email déclaratif comme authority distante. Changement d'AuthEpoch → couper streams/caches du compte précédent. Doublons/mismatch legacy → refus de lecture/écriture + récupération non destructive, pas de `limit(1)` silencieux.
- **Transaction :** opérations local/remote atomiques par propriétaire ; `PATCH /profile` doit utiliser seulement le propriétaire `request.user` et distinguer champ omis, `null`, effacement explicitement autorisé et état inconnu. Gestion de concurrence et replay sans réécriture inter-patient. GET, PATCH et sync doivent restituent les mêmes faits.
- **Parcours :** choix du pays/langue/unité sans devoir renseigner la médecine. « Plus tard » != « je ne sais pas ». D9 : ne pas relancer intégralement le compte déjà présent. Profil modifiable sans modifier une cible validée ; une variation d'applicabilité doit conserver l'invalidation des confirmations de cibles du backend.
- **Sécurité clinique :** vue prédiabète : habitudes de vie en premier, insuline accessible seulement comme déclaration inhabituelle volontaire. Type1 : ne jamais impliquer que l'hygiène remplace l'insuline. Type gestationnel/mineurs/inconnu : aucune déduction de seuil/dose/triage. Clinique déterministe inchangée ; adaptation médicale soumise à audit D19 + reviewer clinicien.

## Tests bloquants à écrire/faire passer

1. FR/AR : six types, `null`, combinaison de 2+ traitements, sélection/désélection, `later` et `unsure`, réouverture, accessibilité/RTL.
2. Drift/Postgres : additif/roundtrip, préservation old scalar/metadata, null vs unknown vs none, replay idempotent et atomique, restauration.
3. Auth : compte natif A→B même DB, compte Firebase→natif, app locale offline, 2 profils legacy, token expiré, streams consentement et `watchProfile`, B refuse lecture/écriture A ; retour A conserve données A.
4. Backend : GET/PATCH sous `request.user`, absence d'ID forgé, refus cross-patient, validation codes/état, conflit concurrent, sans changement non demandé de cible ni egress IA.
5. UX : BEFORE/AFTER vrais Chrome aux mêmes viewports avec le même état ; validation visuelle explicite de l'utilisateur ; revues indépendantes sécurité/clinique et Release Certifier.

**Interdiction de clôture/merge :** BLOCKER/MAJOR sécurité, migration, clinique ou UX non traités ; backend/Postgres skipped ; aucune approbation humaine visuelle ; preuves hors HEAD. **Aucun déploiement Vercel sans autorisation explicite.**

**Next exact :** inventaire de tous les consommateurs de profil + convention d'identité stable, implémenter et prouver l'isolation native A→B avant persistance multi-traitement, puis migration/versioning, UI et certification.
