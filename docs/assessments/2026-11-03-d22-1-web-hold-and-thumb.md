# IAMINA — D22.1 Web : maintien accéléré et lecture hors du pouce

**Date :** 2026-11-03  
**Issue :** [#1254](https://github.com/hraaaaf/IAMINA-MVP/issues/1254)  
**Décision :** D22.1 Web — correctif UX du cadran de glycémie existant.  
**Statut :** implémenté en PR Draft ; pas encore validé en CI ni déployé.

## Feedback réel et état BEFORE
L'utilisateur confirme deux difficultés sur **D22 effectivement publié** : un appui continu sur `+` ou `−` ne doit pas se comporter comme de simples taps ; il doit répéter et **accélérer progressivement** à la manière du volume d'une télécommande. En faisant glisser le pouce au sommet de l'arc dans la zone verte, le pouce recouvre la lecture numérique centrale. Il demande explicitement les deux corrections en même temps.

**Baseline code et visuels** : D22 en production Vercel `dpl_6RntVe5ckPRvxNL8Cw7YPGGWHNE9`, code SHA `a7cc05138dab3c38311fbbe37aff99415368659c` (12/12 workflows SUCCESS, 991 tests Flutter PASS/7 skipped, FUE Chrome 6/6). Code actuel `frontend/lib/features/dashboard/widgets/glucose_half_dial_input.dart` : deux `IconButton.outlined` avec `onPressed` simple, le `TextField` au centre de l'arc, aucune valeur externe visible pendant glissement. Les captures FUE sur les viewports FR/AR 390×844, 768×1024, 1280×900 et la comparaison D22 `before-after-six-viewports.jpg` établissent la référence de géométrie.

## Goal / succès / preuve
- **Goal** : conserver les taps exacts et la sélection par arc, ajouter répétition automatique **avec accélération graduelle** sur maintien de `−/+` ; afficher la **valeur active dans l'en-tête fixe au-dessus de l'arc pendant la pression**, hors du trajet du pouce.
- **Succès observable** : appui bref `126→127`; maintien à partir de `126` dépasse plusieurs pas, avec intervalles décroissants entre répétitions ; relâchement/annulation arrête immédiatement et définitivement ; `−` même effet ; en mmol/L pas de 0,1; bouton inactif sans mesure, aucune valeur inventée/DB insert accidentel. Pendant drag zone verte, nombre actif visible au-dessus, arc physiquement stable (absence de saut vertical), disparaît à la libération.
- **Preuve** : `flutter analyze`, tests horaires de cadence et gestes réels avec `WidgetTester.startGesture`, 6 layouts FR/AR × 390×844 / 768×1024 / 1280×900, sauvegarde SQLite vraie depuis champ contrôlé, D12/D13 non-régression, FUE Chromium et captures AFTER aux mêmes viewports, score visuel motivé. QA iPhone réelle restant distincte.

## Décision UX — BEFORE → Goal → mockup → AFTER
- BEFORE : ligne « SAISIE DIRECTE » + bouton de bascule au-dessus de l'arc, centre `TextField` éventuellement caché par pouce, commandes `−/+` click-only.
- Mockup structurel sans illustration nouvelle : **ligne de tête de hauteur fixe 46 px** : gauche « SAISIE DIRECTE » au repos, devient « VALEUR · 126 mg/dL » pendant drag ; droite bouton unité inchangé. **Aucun changement de hauteur pendant drag**. Sous la courbe, commandes fines préexistantes sont les mêmes visuellement. Tout contrôle reste keyboard-accessible et RTL.
- AFTER attendu : affiche le chiffre sélectionné en **21 px gras**, au-dessus et en dehors de la surface gestuelle, uniquement pendant le toucher sur l'arc valide ; sur relâchement retour à SAISIE DIRECTE. `GestureDetector.onLongPressStart/End/Cancel` sur les `IconButton` existants : premier pas à reconnaissance de l'appui long, puis intervalle **270 ms → 155 ms → 85 ms** (minimum borné), cancel sur fin/annulation, changement d'unité, invalidation ou `dispose`. Un simple tap reste **exactement un pas**, pas d'haptique répétée en boucle pour ne pas détériorer Safari.

## Périmètre et risques
- Bran. `fix/d22-1-web-accelerated-hold-visible-reading-20261103` depuis D22 post-release docs HEAD `98159788f00c2a4eaa49390f1f4e42175f1538b8` ; pas de mise à jour du `main` ni de déploiement.
- Source unique `frontend/lib/features/dashboard/widgets/glucose_half_dial_input.dart` (UI/gestes), tests `frontend/test/features/dashboard/d22_1_accelerated_hold_thumb_reading_test.dart`, ce bilan canonique.
- **Aucun** changement de valeur médicale cible, couleurs illustratives, facteur de conversion D22, garde numérique D12, navigation D13, API, schéma/DB/backend, authentification, analytics ou contenu patient.
- Les bornes visuelles 40–320 mg/dL ne sont pas des limites médicales et ne bornent pas la saisie directe ni les commandes fines.
- Éviter que les répétitions créent de la valeur au démarrage vide ; préserver la protection de conversion/finite et l'exactly-once Drift.

## Vérification et suite
**État au démarrage :** Vercel production D22 inchangée ; pas de tests exact HEAD exécutés pour D22.1. **Next** : ouvrir PR Draft ciblant branche D22, bascule temporaire `main` uniquement pour déclencher GitHub CI complète et FUE selon workflows du repo, puis retour sur base D22. Vérifier tests Flutter, captures Chrome AFTER, corriger si anomalie, documenter preuves et actualiser Notion. Publication Vercel **interdite sans nouveau GO** explicite propriétaire ; la commande « Go les deux à la fois » est autorisation de développement, pas déploiement.
