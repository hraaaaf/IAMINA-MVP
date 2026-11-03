# IAMINA — Décision D22.2 Web — iPhone Safari maintien ±

Date : 2026-11-03. Statut : **correctif proposé, tests fonctionnels CI non encore prouvés, recette physique iPhone requise**.

## Goal / Succès / Preuve

- **Goal** : appui long répété fiable pour les deux boutons ± sur iPhone Safari, même après plusieurs maintiens successifs ; accélération progressive et arrêt instantané au relâchement.
- **Succès** : tap bref = un pas (1 mg/dL / 0,1 mmol/L), maintien >420ms = premier pas puis 270→155→85ms, aucun changement après PointerUp/Cancel/sortie du bouton ; deux maintiens consécutifs fonctionnent ; aucune sauvegarde avant Save.
- **Preuve attendue** : Flutter widget tests FR/AR + Chrome FUE + vraie recette Safari iPhone (deux maintiens +, deux maintiens −, arrêt, switch unité, persistance).

## BEFORE / Hypothèse / AFTER

**BEFORE** : D22.1 SHA `b10ede6ac3452151aee72ed08857995e1e6261c4`, Vercel production `dpl_3xgGNJfnaSngdM5pZgFJEfyKbDf5` READY, alias `iamina-review.vercel.app`. Retour utilisateur iPhone : maintien +/- ne fonctionne que la première fois. D22.1 12/12 workflows verts mais comportement réel Safari non couvert.

**Hypothèse, non certitude** : compétition `IconButton.onLongPress`/tooltip/recognizer natif dans Safari Web.

**AFTER proposé** : `Listener.onPointerDown` pilote un timer d'activation 420ms ; répétition via Timer à cadence bornée 270→155→85ms ; `onPointerUp/Cancel/Move` coupe l'activation et la répétition. `IconButton.onPressed` conserve un tap bref ; l'appui long ne doit pas produire un second tap fantôme. Aucun changement backend, DB, seuils ou calcul des unités.

## Traçabilité

- PR Draft [#1256](https://github.com/hraaaaf/IAMINA-MVP/pull/1256), branche `fix/d22-2-web-ios-pointer-hold-20261103`, base D22.1.
- Code initial `3fa81c8`, tests de second maintien FR/AR `fc283e9`.
- Six workflows visuels du SHA `fc283e9` : **6/6 SUCCESS** ; **ne pas confondre avec Flutter CI complet**, absent à ce point.
- Pas de nouveau déploiement Vercel autorisé. Prochaine action : prouver Flutter + Chrome, comparaison visuelle aux mêmes viewports, recette Safari sur preview après GO explicite, puis closeout.
