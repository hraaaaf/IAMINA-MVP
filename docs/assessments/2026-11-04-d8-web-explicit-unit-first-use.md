# D8 — Web : unité glycémique explicitement choisie avant première mesure

**04/11/2026 — IAMINA Chantier B.** Autorisation du propriétaire : « Okay go » après arbitrage d'une unité choisie par le patient (sans présélection selon pays). **Périmètre :** Web/PWA, onboarding neuf. **Aucun GO merge ni Vercel.**

## Goal, succès et preuve attendue
- **Goal :** ni `mg/dL` ni `mmol/L` n'est préconfirmé au premier usage, même après choix du pays ou suggestion IP. Le patient choisit son unité de lecteur avant d'accéder à la première mesure.
- **Succès :** CTA de fin d'onboarding bloqué sans unité ; sur mobile/tablette CTA visible mais désactivé, sur desktop CTA absent tant que l'unité manque. Après clic explicite, sauvegarde unique du bon code dans le profil Drift, réversible depuis le profil. Pays et changement de langue n'effacent jamais le choix. Les questions sur le type de diabète et les traitements demeurent facultatives. `preferencesOnly` ne change pas.
- **Preuve à obtenir :** tests Widget D5/D7/D8 en FR/AR RTL, tests Chrome D5 + sticky onboarding FR/AR aux viewports 390×844 / 768×1024 / 1280×900, rapports et captures réelles, CI sur HEAD exact. Ni patient réel, ni politique clinique, ni activation de cible personnelle.

## BEFORE — code et référence
Base `main@8bcc6a16710a16d202a7b3f5c48d1c0ac4cc9288` : `frontend/lib/features/auth/onboarding_chat_screen.dart` initialise `String _unit = 'mg/dL'`. Le bouton Commencer est activable après seule confirmation langue/pays ; `_finish` inscrit `unitPreference` avec le défaut non choisi. Capture antérieure possible depuis les workflows `onboarding-sticky-cta-cert.yml` et `d5-country-web-fue.yml`. **Captures BEFORE non inspectées pendant cette rédaction : comparaison visuelle reste à effectuer.**

## Mini-mockup choisi avant code
```text
Quelle unité préférez-vous pour les mesures ?
[ mg/dL ]    [ mmol/L ]     (aucun choix)
Choisissez l’unité indiquée sur votre lecteur avant de continuer.
[ Commencer — désactivé ]  (mobile/tablette)
(Aucune action finale avant sélection sur desktop)

Après un clic explicite :
[ mg/dL ]    [ mmol/L ✓ ]
[ Commencer — actif ]
```
Pas de dialogue ou de navigation nouvelle, les deux chips de l'onboarding existant sont réutilisés. Aide en français, anglais et arabe.

## AFTER candidat — périmètre de changement
- `_unit` devient nullable seulement pendant le premier usage. `_finish` refuse toute sauvegarde si le premier choix n'existe pas, puis `unitPreference: drift.Value(_unit!)` conserve exactement l'unité sélectionnée.
- `ready` exige langue, pays explicitement choisi et unité choisie **uniquement** pour l'onboarding initial ; les préférences langue/pays des comptes existants restent libres.
- CTA sticky désactivé jusqu'au choix, hint localisé ; tests Flutter et scripts navigateur réalignés sur ce contrat pour empêcher un faux PASS D5.
- **Aucune règle pays→unité**, aucun support `g/L`, aucun changement de schéma Drift, de la valeur canonique mg/dL, des seuils legacy D22/D32, de la synchronisation ou des données cliniques historiques.

## État des gates
**Avant exécution CI :** implémentation candidate seulement. Les captures AFTER et le score visuel sont **NOT_RUN** ; aucune preuve d'une FUE hébergée/patient réel. D8 décision globale reste OPEN jusqu'à tests, contrôle visuel, review et autorisations distinctes de merge/Preview. D32 clinique reste responsable de toute conversion ou politique d'unité du lecteur.

## Preuves observées — 04/11, premier HEAD candidat a3b49a3a

- **BEFORE référence réelle** : D5 Chrome [run #41156056461](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41156056461), artifact `13025221192` (31/10, SHA `b3e41405`, donc **pas** exactement le `main@8bcc6a16` de cette PR) : captures `fr-390x844-ip_proposal-after-confirm.png`, `ar-390x844-ip_proposal-after-confirm.png`, `fr-768x1024-no_ip-manual-selected.png`, `fr-1280x900-no_ip-manual-selected.png`. Inspectées : le chip `mg/dL` est coché avant choix patient et le CTA `Commencer` actif.
- **AFTER référence réelle** : [D5 Chrome #41823209572](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41823209572), artifact `13318885131`, `result.json` **25/25 PASS, 0 erreur** sur exact `a3b49a3a`. Capture `after-confirm` au même viewport 390×844 FR/AR : aucun chip coché, aide de choix visible, bouton gris/inactif. Idem `manual-selected` à 768×1024/1280×900. Hors périmètre : authentification hébergée et vraies données patient (explicitement NOT_PROVEN).
- **AFTER navigateur FR et AR/RTL sur trois viewports** : [Onboarding Chrome #41823209782](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41823209782) SUCCESS sur `a3b49a3a` ; artéfacts FR `13318506156`, AR `13318023466`. Images `onboarding-step-units` / `arabic-units-revealed` inspectées : CTA désactivé sur 390 et 768, aucun débordement visible ; desktop 1280 n'expose pas d'action prématurée. Contrôle RTL cohérent. [First-use mobile #41823209587](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41823209587) SUCCESS (artifact `13318152350`).
- **Score visuel provisoire pour ce premier candidat : 9,1/10** sur les couples inspectés. Point perfectible : la consigne restait sur la même ligne que les chips à 768/1280 ; le correctif suivant force une ligne complète sous les chips, avec nouvelle capture AFTER nécessaire. Score final du dernier SHA **NON encore attribué**.
- **CI générale #41823209497 RED** sur `a3b49a3a` : 970 Flutter PASS / 1 FAIL / 7 SKIPPED ; l'unique FAIL est un test statique D7 demandant littéralement l'ancienne ligne `ready = langue && pays`, désormais incompatible avec D8. Correctif attendu : vérifier la nouvelle condition `langue && pays && unité explicite` sans rendre traitements obligatoires.
- **D22 navigateur #41823209474 RED** sur `a3b49a3a` : script `scripts/d22_gate_a_web_recipes.py` clique `Start` directement après le pays, sans choisir d'unité ; le CTA désormais bloqué explique le timeout. Correction attendue : vérifier le CTA inactif, sélectionner `mg/dL` en tant que patient synthétique puis poursuivre le test D22. Aucune modification d'oracle ni d'unité clinique.

**Validation finale :** ces deux corrections contractuelles et le raffinement du texte nécessitent une **nouvelle CI exacte** avant closeout. Aucun merge, aucune Preview/production Vercel.
