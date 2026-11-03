# IAMINA — D22.1 Web : maintien accéléré et lecture hors du pouce

**Date :** 2026-11-03  
**Issue :** [#1254](https://github.com/hraaaaf/IAMINA-MVP/issues/1254)  
**Décision :** D22.1 Web — correctif UX du cadran de glycémie existant.  
**Statut :** **VALIDÉ TECHNIQUEMENT sur SHA code `b10ede6ac3452151aee72ed08857995e1e6261c4` (12/12 GitHub SUCCESS).** PR Draft #1255 ouverte, base D22 restaurée, diff 3 fichiers et `mergeable:true`, non fusionnée et **non déployée** ; recette iPhone Safari réelle et nouveau GO Vercel restent ouverts. Une mise à jour documentaire post-certification peut produire un SHA différent du code validé.

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
- AFTER attendu : affiche le chiffre sélectionné en **21 px gras**, au-dessus et en dehors de la surface gestuelle, uniquement pendant le toucher sur l'arc valide ; sur relâchement retour à SAISIE DIRECTE. `IconButton.onLongPress` **natif** (évite la concurrence avec le tooltip Flutter) accompagné d'un `Listener` sur `PointerUp/Cancel/Move` : premier pas à reconnaissance de l'appui long, puis intervalle **270 ms → 155 ms → 85 ms** (minimum borné), arrêt immédiat au relâchement, sortie de la zone tactile, changement d'unité, invalidation ou `dispose`. Un simple tap reste **exactement un pas**, pas d'haptique répétée en boucle pour ne pas détériorer Safari.

## Périmètre et risques
- Branche `fix/d22-1-web-accelerated-hold-visible-reading-20261103` depuis D22 post-release docs HEAD `98159788f00c2a4eaa49390f1f4e42175f1538b8` ; pas de mise à jour du `main` ni de déploiement.
- Source unique `frontend/lib/features/dashboard/widgets/glucose_half_dial_input.dart` (UI/gestes), tests `frontend/test/features/dashboard/d22_1_accelerated_hold_thumb_reading_test.dart`, ce bilan canonique.
- **Aucun** changement de valeur médicale cible, couleurs illustratives, facteur de conversion D22, garde numérique D12, navigation D13, API, schéma/DB/backend, authentification, analytics ou contenu patient.
- Les bornes visuelles 40–320 mg/dL ne sont pas des limites médicales et ne bornent pas la saisie directe ni les commandes fines.
- Éviter que les répétitions créent de la valeur au démarrage vide ; préserver la protection de conversion/finite et l'exactly-once Drift.

## Vérification — preuves exactes 03/11/2026

**Goal atteint techniquement sur SHA CODE `b10ede6ac3452151aee72ed08857995e1e6261c4`** (ne pas confondre avec un commit documentaire ultérieur).

- [CI Flutter #41726706339](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41726706339) **SUCCESS** : flutter analyze, **1 000 tests PASS / 7 SKIP**, build PWA `✓ Built build/web`, sorties compilées. **9/9 tests D22.1 SUCCESS** : 1 test cadence, 6 tests geste avec lecture en-tête hors arc à FR/AR × (390×844, 768×1024, 1280×900) et vraie `NativeDatabase.memory()`, 2 tests long-press accéléré +/- FR et AR, relâchement/sortie tactile et conversion mmol/L. Les tests existants D22 et D12 sont aussi passés.
- [Chromium D13 #41726706385](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41726706385) **SUCCESS 6/6**, FR/AR × 3 tailles : vrai INSERT Drift bloqué, refus Retour app/navigateur pendant sauvegarde, reçu et exactement une glycémie 126 mg/dL après rechargement.
- **12/12 GitHub workflows exact SHA SUCCESS, zéro failed/pending** : CI, capture navigateur, audit géométrie, TD-014, D3, D13 et certifications UI existantes. Le backend et PostgreSQL sont SKIPPED volontairement, sans changement dans ce lot.
- **Comparaison visuelle BEFORE/AFTER réellement inspectée** : capture D22 baseline `d22-final-inspection/after/before-fr/ar-390x844.png` versus screenshot D22.1 extrait de l'artifact de [Chromium #41726706385](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41726706385), mêmes viewports FR/AR × 390×844, 768×1024, 1280×900. Au repos, en-tête « SAISIE DIRECTE » conservé, arc et touches ± centrés, CTA visible, pas de débordement observé. Texte d'aide mis à jour. **Score visuel qualitatif 8,5/10** pour ces captures statiques ; ce n'est pas une mesure automatisée. Les captures au repos **ne peuvent pas** prouver la valeur pendant mouvement : ce point est démontré par les 6 tests widget qui vérifient lecture hors arc et position verticale stable ; la validation tactile sur Safari iPhone demeure à réaliser.
- Échec précédent, corrigé sur le code certifié : SHA `735b178` avait Flutter CI 988 PASS / 12 FAIL / 7 SKIP, pour 1px de RenderFlex overflow de l'en-tête et la simulation horloge Flutter incorrecte de timers réarmés. Correctifs `TextStyle.height:1.0` et `_pumpInFrames(50 ms)` ; **1000/1000 tests réussis sur SHA b10ede**. Le dernier code n'est pas affecté par l'échec des anciennes tentatives.
- [PR Draft #1255](https://github.com/hraaaaf/IAMINA-MVP/pull/1255) base **restaurée** vers `fix/d22-web-glucose-fine-step-20261103` après certification temporaire contre `main` ; `mergeable:true`, delta **3 fichiers** (composant, tests, ce document), non mergée.

## Human gate et séquence restante

**Production D22 inchangée** : `https://iamina-review.vercel.app` déploiement `dpl_6RntVe5ckPRvxNL8Cw7YPGGWHNE9`, code D22 `a7cc05138dab3c38311fbbe37aff99415368659c`. Aucun déploiement D22.1, merge ou backend. L'utilisateur « Go les deux à la fois » a validé **le développement**, pas le déploiement. **NOUVEAU GO VERCEL EXPLICITE REQUIS**.

**Next exact** : obtenir GO pour déploiement Web D22.1 (prod ou preview selon décision du propriétaire), vérifier Vercel READY/alias/SHA/errors, puis recette physique iPhone avec données synthétiques : saisir 126 ; tap ± pas de 1 ; maintenir + et observer accélération ; relâcher puis vérifier arrêt ; tenir − et glisser hors bouton, vérifier arrêt ; changer d'unité à 7,0 mmol/L puis même comportement au pas de 0,1 ; glisser dans zone verte et lire valeur dans tête au-dessus du pouce ; enregistrer et vérifier reçu + une seule mesure après recharge, FR/AR. En cas de bug, nouveau correctif et nouveau GO avant redéploiement. Les seuils et recommandations médicaux D32 restent hors scope.

**Traçabilité** : cette mise à jour est uniquement documentaire. Le SHA des tests et des futurs binaires est `b10ede6...`, pas nécessairement le HEAD documentaire apparu après ce fichier.
