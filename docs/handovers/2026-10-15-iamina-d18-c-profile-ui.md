# IAMINA — D18-C Profil progressif — Handover opérationnel

**Date** : 2026-10-15. **État** : CANDIDATE / non certifiée / PR DRAFT, aucun merge ni déploiement.
**PR** : [#1066](https://github.com/hraaaaf/IAMINA-MVP/pull/1066), branche `feat/v1-d18-c-profile-progressive-ui-20261015`, fondée sur D18-B #1064. Base GitHub `main` temporaire pour déclencher CI uniquement ; **NE JAMAIS MERGER sous cette base**.
**Référence produit** : décision 18, option A, Notion 2026-10-08.

## Goal → Success → Proof

**Goal** : rendre le poids daté/historisé, l'année de naissance et l'identité de genre facultatifs et éditables, sans forcer l'onboarding ni créer des données médicales/inférences.
**Succès observable** : patient natif, coffre sélectionné et déverrouillé → saisie explicite → sauvegarde LOCALE uniquement → relecture historique sans écraser, avec kg/lb, horodatage, provenance. Coffre vide reste vide ; entrées invalides refusées ; aucun accès depuis Web non sécurisé.
**Preuve requise** : tests Flutter widgets/intégration réels, parcours A→B→A natif/PWA, tests de session verrouillée, captures BEFORE/AFTER par viewport, score visuel, reviewers privacy/clinique indépendants, CI exact-head.

## BEFORE connu (source vérifiée, pas capture)

- `frontend/lib/features/profile/profile_screen_presentation.dart` sur `main@851117c` : sections existantes médical/Ramadan/IAmina/données/compte, **aucune section D18**.
- `frontend/lib/features/profile/profile_screen.dart` ne consomme pas encore les magasins locaux D18-B.
- Capture visuelle BEFORE du vrai écran Profil aux viewports requis **NON EFFECTUÉE**. Aucune certification UI ne peut être attribuée.

## Target/mockup de travail (spécification, pas rendu validé)

- **390×844**, petit écran : section indépendante « Informations personnelles facultatives » après la section médicale, fermée au chargement; ouverture par accordéon; année de naissance (vide autorisé) et identité de genre déclarée (vide/effacement autorisés) puis bouton d'enregistrement explicite; séparateur; nouvelle pesée (valeur, kg/lb, date+heure, ajouter); historique affichant valeur et date source, plus récent en premier.
- **768×1024** : même ordre de lecture, sans perte d'accès au bouton ou troncature de valeur/unité ; navigation clavier, lecteurs d'écran.
- **1280×900** : même hiérarchie dans la surface de contenu du profil, pas de modal ni flux secondaire obligatoire.
- **FR/EN/AR et RTL** : libellés compréhensibles, nombres/unités non inversés, états chargement/vide/refus/enregistré distincts.
- Le message doit préciser : « enregistré dans ce coffre uniquement », pas de promesse de sync ni d'adaptation thérapeutique.

## Implementation candidate

- `frontend/lib/features/profile/d18_profile_panel.dart` : composant Flutter local, explicite, pas de réseau ni modèle génératif. Horodatage **explicitement confirmé** via les deux sélecteurs date et heure, sinon ajout bloqué ; date locale convertie UTC, provenance `patient_declared`. Aucun horodatage inventé à l'ouverture du formulaire.
- `profile_screen.dart` + `profile_screen_presentation.dart` : section visible uniquement pour **coffre natif Django déverrouillé**, **pas sur Web** tant que #1054 (IndexedDB/chiffrement/contrôle du propriétaire) reste ouvert.
- `frontend/test/features/profile/d18_profile_panel_test.dart` : scénarios défaut vide, année facultative, pesées multiples, erreurs de saisie, absence de profil local; **résultats CI à vérifier**.
- Aucune conversion genre → paramètre biologique, aucune date de naissance inventée, aucune modification de traitement ou cible, aucun upload automatique.
- **D18-D** demeure séparé : appareils réels A→B→A, consentement sync D30 et privacy reviewer.

## Validation et limites

- D18-A [#1060](https://github.com/hraaaaf/IAMINA-MVP/pull/1060) HEAD `953e7ef` : 2/2 workflows CI/migration SUCCESS.
- D18-B [#1064](https://github.com/hraaaaf/IAMINA-MVP/pull/1064) HEAD `bd04e1b` : 5/5 CI/PWA/P5-5 SUCCESS.
- D18-C PR #1066 : CI à vérifier **sur HEAD final**, les workflows lancés sur d'anciens commits C ne prouvent pas le dernier HEAD.
- **Visual certification : NO_GO** tant que BEFORE→Target→AFTER identiques, tests d'accessibilité et score visuel ne sont pas observés. Cap de score fidélité **≤7.5/10**. Pas de notation globale trompeuse.
- **Release : NO_GO** : revues spécialisées/manuelles absentes, D18-A/B non mergées, pas de preuve 2 appareils, D10 Web risque ouvert.
- **Pas de Vercel D18 sans nouvelle autorisation explicite.** Aucun patient réel. P5 historique 50 % inchangé.

## Next exact

1. Inspecter les workflows #1066 au SHA actuel ; corriger les erreurs Flutter/analyze/screenshot sur la branche C, revalider SHA final.
2. Revue adversariale : idempotence dans les retries, propriétaire après changement de compte, verrouillage réel, erreurs et provenance ; corriger les findings de périmètre.
3. Capturer le vrai Profil BEFORE, produire le mockup visuel cible, puis AFTER mêmes viewports avec comparaison+tests RTL/accessibilité et score.
4. Retarget PR #1066 vers D18-B #1064 **après** confirmation des SHAs et diff limité au lot UI ; reviews → Release Certifier → merge/postmerge uniquement si gates réellement franchis.
5. D18-D vrais tests device/PWA + consentement ; handover Notion, retour roadmap. Aucun passage à 100 % sans preuve.

## Revue adversariale corrective — 15/10/2026

- Défaut corrigé : horodatage initial fixé à l'ouverture et réutilisé malgré une mesure réelle différente. Date et heure doivent désormais être confirmées avant chaque pesée ; champ réinitialisé après ajout. Test dédié.
- Défaut corrigé : sauvegarde des deux champs démographiques même quand un seul était modifié (risque d'écraser une déclaration plus récente). Drapeaux de modification séparés ; test de mise à jour concurrente. Contrôles désactivés pendant sauvegarde.
- Les captures navigateur Web ne certifient pas le widget D18 natif, volontairement interdit Web tant que #1054 n'est pas résolu. Visuels BEFORE/AFTER réels et revue indépendante sont encore ouverts. CI du nouveau HEAD à vérifier avant tout verdict.

- Correction UX complémentaire : bouton « Actualiser » désactivé lorsqu'une déclaration démographique reste modifiée mais non enregistrée ; évite l'effacement silencieux du brouillon. Régression Flutter ajoutée.
