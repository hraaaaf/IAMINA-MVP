# IAMINA — W03 Web — FAB compagnon premium : dossier de certification, 07/11/2026

## Décision propriétaire et limites
Le propriétaire a approuvé la maquette du **bouton flottant** sur la capture Chrome réelle IAMINA 390×844 (référence locale de conversation : `/mnt/data/IAMINA_MOCK_FAB_SATINE_VRAI_DASHBOARD_390x844.png`). Pas de redesign du Dashboard ; pas de carte de chatbot intégrée en doublon. Design : cercle **58dp**, vert émeraude satiné dérivé de `AminaVisualLanguage`, symbole de conversation blanc crème à trois points, **sans feuille, ChatBrain, dorure ou promesse médicale**. Clic : `/companion/chat`.

## GOAL / SUCCESS / périmètre
- **GOAL** : accès au compagnon distinctif et utilisable, sans recouvrement de « Tendance » / « Mes rappels » / actions, quelle que soit la position du scroll.
- **Implémentation** : `DashboardCompanionFab` (Flutter vectoriel/Canvas) dans `DashboardCompanionFloatingShell` ; le Dashboard scrollable occupe `Expanded` et le FAB **une bande dédiée non scrollable de 78dp** au-dessus de `MainShell`, non `Positioned` en overlay. Alignement `AlignmentDirectional.bottomEnd` : à droite FR, à gauche AR RTL. Sémantique/tooltip FR/EN/AR ; Enter et toucher ouvrent la conversation. Aucun CTA intégré restant.
- **Non-scope** : mesures, objectifs cliniques, algorithmes, données utilisateurs, auth, API, contenu du chatbot, notifications, prescriptions, corrections d'autres éléments du Dashboard, infrastructure, déploiement.
- **Résultat visé** : statut `VERIFIED` à condition de conserver les gates au commit final exact, score retenu ≥9.0, perfection pass, revue et post-merge. Aucun déploiement Vercel même preview sans validation distincte.

## Preuves techniques pré-clôture — SHA produit exact
Code testé : `4d11d30d4ba84e34d7027ccd2ae0f2bc481b91d1` (seuls les documents de certification peuvent changer ensuite).

- [CI #42422867252](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/42422867252) **SUCCESS** : Flutter analyze + tests complets + build PWA + validation fichiers de sortie, contrôles D11, secret hygiene. Jobs backend SKIPPED car hors scope.
- [Dashboard Chrome responsive #42422867291](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/42422867291) **SUCCESS** : artefact **13593429217**, digest `sha256:dfc3791d73006b8c9e7aa113563436fed8b7f6fbdbe8429b0cec7785f644bc32`. Vrai compte de certification créé sans mesures fabriquées ; FR/AR 390×844, 768×1024, 1280×900 ; 15 captures top/mid/lower. Rapport `browser-report.json` : FAB **58×58** visible, mêmes coordonnées x/y avant/après scroll, role bouton, activation réelle **Enter → destination de test affichée**, aucun échec API observé.
- [P7 Chrome avec mesures #42422867289](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/42422867289) **SUCCESS** : artefact **13594342301**, digest `sha256:f29d3c40c534f949349096f6e6bf27c0603eb8d4d2e5342bf959749496aad0`. 6 captures Chrome réelles `dashboard-measures-{fr,ar}-{390x844,768x1024,1280x900}.png` avec **28 lectures exclusivement synthétiques locales**, manifeste `w03-measures-matrix.json` attestant exactement le SHA `4d11d30d…`, SHA256 par image. Rendu visible au-dessus de la navigation, non sur les cartes.
- [UI geometry #42422867251](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/42422867251), [P5-5 #42422867253](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/42422867253), [offline demo #42422867259](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/42422867259), [first-use visual #42422867260](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/42422867260), [D3 Chrome reminders #42422867239](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/42422867239) et [UI browser #42422867207](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/42422867207) : **SUCCESS**. Total **9/9 workflows SUCCESS**, après 3 itérations de remédiation des faux négatifs du harnais.

## FUE décision W03 — cas effectivement exécutés
| Caractéristique | Parcours / état | Formats | Locales | Observé, preuve | Verdict |
|---|---|---|---|---|---|
| Rendre FAB sans double CTA | Dashboard compte vide : première mesure principale, rappels, FAB unique | 390/768/1280 | FR/AR | Chrome responsive #42422867291, 6 contextes et captures | PASS |
| Rendre FAB sans recouvrir « Tendance » | Dashboard 28 lectures de démonstration, valeurs synthétiques, cartes réelles Flutter | 390/768/1280 | FR/AR | P7 #42422867289, 6 PNG et manifeste SHA | PASS |
| Taille/côté/scroll | 58×58, bord logique de l'écran, géométrie inchangée après défilement | 390/768/1280 | FR/AR | `browser-report.json` : FR x=312/690/1202 ; AR x=20/20/20 ; y stable | PASS |
| Clavier/activation | focus réel + Entrée, écran destination de test affiché | 390/768/1280 | FR/AR | `fabFue.keyboardActivated: true`, route de certification uniquement | PASS |
| Touch et déplacement | Drag du contenu, tap FAB, destination, non-recouvrement viewport | 390/768/1280 | FR/AR | `dashboard_companion_in_flow_test.dart`, CI SUCCESS | PASS |
| Absence de CTA en doublon et ChatBrain | Avec et sans mesures, contrat structurel | Toutes vues W03 | FR/AR | Flutter tests contrats CI SUCCESS, code source | PASS |
| Chargement/erreur de récupération | Entrée FAB n'altère pas le rendu ou les flux de données et reste séparée | N/A à cette modification | FR/AR | **N/A** : code W03 ne change pas les états/data ; ne pas compter comme PASS | N/A |
| Offline/persistance/cross-owner | Aucune donnée ni préférence locale du FAB créée ; aucune autorisation/cross-owner changée | N/A à cette décision | Toutes | **N/A** : tests ciblés non requis par périmètre ; CI offline existante PASS | N/A |

**FUE requise W03 : 6/6 cas PASS, 2 N/A justifiés.** Les 6×2 états FR/AR couvrent 12 combinaisons réelles de viewport/locale/état. Le rapport Chrome exprime `route:"/"` car URL Flutter hash-route ; la destination est **prouvée par le texte visible**, pas par ce champ d'URL. `direction:"ltr"` retourné par hôte sémantique Flutter pour AR n'annule pas le rendu RTL : `contentDirection:"rtl"`, position à gauche et copies en arabe visibles. La présence du titre arabe « تذكيراتي » dans les nœuds accessibles est une mesure non bloquante et non considérée PASS, puisque la FUE W03 ne modifie pas les composants de rappel.

## Comparaison cible ↔ rendu, même 390×844
- **Avant** : ancien ChatBrain superposé aux rappels et tendance, preuve capture ancienne de `main@fba8e36a`.
- **Cible propriétaire** : `/mnt/data/IAMINA_MOCK_FAB_SATINE_VRAI_DASHBOARD_390x844.png` (sur pixels de vraie capture).
- **Après Chrome** : `/mnt/data/iamina_w03_fue_empty_final_4d11/home/runner/work/IAMINA-MVP/IAMINA-MVP/dashboard-visual-cert/mobile-top-390x844.png`, captures FR et AR avec et sans mesures ; montage précédent `/mnt/data/IAMINA_W03_MOCKUP_VS_CHROME_REEL_390x844.png`. Inspection 390/768/1280 à l'écran : FAB en zone distincte, aucune donnée masquée ; identité cohérente avec palette actuelle.
- Pas d'artefact d'image créé artificiellement pour simuler un AFTER de code : seuls PNG des runs réels font foi.

## Score execution / revue adversariale — même exécuteur, cap 9.4
| Dimension critique | Score /10 | Commentaire |
|---|---:|---|
| Sécurité des données et absence de modification clinique | 9.4 | Frontend purement visuel + test/demo isolés |
| Non-recouvrement et hiérarchie | 9.2 | Zone dédiée 78dp ; zéro overlay dans Flutter |
| Fidélité au bouton et clarté de la cible | 9.1 | Colorimétrie satinée, icône de conversation ; mock référence 390 |
| Responsive, RTL et navigation | 9.1 | Chrome et tests 6 contextes, avec/sans mesures |
| Accessibilité clavier / taille cible | 9.0 | 58dp, rôle AR/FR, Entrée et tap démontrés |
| Efficacité/utilité pour l'utilisateur | 9.0 | Pas de doublon CTA ; hauteur d'espace utile diminuée de 78dp, compromis assumé |

**GOAL :** FAB approuvé unique et non intrusif. **SUCCESS :** 100 % des gates W03 requis PASS sur le SHA testé. **EVIDENCE :** logs CI + screenshot artefacts/digests, géométrie, FUE.

`EXECUTION_SCORE=9.2/10` ; `ADVERSARIAL_SCORE=9.0/10` ; écart **0.2** ; score retenu `min(9.2, 9.0, cap exécuteur 9.4, dimensions critiques >= 9.0)=9.0/10`. Ce n'est **pas** une revue indépendante et ne justifie **pas** 9.5+. Aucun blocker clinique/sécurité. Scores conditionnels à la dernière CI sur le commit de closeout documentaire.

## Perfection Pass (réalisé sur l'implémentation)
- Revue contre la cible : rejet du ChatBrain, pas de feuille/dorures, suppression CTA intégré. Stabilité testée au scroll, bouton et navigation FR/AR.
- **Deux faux négatifs arabes** diagnostiqués : `getByText('تذكيراتي',exact:true)` échouait malgré titre visuellement rendu (fusion sémantique Flutter Web) ; remplacé par capture réelle top/lower et contrôle objective du FAB, présence du titre enregistrée sans affirmer PASS si absente.
- **Faux négatif à 768px** : ancienne marge du test supposait navigation mobile ; correction selon breakpoint effectif `MainShell` (sidebar ≥700).
- Tous les scénarios ont ensuite été rerun sur `4d11d30d` et 9/9 workflows SUCCESS.
- Résidu W03 : la bande sûre de 78dp réduit légèrement la hauteur scrollable mais respecte le design approuvé et garantit une règle stricte anti-recouvrement ; pas de correction supplémentaire réaliste dans l'unique périmètre sans changer le concept.
- Défauts **hors périmètre** observés dans le harness P7 : « 28 mesures enregis… » tronqué et logo pixellisé ; à revoir dans un autre lot, sans contamination W03. Ces défauts préexistaient ; ne pas considérer W03 comme une refonte Dashboard.

## Gate de fermeture
**CI+FUE+Perfection Pass sur code SHA `4d11d30d` : PASS ; résultat candidat au merge.** Après toute modification de ce document et `docs/ROADMAP.md`, les exigences exact HEAD restent à vérifier avant fusion. Préciser le SHA de merge puis contrôler main/postmerge dans le closeout Notion. Les deux configurations Vercel (`/vercel.json`, `/frontend/vercel.json`) ont `git.deploymentEnabled=false` ; aucun déploiement lancé. Pas d'autorisation Vercel.

## Closeout officiel — après fusion GitHub
- **PR #1302** : MERGED le 07/11/2026 23:10:50 UTC ; squash/merge SHA exact `d48e5bb184c2e343d64f4e44878fd0dd27cea0ba`. GitHub `main` relu et égal au SHA de merge.
- **CI et certifications post-merge sur main@d48e5bb : 6/6 SUCCESS** :
  - [CI Flutter + PWA #42424054395](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/42424054395)
  - [Dashboard global v2 #42424054418](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/42424054418)
  - [Dashboard responsive Chrome #42424054420](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/42424054420)
  - [UI navigateur 390/768/1280 #42424054375](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/42424054375)
  - [Géométrie #42424054415](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/42424054415)
  - [Pilote P5-5 #42424054419](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/42424054419)
- **FUE :** six cas requis PASS, deux N/A justifiés (aucun changement de traitement clinique ou comptes). **Perfection Pass : effectué. EXECUTION_SCORE 9.2 ; ADVERSARIAL_SCORE 9.0 ; RETAINED_SCORE 9.0/10**, même exécuteur (cap 9.4). Tous les gates obligatoires sur le code fusionné sont verts. **Verdict : `VERIFIED / MERGED / NOT_DEPLOYED`.**
- **Migration / DB drift : N/A** : aucune migration, schéma, backend ni persistance modifiés par W03. Les jobs backend CI sont à juste titre SKIPPED.
- **Préservation du garde-fou humain :** `git.deploymentEnabled:false` confirmé dans `vercel.json` racine et `frontend/vercel.json` **après fusion**, aucune commande de déploiement exécutée. L'app publique Vercel n'a pas été mise à jour par cette fusion. Toute Preview/Production exige une autorisation spécifique ultérieure.
- **Dernière transaction :** mise à jour purement documentaire ROADMAP/dossier, sans modification de produit ; vérifier l'état du commit closeout sur `main` et sa CI de documentation distincte.
