# IAMINA — D18 Web / profil progressif + sauvegarde chiffrée — 2026-10-31

## Goal
Intégrer l'UX approuvée au vrai `ProfileScreen` Web IAMINA : données facultatives, poids daté et corrigeable, coffre patient local-first, export chiffré et restauration D18 uniquement. **Pas de synchronisation automatique des données D18 ni de déploiement Vercel.**

## Décisions validées
- Web local-first (option A), profil sans obligation d'onboarding.
- Export manuel chiffré ET restauration testée comme critères bloquants D18.
- Direction UX validée avec obligation d'adaptation aux cartes/typos/couleurs/interaction existantes d'IAMINA. Ce n'est pas une autorisation de merge/deploy.

## État vérifié avant certification
- Base main au démarrage : `fc0366f4c55f2bb25c2b9e2a15367d9241567c76`.
- Branche : `feat/iamina-d18-web-progressive-profile-20261031`.
- PR brouillon : https://github.com/hraaaaf/IAMINA-MVP/pull/1207
- Intégration : `frontend/lib/features/profile/profile_screen.dart` + `profile_screen_presentation.dart` (Web uniquement), et widgets D18 propres au thème `AminaVisualLanguage`.
- Données : `patient_progressive_demographics_store.dart`, `patient_weight_history_store.dart`. PatientVaultScope contraint physiquement le stockage ; pas d'appropriation du coffre legacy.
- Sauvegarde : `d18_encrypted_backup.dart` ; AES-256-GCM avec AAD v1 ; PBKDF2-HMAC-SHA256 600000 itérations + sel aléatoire ; wrapper sans identité ni données patient ; file picker dédié dans Données et appareils. Restauration uniquement si données D18 destination vides, transaction D18-only, vérification après écriture. Jamais `LocalBackup.restoreVaultJson` qui écrase des tables médicales étrangères à D18.
- Poids : version correcte écrite comme nouvelle observation liée à la précédente ; écran n'affiche que la dernière version ; suppression explicite purge la famille.
- Tests ajoutés/portés : démographie indépendante du profil médical, historique + correction/suppression, crypto, altération/mauvaise phrase secrète, mauvais propriétaire, import non destructif, transfert local volontaire.

## Gates NON ATTEINTS — NO GO PROD / NO MERGE
1. CI exacte du dernier HEAD **pas encore prouvée verte**. Pas de Flutter/Dart compilateurs dans l'environnement local de ce travail ; vérification par CI GitHub obligatoire.
2. UI : capture BEFORE réelle du Profil main → AFTER aux mêmes viewports 390 / 768 / 1280, FR/AR RTL, double score reviewer et approbation humaine.
3. FUE vrai Chrome / PWA : A→B→A, offline/reload, export → effacement navigateur / navigateur vierge → restauration, mauvais secret, contenu malformé, transfer device-only, session change, stockage indisponible.
4. Security/privacy : contrôle de l'exposition IndexedDB au repos, XSS/gestion mémoire des clés, PBKDF2/calibration navigateur, restauration atomique et données médicales non altérées ; conformité et conservation légale.
5. Résoudre erreurs CI éventuelles. Actualiser ce document et Notion avec SHA/runs preuves ; ne jamais inventer des pourcentages du lot.

## Next exact
Inspecter la CI de la PR #1207 une fois disponible ; diagnostiquer/corriger les erreurs, terminer FUE navigateur + revue UX/security, puis gate humain. Aucun merge/production ni Vercel sans autorisation explicite.

## Rappel
Chantier A : 4 décisions closes sur 13 (30,8 %) avant D18 ; **D18 reste OPEN**, aucun changement d'avancement global tant que les gates ne sont pas satisfaits.
