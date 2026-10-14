# D9 — preuve explicite de première utilisation, contrat serveur

14 octobre 2026. **Statut : implémentation isolée, non certifiée avant CI, non fusionnée.**

## Goal
Permettre à un appareil nouvellement connecté de distinguer, pour **ce patient authentifié**, l'achèvement **explicitement enregistré** de la première utilisation, sans déduire celui-ci d'un profil médical (éventuellement vide) ou d'une date de consentement IA.

## Contrat V1
- `GET /api/v1/profile/first-use` : `{ "version": 1, "completed": false, "completed_at": null }` en absence de preuve. Le principal est extrait du bearer côté serveur, jamais de l'URL/corps client.
- `POST /api/v1/profile/first-use` avec **uniquement** `{ "version": 1, "confirmed": true }` : action explicite suivant une sauvegarde locale first-use réussie. Même réponse avec horodatage serveur, commande **idempotente**. Le `confirmed` est une déclaration **du client authentifié**, pas une preuve biométrique ou clinique.
- Conservation : champ nullable `core.BasePatientProfile.first_use_completed_at`; null par défaut sur anciens comptes. Aucune migration automatique d'anciens champs cliniques, aucun défaut de diagnostic, aucune modification des consentements.
- Authentification : mêmes protections Django-Ninja `HybridBearerAuth` existantes que `GET /api/v1/profile`; jeton natif révoqué/invalide refusé. La sélection du propriétaire est exclusivement `request.user`.
- Écriture concurrente : transaction + verrou de ligne + création unique d'horodatage serveur, sans écraser la première date.
- Un `200` `GET /profile`, une coque de profil, un jeton ou `clinical_profile_complete` ne suffisent jamais à affirmer que l'onboarding est achevé.

## Tests à faire valider
`backend/diabetes/tests/test_d9_explicit_first_use_proof.py` : huit scénarios réels HTTP bearer : connexion seule != preuve, action explicite idempotente, A→B→A indépendants, autre client HTTP pour même propriétaire, absence de bearer, révocation, commande invalide, dissociation clinique. Contrat API OpenAPI à conserver synchronisé.

## Blocages réels / rollout
- **Frontend encore non implémenté** : aucune utilisation de GET/POST en Dart dans cette branche ; ne jamais afficher « reconnu sur nouvel appareil » avant code et tests de restauration dans le coffre **du bon propriétaire** avec génération/auth-epoch et app-lock.
- **Anciennes inscriptions déjà effectuées avant D9** : sans preuve serveur historique, le champ reste null. Aucun backfill depuis les données cliniques ni consentements (ce serait une inférence trompeuse). La synchronisation de la preuve depuis un appareil d'origine déjà initialisé devra être explicitement décidée et testée.
- **Offline/401/403/timeouts** : état distant « inconnu », ne signifie ni complété ni non complété ; ne pas emprunter de session précédente.
- **Sécurité** : la validation de statut reste une assertion d'un patient authentifié, pas une autorisation de traitement IA ni de synchronisation des journaux/profils. Tout déploiement médical doit passer une revue indépendante de confidentialité et de sécurité ; la CI seule ne certifie pas cette revue.

**Succès de cette tranche seulement** = modèles + migration + endpoint + 8 tests authentifiés et CI backend/PostgreSQL/migration-drift + snapshot OpenAPI exact au SHA final. **Succès D9 global** = en plus restauration client sur appareil neuf, tests A→B→A réels, fail-closed, consentement distinct et revue. Pas de déploiement Vercel.
