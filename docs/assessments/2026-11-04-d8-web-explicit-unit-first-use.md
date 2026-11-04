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

## 04/11/2026 — Qualification exacte du code c6801a4c — 9/9 workflows SUCCESS

**HEAD de code vérifié :** `c6801a4cf4ad59cf18bae17951f19e968ae93c54`. Ne pas confondre avec le HEAD documentaire qui suit.

**GitHub Actions au SHA exact : 9/9 COMPLETED/SUCCESS, zéro workflow actif.**
- [CI générale #41824721814](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41824721814) SUCCESS : logs du job frontend `126556485478`, **971 Flutter tests PASS / 7 SKIPPED / 0 FAILED**, y compris les 4 nouveaux tests D8 : pas d'unités réécrites par IP/pays ; FR390, AR RTL390 et FR desktop ; `flutter build web --release --no-web-resources-cdn` réussi. Backend SQLite/PostgreSQL SKIPPED car non modifiés.
- [D5 Chrome #41824721861](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41824721861) SUCCESS : artefact `13319795192` avec `result.json` lu, **25/25 PASS / 0 erreurs**, `head=c6801a4c...`. Scénarios pays proposé par IP, absence IP, pays explicitement confirmé, clavier, offline et A→B→A sur app Flutter/IndexedDB de test.
- [D22 Gate A #41824721836](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41824721836) SUCCESS après actualisation du test navigateur qui choisit l'unité explicitement avant Start ; aucun oracle clinique assoupli.
- [Onboarding sticky CTA Chrome #41824721827](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41824721827) SUCCESS, tests et captures FR/AR 390×844 / 768×1024 / 1280×900.
- [First-use mobile visual #41824721821](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41824721821), [Auth visual #41824721808](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41824721808), [TD-014 app-lock #41824721843](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41824721843), [UI global #41824722005](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41824722005), [UI screenshot #41824721863](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41824721863) : tous SUCCESS.

### Comparaison visuelle finale inspectée sur le code c6801a4c

Couples de captures au **même viewport** : FR390×844, AR RTL390×844, FR768×1024, FR1280×900. Avant : D5 Chrome du 31/10, SHA `b3e41405`, artifact `13025221192` (**référence historique, pas `main@8bcc6a16` exact**). Après : D5 Chrome du 04/11, SHA exact `c6801a4c`, artifact `13319795192`, images réellement extraites et inspectées.

**Constat AFTER** : aucune unité cochée après pays, consigne sous les deux chips sur sa propre ligne en 390/768/1280 ; bouton mobile/tablette `Commencer` grisé et désactivé avant choix ; CTA desktop non visible avant choix ; orientation AR RTL correcte et textes non tronqués aux viewports inspectés. Après choix manuel de `mmol/L`, CTA disponible et préférence persistée dans profil (tests Flutter/Chrome). **Score visuel de revue du candidat : 9,2/10 (évaluation subjective sur ces images)**. Limites : baseline historique pas au même SHA immédiatement précédent, capture après choix AR/FR 390 encore à revoir lors de recette Safari, vraie Preview hébergée non testée.

### Verdict et human gate

**D8 — code Web et préflight automatisé techniquement QUALIFIÉS sur c6801a4c ; D8 décision produit PAS encore CLOSED/DEPLOYED.** La décision produit validée est le **choix explicite du patient**, non un mapping géographique ; les conventions cliniques D32, `g/L`, conversion de cibles, egress et ancien historique médical n'ont pas été modifiés.

PR [#1269](https://github.com/hraaaaf/IAMINA-MVP/pull/1269) **OPEN/DRAFT, non mergée**. Le propriétaire n'a **pas** autorisé un déploiement Vercel ou un merge par son « Okay go » (ce GO portait sur implémentation). Aucune publication, aucune migration réelle, aucune mesure de patient. **Next exact :** recette humaine iPhone Safari/AR RTL d'abord seulement après autorisation distincte de Preview Vercel ; si FUE + reviews conformes, demander GO de merge séparé, post-merge CI, closeout.


## 04/11/2026 — Preview READY et recette utilisateur iPhone Safari 5/5 OK

**Événement autorisé :** après validation du code, propriétaire : « Go » pour **Preview Vercel** uniquement, pas pour production/merge. Déploiement `dpl_9M5C2vy2FcLp5fS7rnmMVeZrKBw8`, **Preview** `iamina-review` (pas `iamina-certified`), SHA déployé `50a459c560628b88af23c9f54812a103fa0c4a85`. Vercel API : `READY`, `target=null` (Preview), GET `/`, `flutter_bootstrap.js`, `manifest.json`, `iamina_app_lock.js` = **HTTP 200** via accès protégé ; `noindex`. Aucun alias production modifié. Preview protégée par Vercel Authentication.

**Retour utilisateur explicite et daté** : « D8 : j’ai effectué les 5 vérifications iPhone Safari de la Preview. Voici mon retour : tout est OK. » → **5/5 vérifications déclarées OK par le propriétaire**, zéro anomalie signalée ; **attestation utilisateur, pas exécution du navigateur Safari par l'agent**, ni enregistrement de screenshots supplémentaires du téléphone. Checklist transmise : [x] langue et pays n'activent pas l'unité implicitement ; [x] choix `mmol/L` active « Commencer » ; [x] profil conserve l'unité ; [x] rechargement conserve la préférence ; [x] arabe RTL sans chevauchement visible. La recette Safari contribue à l'acceptation UX D8 dans le périmètre Preview **sans confirmer clinique D32, iOS natif, backend distant réel ni tous les types de comptes**. Une vérification supplémentaire des anciens profils, hors de ces cinq cases, demeure soutenue par les tests de non-régression sans attestation d'un patient réel.

**CI finale antérieure Preview** : le SHA déployé `50a459c5` a **9/9 workflows GitHub SUCCESS** : CI #41825917105, D5 Chrome #41825917079, D22 #41825917052, CTA Chrome #41825917377, UI screenshot #41825917219, first-use #41825917234, Auth #41825917371, UI global #41825917166, TD-014 #41825917195. Pour le SHA code `c6801a4c` : 971 Flutter PASS/7 SKIP, 25/25 D5 Chrome synthétiques, build PWA. Contrôle comparatif PR → main au moment de l'attestation : 4 commits ahead, 0 behind ; PR `#1269` **OPEN/DRAFT/MERGEABLE** ; aucune review PR enregistrée, protection de `main` non lisible par l'intégration (HTTP 403), **ne pas conclure absence de règles**.

**Verdict de recette D8 :** UI Web/PWA sur Preview **USER-ACCEPTED (5/5) + CI PASS**. **Reste un human gate séparé pour fusionner la PR**, suivi par validation post-merge et mise à jour du chantier B. Sans autorisation de fusion, laisser `main` et la production inchangés. La présente modification est documentaire seulement ; elle crée un nouveau SHA de branche et ses propres CI doivent être revérifiées avant fusion. **Next exact :** vérifier nouvelle CI document-only et recueillir autorisation explicite de merge ; après GO, résoudre reviews/règles requises puis merge et post-merge CI, closeout Notion ; ensuite D10 selon la priorité du Chantier B.
