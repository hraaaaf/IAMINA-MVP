# IAMINA — Logo Web V4 : remplacement global des identités visuelles (05/11/2026)

## Goal
Remplacer les anciens visuels IAmina dans toutes les surfaces Flutter **Web** identifiées et les métadonnées PWA, sans modifier le tracé calligraphique intérieur du carré transmis par le propriétaire.

## Périmètre
- Versions V4 : verticale (login et verrouillage), carré seul (header mobile, tableau de bord, overlay de tâche), horizontale (onboarding).
- Favicon 64, icônes PWA 192/512, variantes maskable et icône écran d'accueil iOS via la balise Web existante.
- Thème/écran de lancement PWA alignés sur vert forêt et papier IAMINA.
- Cache PWA / Flutter release `0.1.1+2`, aligné sur `frontend/pubspec.yaml` et `flutter_bootstrap.js`; precache des nouveaux visuels et alias rétrocompatible du nouveau carré au chemin `logo_amina.png`.

## Limites
- Les ressources graphiques changées visent Flutter Web/PWA ; les icônes natives Android/iOS ne sont pas modifiées (roadmap WEB-ONLY). Le dépôt comprend une correction de tests backend historiques, sans modification du runtime médical/sécurité.
- Les pixels des nouveaux PNG sont des dérivés raster du concept V4. Il n'y a pas eu de nouvelle construction calligraphique ; les épaisseurs/espaces ont pu varier lors du rendu/quantification. Le tracé symbolique reste celui de la référence.
- La lisibilité des détails en favicon 16–24px demeure limitée.
- Les tests statiques ne prouvent pas à eux seuls la qualité visuelle ; des captures du vrai navigateur Chrome avec données synthétiques ont été inspectées sur 390×844, 768×1024 et 1280×900 (dashboard et compagnon), avec comparaison BEFORE/AFTER.
- Aucune logique de données patient, d'authentification ni de runtime sécurité modifiée. Les tests de gouvernance historiques et le test explicite de rejet d'une preuve expirée ont été modifiés pour leur déterminisme.
- Aucun déploiement Vercel autorisé par cette PR.

## Critères de succès
1. Zéro référence Dart à `logo_amina.png`.
2. Toutes les surfaces de marque repérées chargent le nouvel asset correspondant.
3. Tous les PNG existent avec dimensions prévues et manifest/precaching cohérents.
4. Flutter analyze/test Web et visualisation sur 390×844/768×1024/1280×900, FR/AR RTL avant merge.
5. Nouveau visuel évalué par propriétaire avant tout déploiement.

## Preuve disponible au moment du commit
Les 8 objets PNG GitHub sont créés depuis fichiers locaux et leurs SHA correspondent aux hashes binaires locaux. Les tests CI à SHA final et la FUE navigateur réelle restent à exécuter ; pas de revendication VERIFIED/CLOSED.

## Séquence restante
CI SHA exact → correction si échec → revue visuelle BEFORE/AFTER sur navigateur Flutter réellement construit → FR/AR, responsive et RTL → certifier les gates sur HEAD exact → demande GO propriétaire pour tout déploiement Preview Vercel → merge/puis postmerge uniquement selon garde explicite.

## Revue visuelle adversariale — contraste en mode sombre
L'emblème vert sur fond sombre pouvait devenir difficile à distinguer. Les surfaces de login FR/MENA, verrouillage setup/unlock et en-tête onboarding appliquent désormais une colorisation blanche au rendu du PNG en mode sombre, sans modifier les glyphes vectoriels ni l'asset de référence. Les cartes blanches du dashboard et des en-têtes conservent l'emblème vert. La preuve finale requiert une capture Flutter Web réelle en mode sombre ; pas de certification anticipée.

## Dernier perfectionnement — accueil onboarding desktop
Le panneau de bienvenue desktop sur fond vert comporte désormais le lockup IAMINA horizontal blanc ; l'ancien cœur décoratif et la typographie « IAmina » indépendante ont été supprimés de ce panneau. Le même composant de marque reste visible sur l'AppBar du parcours mobile, en vert sur fond clair et en blanc sur fond sombre. Pas de modification des questions, traitements ou formulaires d'onboarding.

## 05/11/2026 — Analyse des six échecs CI initiaux et correction proposée

Constat GitHub sur `4f498bb4`: 14 workflows SUCCESS, six FAILURE. `CI` 918 PASS / 56 FAIL / 7 SKIPPED, avec `Unable to load asset: assets/images/logo_amina.png`. Les échecs de `UI geometry` et `P7 responsive Dashboard` ont la même erreur de ressource; D11 FR/AR en navigateur remonte deux 404 de ressources; D7 timeout au bouton `Start`, lien causal à vérifier après correction. `PWA update` et packaging échouent sur `IAMINA_CACHE_SCHEMA` divergent de `pubspec.yaml`.

Remédiation : compléter les références Flutter laissées sur le nom historique dans enrollment local, compagnon, overlay chat, FAB et contrat de langage visuel ; maintenir `assets/images/logo_amina.png` comme **alias binaire exact du nouvel emblème V4** pour compatibilité des clients Web anciens, sans restaurer l'ancien dessin ; ajouter l'alias au precache du service worker ; avancer `frontend/pubspec.yaml` de `0.1.0+1` à `0.1.1+2`, et aligner `IAMINA_CACHE_SCHEMA` et fallback bootstrap au même identifiant canonique. Le test de branding contrôle l'identité de l'alias et la cohérence de version.

Ces modifications ne constituent pas une preuve de succès CI ou navigateur tant que le nouveau SHA n'a pas passé les gates exact-HEAD. Aucun déploiement Vercel.

## 06/11/2026 — Revue des 4 workflows rouges au HEAD 93225aae

Les 27 workflows sur la PR Draft #1275 indiquent 23 SUCCESS / 4 FAILURE, soit : CI Flutter (967 tests PASS, 7 FAIL, 7 SKIPPED), PWA update/recovery (Chrome n'expose pas le port de débogage 9225), D7 FUE (le scénario navigateur n'a pas sélectionné l'unité obligatoire avant de chercher le bouton « Start »), Developer portability macOS (5 tests de gouvernance échouent car la preuve `fallback.processor_identity` expire le 04/11/2026). La preuve réglementaire expirée est un **vrai bloqueur de sécurité**, non un problème de marque : ne pas prolonger arbitrairement sa date ni exclure ces tests pour obtenir artificiellement une CI verte.

Correction en cours : mettre à jour les deux contrats de tests restés sur l'ancien nom `logo_amina.png` (qui causaient les 7 FAIL Flutter), faire sélectionner explicitement `mg/dL` au patient **synthétique** dans le scénario D7, et stabiliser le navigateur du test PWA avec un Chromium Playwright versionné + diagnostic de démarrage. Aucune modification du flux clinique ou de ses exigences.

**Statut** : à prouver sur nouveau HEAD. Si le gate macOS reste rouge, demander une revue d'identité et une reconfirmation datée réelle par le responsable IAMINA Security ; ne pas renouveler une preuve sans validation humaine. Aucun merge ni déploiement Vercel.

## 06/11/2026 — Contrôle AVANT sur captures réelles GitHub / correction du lockup principal
Le navigateur Flutter Web a produit et stocké des captures sur les viewports 390×844 et 768×1024 (artefacts UI browser GitHub). Inspection réelle des captures du 06/11/2026 : le carré V4 est affiché, mais le tableau de bord et l'accueil compagnon reprenaient encore un titre `Text('IAmina')` indépendant, au lieu du wordmark V4 prévu. Score visuel qualitatif provisoire : 7,5/10 sur l'intégration de marque (icône reconnue, lettrage incohérent). 

**Goal :** afficher le lockup horizontal V4 (symbole + lettrage exact IAMINA) en en-tête du dashboard et du compagnon, en conservant le sous-titre localisé, les boutons de notification/fermeture et le tracé original. Les zones compactes (FAB, titres des pages de soins, chat Hero) continuent à utiliser le carré V4 sans altération du tracé.

**Implémentation** : passer des deux en-têtes `Text('IAmina')` + icône isolée au même `Image.asset('assets/images/iamina_logo_horizontal.png')`, conserver les sous-titres FR/EN/AR, mode sombre blanc, tests de contrat. Aucun changement médical ; favicon et PWA inchangés. **AFTER réel attendu** : captures CI Web FR/AR, 390/768/1280, revue comparée avec les artefacts AVANT. Pas de certification sans ces preuves.

## 06/11/2026 — Dernières erreurs : tests de marque et horloge de gouvernance

Résultat du HEAD `ee0dcc3a` : 26 SUCCESS / 2 FAILURE. Flutter CI : `973 PASS / 1 FAIL / 7 SKIPPED`. L'échec unique est un contrat source `ui_visual_language_contract_test.dart` attendant l'icône carrée dans le `CompanionPremiumScreen` alors que l'en-tête utilise intentionnellement le lockup horizontal V4. Le contrat a été corrigé pour exiger le lockup `iamina_logo_horizontal.png` et son étiquette accessible `IAMINA`; le carré reste exigé dans `AminaMobilePageHeader`.

Developer portability macOS : cinq tests de CLI d'audit prévus pour le scénario historique du `2026-08-04` invoquent implicitement `date.today()`. À la date actuelle, l'approbation du provider local a expiré le `2026-11-04`, et les tests échouent avant l'assertion attendue. **Correction de déterminisme des tests uniquement** : fixture d'horloge historique limitée aux cinq tests scénarisés, tout en ajoutant un test explicite qui exige que `validate_consent_governance(today=2026-11-06)` rejette `fallback.processor_identity evidence is stale`. Aucun fichier du moteur de gouvernance ni aucune date d'approbation n'est modifié. Cela ne constitue **pas** une revalidation de la preuve locale : le gate opérationnel reste interdit sans audit réel daté du responsable sécurité. 

Statut : correction proposée dans la PR ; succès CI et comportement en navigateur à prouver sur le nouveau SHA. Pas de merge ou Vercel.

## 06/11/2026 — Résultat vérifié : CI 29/29 GREEN et approbation visuelle

**Référence exacte validée (avant ce seul commit documentaire) :** PR [#1275](https://github.com/hraaaaf/IAMINA-MVP/pull/1275), branche `fix/iamina-web-brand-v4-ci-20261105`, code HEAD `135605495fa06ffb279ad8a85ae15f94c20004ca`, base main `d7d650a082300486764019c8238f591057210d54` (GitHub comparateur : ahead 8, behind 0, 34 fichiers modifiés).

**CI constatée sur code exact :** **29/29 WORKFLOWS SUCCESS, 0 failed / 0 pending**, y compris [CI générale #42189165982](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/42189165982), [Developer portability #42189166107](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/42189166107), [UI Chrome certification #42189165941](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/42189165941), [PWA update/recovery #42189166152](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/42189166152), [D7 #42189166156](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/42189166156) et [D11 #42189166001](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/42189166001). Réussite CI des tests historiques de gouvernance ne signifie **pas** revalidation opérationnelle des preuves expirées.

**Validation visuelle par le propriétaire :** réponse explicite « Je valide » après présentation des captures réelles **BEFORE/AFTER**, dashboard et compagnon, aux viewports 390×844, 768×1024 et 1280×900. La V4 horizontale est approuvée pour les en-têtes principaux, carré V4 pour les icônes compactes. Les captures permettent de confirmer le changement de composition ; pas de preuve de conformité artistique chiffrée universelle. Le test favicon très petit (16–24 px) demeure une réserve de lisibilité ; aucune retouche du tracé calligraphique interne n'est requise.

**Contrôle de déploiement :** les fichiers `vercel.json` et `frontend/vercel.json`, lus sur le HEAD ci-dessus, contiennent tous deux `git.deploymentEnabled=false`. L'approbation du design **n'est pas une autorisation de déploiement**. Aucune Preview ni Production Vercel déclenchée dans ce lot.

**Sécurité — frontière importante :** `fallback.processor_identity` et `quota-exhausted.processor_identity` portent la preuve du 04/08/2026 avec échéance du 04/11/2026 dans le registre runtime. Le nouveau test prouve que la vérification au 06/11/2026 la rejette comme **stale**. La correction des cinq tests historiques (horloge test uniquement) permet la CI 29/29 sans falsifier une approbation : un GO de mise en service avec cette preuve exige une réelle revalidation documentée par l'IAMINA Security Owner.

**État du lot :** design APPROUVÉ et code TESTÉ en CI sur `13560549`. Le présent closeout documentaire modifie le HEAD : le résultat 29/29 **ne doit pas être attribué automatiquement à ce commit documentaire** avant vérification GitHub. PR à vérifier après commit, puis seulement envisager merge du code si contrôles stricts satisfaits et sans déploiement automatique.

**Séquence restante :** vérifier CI sur le nouveau HEAD documentaire → en cas de rouge diagnostiqué corriger → en cas de vert fusionner la PR de code sans déclencher Vercel → vérifier main et post-merge → conserver le gate de revue sécurité avant toute Preview/Production ; déployer uniquement après autorisation explicite distincte du propriétaire.
