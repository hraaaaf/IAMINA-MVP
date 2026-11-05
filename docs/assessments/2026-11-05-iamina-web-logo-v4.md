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
