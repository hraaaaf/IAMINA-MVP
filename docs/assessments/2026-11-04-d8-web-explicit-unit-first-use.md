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
