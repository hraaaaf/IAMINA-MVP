# IAMINA D1 P0-A — SAFE-HOLD (10 novembre 2026)

**Décision active :** [roadmap canonique D1–D12](https://app.notion.com/p/3df77c66336281f5b308ec17f7f0a63b), D1 validée sur conservation historique + chiffrement avant activation patient + migration volontaire.

## Goal
Empêcher qu'une future PR connecte accidentellement un migrateur/chiffreur expérimental à l'application clinique ou change les noms des coffres et adopte automatiquement des données legacy.

## Already implemented on main
- `AppDatabase.defaults()` utilise `amina` (legacy) ; `forPatientVault` est limité à `scope.databaseName`.
- `PatientVaultScope` isole les noms d'utilisateurs Django, appareils locaux et audit ; `main.dart` inspecte/ferme le coffre legacy sans le rendre visible dans le shell patient.
- Le worker PWA peut garder du JS ancien hors ligne. **Les nouveaux Web Locks ne contraignent pas les anciens onglets qui ne les sollicitent pas** ; un ancien écrivain peut écrire après copie du coffre.

## Implémentation de ce lot limité
- `tools/d1_legacy_cutover_guard.py` parcourt le graphe d'imports/exports Dart depuis quatre points d'entrée de l'application et **échoue fermement** si un fichier expérimental `d18_*.dart` devient accessible.
- Refuse toute modification des identifiants de bases ou une opération destructive/directe évidente dans les points d'entrée. Tests synthétiques positifs/négatifs.
- CI sur PR changeant `frontend/lib/**`, sans modification de la base ni du service worker en production.

## Limitations et risque résiduel
La vérification est **statique**, basée sur les imports explicites. Elle ne couvre ni le comportement dynamique de Drift/VFS, ni les transformations indirectes, ni les anciennes transactions IndexedDB, ni le chiffrement. Elle ne prétend pas rendre une migration possible. **D1 P0-A reste NO-GO pour une bascule de coffre clinique.**

## Succès observable / preuves à recueillir
1. Tests synthétiques du garde : PASS au HEAD exact.
2. Garde sur le vrai graphe du dépôt : PASS au HEAD exact.
3. Test navigateur réel de v1/IndexedDB/OPFS avec ancien bundle et nouvelle cible, comparaison logique et nouveaux onglets : **NOT_RUN** sur ce lot ; required avant toute migration.
4. D1 chiffrement/recovery crypto et revue indépendante : **NOT_RUN**.
5. Aucune donnée patient réelle ; aucun déploiement Vercel, aucune modification des anciennes bases.

**Next :** comparer les probes navigateur P0-A de la PR #1265 au runtime Drift 2.31.0 et reproduire sur des coffres jetables, sans activer de migration.
