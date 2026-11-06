# IAMINA — Logo Web V4 : remplacement global des identités visuelles (05/11/2026)

## Goal
Remplacer les anciens visuels IAmina dans toutes les surfaces Flutter **Web** identifiées et les métadonnées PWA, sans modifier le tracé calligraphique intérieur du carré transmis par le propriétaire.

## Périmètre
- Versions V4 : verticale (login et verrouillage), carré seul (header mobile, tableau de bord, overlay de tâche), horizontale (onboarding).
- Favicon 64, icônes PWA 192/512, variantes maskable et icône écran d'accueil iOS via la balise Web existante.
- Thème/écran de lancement PWA alignés sur vert forêt et papier IAMINA.
- Nouveau cache release `0.1.0+1-logo-v4`, avec precache des nouveaux visuels.

## Limites
- Cette modification vise uniquement Flutter Web/PWA. Les ressources natives Android/iOS ne sont pas modifiées (roadmap WEB-ONLY).
- Les pixels des nouveaux PNG sont des dérivés raster du concept V4. Il n'y a pas eu de nouvelle construction calligraphique ; les épaisseurs/espaces ont pu varier lors du rendu/quantification. Le tracé symbolique reste celui de la référence.
- La lisibilité des détails en favicon 16–24px demeure limitée.
- Les tests statiques ne prouvent pas à eux seuls la qualité visuelle sur les pages réelles.
- Aucune donnée patient, auth, API ou sécurité touchée.
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
